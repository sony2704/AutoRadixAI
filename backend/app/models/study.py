"""
Study ORM model — maps to a DICOM Study (StudyInstanceUID).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Modality(str, Enum):
    CT = "CT"
    MRI = "MR"
    XRAY = "CR"
    DX = "DX"
    ULTRASOUND = "US"
    PT = "PT"
    NM = "NM"
    MG = "MG"
    UNKNOWN = "UNKNOWN"


class StudyStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    study_instance_uid: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    study_date: Mapped[Optional[str]] = mapped_column(String(20))
    study_description: Mapped[Optional[str]] = mapped_column(String(500))
    accession_number: Mapped[Optional[str]] = mapped_column(String(100))
    modality: Mapped[str] = mapped_column(String(20), default=Modality.UNKNOWN.value)
    institution: Mapped[Optional[str]] = mapped_column(String(255))
    referring_physician: Mapped[Optional[str]] = mapped_column(String(255))
    num_series: Mapped[int] = mapped_column(Integer, default=0)
    num_instances: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default=StudyStatus.UPLOADED.value)
    storage_path: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    series: Mapped[List["Series"]] = relationship(  # noqa: F821
        "Series", back_populates="study", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="study", cascade="all, delete-orphan"
    )
