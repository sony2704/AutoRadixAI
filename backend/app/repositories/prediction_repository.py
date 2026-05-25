"""
Repository for Prediction ORM operations.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction


class PredictionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, prediction: Prediction) -> Prediction:
        self._db.add(prediction)
        await self._db.commit()
        await self._db.refresh(prediction)
        return prediction

    async def get_by_id(self, prediction_id: str) -> Optional[Prediction]:
        result = await self._db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()

    async def get_by_study(self, study_id: str) -> List[Prediction]:
        result = await self._db.execute(
            select(Prediction)
            .where(Prediction.study_id == study_id)
            .order_by(Prediction.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, prediction: Prediction) -> Prediction:
        await self._db.commit()
        await self._db.refresh(prediction)
        return prediction
