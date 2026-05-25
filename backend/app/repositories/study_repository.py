"""
Repository layer for Study ORM operations.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.study import Study


class StudyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, study: Study) -> Study:
        self._db.add(study)
        await self._db.commit()
        await self._db.refresh(study)
        return study

    async def get_by_id(self, study_id: str) -> Optional[Study]:
        stmt = (
            select(Study)
            .where(Study.id == study_id)
            .options(selectinload(Study.series), selectinload(Study.predictions))
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: str, limit: int = 50, offset: int = 0) -> List[Study]:
        stmt = (
            select(Study)
            .where(Study.owner_id == owner_id)
            .order_by(Study.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Study]:
        stmt = (
            select(Study)
            .order_by(Study.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, study: Study) -> Study:
        await self._db.commit()
        await self._db.refresh(study)
        return study

    async def delete(self, study: Study) -> None:
        await self._db.delete(study)
        await self._db.commit()
