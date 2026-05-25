"""
Series ORM model — maps to a DICOM Series (SeriesInstanceUID).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Series(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    study_id: Mapped[str] = mapped_column(String(36), index=True)
    series_instance_uid: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    series_number: Mapped[Optional[int]] = mapped_column(Integer)
    series_description: Mapped[Optional[str]] = mapped_column(String(500))
    modality: Mapped[Optional[str]] = mapped_column(String(20))
    body_part: Mapped[Optional[str]] = mapped_column(String(100))
    num_instances: Mapped[int] = mapped_column(Integer, default=0)
    slice_thickness: Mapped[Optional[float]] = mapped_column(Float)
    pixel_spacing: Mapped[Optional[str]] = mapped_column(String(50))
    image_orientation: Mapped[Optional[str]] = mapped_column(Text)
    storage_path: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    study: Mapped["Study"] = relationship("Study", back_populates="series")  # noqa: F821
