"""
API v1 Router — aggregates all route modules.
"""
from fastapi import APIRouter

from app.api.v1.routes import auth, inference, reports, studies, upload, websocket

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_v1_router.include_router(studies.router, prefix="/studies", tags=["Studies"])
api_v1_router.include_router(inference.router, prefix="/inference", tags=["Inference"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
