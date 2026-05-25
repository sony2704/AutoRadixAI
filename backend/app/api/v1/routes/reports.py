"""
Reports routes — generate and download AI radiology reports.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.study_repository import StudyRepository
from app.workers.tasks import generate_report_task

router = APIRouter()
logger = logging.getLogger(__name__)


class ReportGenerateRequest(BaseModel):
    study_id: str
    prediction_id: str
    formats: List[str] = ["json", "html", "pdf"]
    include_heatmap: bool = True


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, summary="Generate AI report")
async def generate_report(
    payload: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    study_repo = StudyRepository(db)
    pred_repo = PredictionRepository(db)

    study = await study_repo.get_by_id(payload.study_id)
    if not study:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study not found")

    prediction = await pred_repo.get_by_id(payload.prediction_id)
    if not prediction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediction not found")

    report_id = str(uuid.uuid4())
    report_data = {
        "report_id": report_id,
        "study_id": study.id,
        "patient_pseudo_id": "ANON-" + study.owner_id[:8] if study.owner_id else "ANON",
        "study_date": study.study_date,
        "modality": study.modality,
        "body_part": None,
        "model_name": prediction.model_name,
        "model_version": "1.0",
        "task": prediction.task,
        "top_prediction": getattr(prediction, "top_prediction", "Unknown"),
        "overall_confidence": prediction.confidence or 0.0,
        "findings": [],
        "measurements": [],
        "clinical_summary": (
            f"AI analysis completed using {prediction.model_name}. "
            f"Modality: {study.modality}. "
            f"Please review findings with clinical context."
        ),
        "clinical_explanation": prediction.findings or "No additional clinical explanation.",
        "heatmap_path": prediction.heatmap_path if payload.include_heatmap else None,
        "overlay_path": prediction.heatmap_path,
        "preprocessing_config": None,
    }

    task = generate_report_task.apply_async(
        kwargs={"report_data": report_data, "formats": payload.formats},
        queue="reporting",
    )

    # Update prediction with report task
    prediction.report_path = str(settings.OUTPUT_DIR / "reports" / f"{report_id}.html")
    await pred_repo.update(prediction)

    return {
        "report_id": report_id,
        "celery_task_id": task.id,
        "status": "queued",
        "message": "Report generation queued.",
    }


@router.get("/download/{report_id}", summary="Download a generated report")
async def download_report(
    report_id: str,
    format: str = "html",
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    ext_map = {"json": ".json", "html": ".html", "pdf": ".pdf"}
    ext = ext_map.get(format.lower(), ".html")
    report_path = settings.OUTPUT_DIR / "reports" / f"{report_id}{ext}"

    if not report_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Report {report_id} not found ({format})")

    media_types = {
        ".json": "application/json",
        ".html": "text/html",
        ".pdf": "application/pdf",
    }
    return FileResponse(
        path=str(report_path),
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=f"autoradixai_report_{report_id}{ext}",
    )
