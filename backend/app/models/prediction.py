"""
Prediction ORM model — stores AI inference results.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class PredictionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    study_id: Mapped[str] = mapped_column(String(36), index=True)
    series_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    task: Mapped[str] = mapped_column(String(100))  # e.g. "tumor_segmentation"
    status: Mapped[str] = mapped_column(String(30), default=PredictionStatus.PENDING.value)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    labels: Mapped[Optional[str]] = mapped_column(Text)       # JSON array
    findings: Mapped[Optional[str]] = mapped_column(Text)     # free text
    result_json: Mapped[Optional[str]] = mapped_column(Text)  # full result blob
    heatmap_path: Mapped[Optional[str]] = mapped_column(Text)
    report_path: Mapped[Optional[str]] = mapped_column(Text)
    inference_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    study: Mapped["Study"] = relationship("Study", back_populates="predictions")  # noqa: F821
