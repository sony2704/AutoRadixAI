"""
Inference routes — trigger AI inference, check job status.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.prediction import Prediction, PredictionStatus
from app.models.user import User
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.study_repository import StudyRepository
from app.workers.tasks import run_inference_task

router = APIRouter()
logger = logging.getLogger(__name__)


class InferenceRequest(BaseModel):
    study_id: str
    model_name: Optional[str] = None
    task: Optional[str] = None
    class_labels: Optional[List[str]] = None
    formats: List[str] = ["json", "html"]


class InferenceStatusResponse(BaseModel):
    prediction_id: str
    study_id: str
    status: str
    model_name: Optional[str]
    task: Optional[str]
    top_prediction: Optional[str]
    top_confidence: Optional[float]
    heatmap_path: Optional[str]
    report_path: Optional[str]
    inference_time_ms: Optional[int]
    celery_task_id: Optional[str]
    error_message: Optional[str]
    created_at: str


@router.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI inference on a study",
)
async def run_inference(
    payload: InferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    study_repo = StudyRepository(db)
    study = await study_repo.get_by_id(payload.study_id)
    if not study:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study not found")
    if not current_user.is_superuser and study.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    # Auto-select model if not specified
    model_name = payload.model_name or "generic_classification"
    task = payload.task or "classification"

    # Resolve DICOM path (use first file in storage path)
    dicom_path: Optional[str] = None
    if study.storage_path:
        storage_dir = Path(study.storage_path)
        dcm_files = list(storage_dir.rglob("*.dcm"))
        if dcm_files:
            dicom_path = str(dcm_files[0])

    if not dicom_path:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No DICOM file found for this study",
        )

    prediction_id = str(uuid.uuid4())
    pred_repo = PredictionRepository(db)
    prediction = Prediction(
        id=prediction_id,
        study_id=study.id,
        model_name=model_name,
        task=task,
        status=PredictionStatus.PENDING.value,
    )
    prediction = await pred_repo.create(prediction)

    # Dispatch to Celery
    celery_task = run_inference_task.apply_async(
        kwargs={
            "dicom_path": dicom_path,
            "model_name": model_name,
            "task": task,
            "class_labels": payload.class_labels,
            "study_id": study.id,
            "prediction_id": prediction_id,
        },
        queue="inference",
    )

    prediction.celery_task_id = celery_task.id
    prediction.status = PredictionStatus.RUNNING.value
    await pred_repo.update(prediction)

    logger.info(
        "Inference dispatched: prediction=%s celery=%s", prediction_id, celery_task.id
    )
    return {
        "prediction_id": prediction_id,
        "celery_task_id": celery_task.id,
        "status": "queued",
        "message": "Inference job queued. Poll /inference/status/{prediction_id} for results.",
    }


@router.get(
    "/status/{prediction_id}",
    response_model=InferenceStatusResponse,
    summary="Get inference job status",
)
async def get_inference_status(
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InferenceStatusResponse:
    pred_repo = PredictionRepository(db)
    prediction = await pred_repo.get_by_id(prediction_id)
    if not prediction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediction not found")

    # Sync Celery task result if still running
    if prediction.status == PredictionStatus.RUNNING.value and prediction.celery_task_id:
        from celery.result import AsyncResult
        from app.workers.celery_app import celery_app as _app
        task_result = AsyncResult(prediction.celery_task_id, app=_app)
        if task_result.ready():
            result_data = task_result.result or {}
            if isinstance(result_data, dict):
                prediction.status = result_data.get("status", PredictionStatus.COMPLETED.value)
                prediction.top_prediction = result_data.get("top_prediction")
                prediction.confidence = result_data.get("top_confidence")
                labels = result_data.get("labels", [])
                prediction.labels = json.dumps(labels)
                prediction.heatmap_path = result_data.get("overlay_path")
                prediction.inference_time_ms = int(result_data.get("inference_time_ms", 0))
                prediction.completed_at = datetime.now(timezone.utc)
                if result_data.get("error"):
                    prediction.status = PredictionStatus.FAILED.value
                    prediction.error_message = result_data["error"]
            await pred_repo.update(prediction)

    return InferenceStatusResponse(
        prediction_id=prediction.id,
        study_id=prediction.study_id,
        status=prediction.status,
        model_name=prediction.model_name,
        task=prediction.task,
        top_prediction=getattr(prediction, "top_prediction", None),
        top_confidence=prediction.confidence,
        heatmap_path=prediction.heatmap_path,
        report_path=prediction.report_path,
        inference_time_ms=prediction.inference_time_ms,
        celery_task_id=prediction.celery_task_id,
        error_message=prediction.error_message,
        created_at=prediction.created_at.isoformat(),
    )


@router.get(
    "/study/{study_id}",
    summary="Get all predictions for a study",
)
async def get_predictions_for_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    pred_repo = PredictionRepository(db)
    predictions = await pred_repo.get_by_study(study_id)
    return [
        {
            "prediction_id": p.id,
            "model_name": p.model_name,
            "task": p.task,
            "status": p.status,
            "confidence": p.confidence,
            "created_at": p.created_at.isoformat(),
        }
        for p in predictions
    ]
