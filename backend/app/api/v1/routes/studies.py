"""
Studies routes — CRUD for DICOM studies and series.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import StudyNotFoundError
from app.dependencies import get_current_user, get_db
from app.models.study import Study
from app.models.user import User
from app.repositories.study_repository import StudyRepository

router = APIRouter()
logger = logging.getLogger(__name__)


class StudyOut(BaseModel):
    id: str
    study_instance_uid: Optional[str]
    study_date: Optional[str]
    study_description: Optional[str]
    modality: str
    institution: Optional[str]
    num_series: int
    num_instances: int
    status: str
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=List[StudyOut], summary="List all studies for current user")
async def list_studies(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudyOut]:
    repo = StudyRepository(db)
    if current_user.is_superuser:
        studies = await repo.list_all(limit=limit, offset=offset)
    else:
        studies = await repo.get_by_owner(current_user.id, limit=limit, offset=offset)
    return [StudyOut(
        id=s.id,
        study_instance_uid=s.study_instance_uid,
        study_date=s.study_date,
        study_description=s.study_description,
        modality=s.modality,
        institution=s.institution,
        num_series=s.num_series,
        num_instances=s.num_instances,
        status=s.status,
        created_at=s.created_at.isoformat(),
    ) for s in studies]


@router.get("/{study_id}", response_model=StudyOut, summary="Get a specific study")
async def get_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyOut:
    repo = StudyRepository(db)
    study = await repo.get_by_id(study_id)
    if not study:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Study {study_id} not found")
    if not current_user.is_superuser and study.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    return StudyOut(
        id=study.id,
        study_instance_uid=study.study_instance_uid,
        study_date=study.study_date,
        study_description=study.study_description,
        modality=study.modality,
        institution=study.institution,
        num_series=study.num_series,
        num_instances=study.num_instances,
        status=study.status,
        created_at=study.created_at.isoformat(),
    )


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a study")
async def delete_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    repo = StudyRepository(db)
    study = await repo.get_by_id(study_id)
    if not study:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Study {study_id} not found")
    if not current_user.is_superuser and study.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    await repo.delete(study)
    logger.info("Study %s deleted by user %s", study_id, current_user.id)
