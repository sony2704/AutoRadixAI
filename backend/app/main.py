"""
AutoRadixAI - FastAPI Application Entry Point
Production-grade Medical AI Agent Platform
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import AutoRadixException
from app.core.logging_config import configure_logging
from app.core.middleware import (
    AuditLogMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.models.database import create_tables, engine
from app.workers.celery_app import celery_app  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    configure_logging()
    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    # Ensure upload/output directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (settings.OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
    (settings.OUTPUT_DIR / "heatmaps").mkdir(parents=True, exist_ok=True)
    (settings.OUTPUT_DIR / "anonymized").mkdir(parents=True, exist_ok=True)

    # Initialize database tables
    await create_tables()
    logger.info("Database tables initialized")

    yield

    # Cleanup
    await engine.dispose()
    logger.info("AutoRadixAI shutdown complete")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ #
    # Middleware (order matters — outermost first)
    # ------------------------------------------------------------------ #
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------ #
    # Exception handlers
    # ------------------------------------------------------------------ #
    @app.exception_handler(AutoRadixException)
    async def autoradix_exception_handler(
        request: Request, exc: AutoRadixException
    ) -> JSONResponse:
        logger.warning("AutoRadixException: %s", exc.detail, extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred."},
        )

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #
    app.include_router(api_v1_router, prefix="/api/v1")

    # Static files for outputs (heatmaps, reports)
    app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #
    @app.get("/health", tags=["Health"], summary="Platform health check")
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time(),
        }

    return app


app = create_application()
