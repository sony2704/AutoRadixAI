"""
Upload routes — drag-drop, folder, ZIP, single file uploads.
"""
from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.study import Study, StudyStatus
from app.models.user import User
from app.repositories.study_repository import StudyRepository
from app.services.dicom_service import DICOMService
from app.services.storage_service import StorageService

router = APIRouter()
logger = logging.getLogger(__name__)
_storage = StorageService()


class UploadResponse(BaseModel):
    upload_id: str
    study_ids: List[str]
    summary: dict
    model_match: Optional[dict]
    preprocessing_config: Optional[dict]
    message: str


@router.post(
    "/dicom",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a DICOM file, ZIP archive, or folder",
)
async def upload_dicom(
    file: UploadFile = File(..., description="DICOM file, ZIP archive, PNG, JPG, or PDF"),
    anonymize: bool = Form(False, description="Auto-anonymize after upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    # Validate file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit",
        )

    # Save to temp file
    suffix = Path(file.filename or "upload").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        temp_path = Path(tmp.name)

    try:
        dicom_svc = DICOMService(storage=_storage)
        result = await dicom_svc.process_upload(
            temp_path=temp_path,
            original_filename=file.filename or "upload.dcm",
            owner_id=current_user.id,
        )

        # Persist studies to DB
        study_repo = StudyRepository(db)
        study_ids: List[str] = []

        for study_uid, series_map in result["organization"].studies.items():
            first_meta = None
            for series_uid, instances in series_map.items():
                if instances and instances[0].metadata:
                    first_meta = instances[0].metadata
                    break

            study = Study(
                study_instance_uid=study_uid,
                study_date=first_meta.study_date if first_meta else None,
                study_description=first_meta.study_description if first_meta else None,
                accession_number=first_meta.accession_number if first_meta else None,
                modality=first_meta.modality if first_meta else "UNKNOWN",
                institution=first_meta.institution if first_meta else None,
                num_series=len(series_map),
                num_instances=sum(len(v) for v in series_map.values()),
                status=StudyStatus.UPLOADED.value,
                storage_path=result["storage_path"],
                owner_id=current_user.id,
            )
            study = await study_repo.create(study)
            study_ids.append(study.id)

        logger.info(
            "Upload complete: %d studies, %d valid DICOMs",
            len(study_ids),
            result["summary"].get("valid_dicoms", 0),
        )

        match_dict = None
        if result["model_match"]:
            m = result["model_match"]
            match_dict = {
                "model_name": m.model.name if m.model else None,
                "task": m.model.task if m.model else None,
                "confidence": m.confidence.value,
                "score": m.score,
                "reasoning": m.reasoning,
            }

        return UploadResponse(
            upload_id=result["upload_id"],
            study_ids=study_ids,
            summary=result["summary"],
            model_match=match_dict,
            preprocessing_config=result["preprocessing_config"],
            message=f"Successfully processed {result['summary'].get('valid_dicoms', 0)} DICOM file(s).",
        )
    finally:
        temp_path.unlink(missing_ok=True)


@router.post(
    "/batch",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload multiple DICOM files at once",
)
async def upload_batch(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if len(files) > 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Maximum 100 files per batch")

    results = []
    for file in files:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        content = await file.read(max_bytes + 1)
        if len(content) > max_bytes:
            results.append({"filename": file.filename, "status": "skipped", "reason": "too_large"})
            continue

        suffix = Path(file.filename or "upload").suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_path = Path(tmp.name)

        try:
            dicom_svc = DICOMService(storage=_storage)
            result = await dicom_svc.process_upload(
                temp_path=temp_path,
                original_filename=file.filename or "upload.dcm",
                owner_id=current_user.id,
            )
            results.append({
                "filename": file.filename,
                "status": "accepted",
                "upload_id": result["upload_id"],
                "valid_dicoms": result["summary"].get("valid_dicoms", 0),
            })
        except Exception as exc:
            results.append({"filename": file.filename, "status": "error", "detail": str(exc)})
        finally:
            temp_path.unlink(missing_ok=True)

    return {"batch_results": results, "total": len(files)}
