"""
AutoRadixAI Platform Configuration
Central configuration management using pydantic-settings.
"""
from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "AutoRadixAI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-powered core radiology intelligence platform that automates "
        "medical imaging workflows."
    )
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | staging | production

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://autoradix:autoradix@localhost:5432/autoradixai"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ------------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ------------------------------------------------------------------
    # File Storage
    # ------------------------------------------------------------------
    UPLOAD_DIR: Path = Path("uploads")
    OUTPUT_DIR: Path = Path("outputs")
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [
        ".dcm", ".zip", ".png", ".jpg", ".jpeg", ".pdf", ""
    ]

    # S3-compatible storage
    USE_S3: bool = False
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "autoradixai"
    S3_REGION: str = "us-east-1"

    # ------------------------------------------------------------------
    # AI / ML
    # ------------------------------------------------------------------
    MODEL_REGISTRY_PATH: Path = Path("ai-models/registry")
    MODEL_WEIGHTS_PATH: Path = Path("ai-models/weights")
    GPU_ENABLED: bool = False
    GPU_DEVICE_ID: int = 0
    INFERENCE_TIMEOUT_SECONDS: int = 120

    # ------------------------------------------------------------------
    # PACS / DICOMWeb
    # ------------------------------------------------------------------
    ORTHANC_URL: Optional[str] = "http://localhost:8042"
    ORTHANC_USER: Optional[str] = "orthanc"
    ORTHANC_PASSWORD: Optional[str] = "orthanc"
    DICOMWEB_BASE_URL: Optional[str] = None

    # ------------------------------------------------------------------
    # HL7/FHIR
    # ------------------------------------------------------------------
    FHIR_SERVER_URL: Optional[str] = None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[Path] = Path("logs/autoradixai.log")

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------
    WS_HEARTBEAT_INTERVAL: int = 30

    @field_validator("UPLOAD_DIR", "OUTPUT_DIR", "MODEL_REGISTRY_PATH",
                     "MODEL_WEIGHTS_PATH", mode="before")
    @classmethod
    def create_dirs(cls, v: Path) -> Path:
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
