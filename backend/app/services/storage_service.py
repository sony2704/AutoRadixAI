"""
Storage Service — local filesystem with S3-compatible interface.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class StorageService:
    """
    Abstracts file storage.
    Uses local filesystem by default; can be extended to S3 via boto3.
    """

    def __init__(self) -> None:
        self._use_s3 = settings.USE_S3
        if self._use_s3:
            self._init_s3()

    def _init_s3(self) -> None:
        try:
            import boto3
            self._s3 = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            )
            self._bucket = settings.S3_BUCKET
        except ImportError:
            logger.warning("boto3 not installed; falling back to local storage.")
            self._use_s3 = False

    async def save_upload(self, source: Path, dest_key: str) -> str:
        """Save an uploaded file. Returns storage key/path."""
        dest = settings.UPLOAD_DIR / dest_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, dest)
            logger.debug("Saved upload to %s", dest)
            return str(dest)
        except OSError as exc:
            raise StorageError(f"Failed to save upload: {exc}") from exc

    async def get_path(self, key: str) -> Optional[Path]:
        """Resolve a storage key to a local path."""
        path = Path(key) if Path(key).is_absolute() else settings.UPLOAD_DIR / key
        return path if path.exists() else None

    async def delete(self, key: str) -> bool:
        """Delete a stored file."""
        path = settings.UPLOAD_DIR / key
        try:
            if path.exists():
                path.unlink()
                return True
        except OSError as exc:
            logger.error("Failed to delete %s: %s", key, exc)
        return False

    async def list_uploads(self, prefix: str = "") -> list:
        base = settings.UPLOAD_DIR / prefix
        if not base.exists():
            return []
        return [str(p) for p in base.rglob("*") if p.is_file()]
