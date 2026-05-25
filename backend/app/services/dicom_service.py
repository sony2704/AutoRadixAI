"""
DICOM Service — orchestrates agents and business logic for DICOM processing.
"""
from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pydicom

from app.agents.anonymizer_agent import DICOMAnonymizerAgent
from app.agents.feature_extraction_agent import FeatureExtractionAgent, RadiomicFeatures
from app.agents.file_identifier_agent import (
    FileIdentifierAgent,
    FileIdentificationResult,
    StudyOrganizationResult,
)
from app.agents.model_matcher_agent import MatchResult, ModelMatcherAgent
from app.agents.preprocessing_agent import PreprocessingConfig, PreprocessingRecommendationAgent
from app.config import settings
from app.core.exceptions import DICOMParseError, StorageError
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class DICOMService:
    """
    Orchestrates the full DICOM processing pipeline:
    upload → identify → store → anonymize → extract features → match model → recommend preprocessing
    """

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage
        self._file_identifier = FileIdentifierAgent()
        self._anonymizer = DICOMAnonymizerAgent(
            output_dir=settings.OUTPUT_DIR / "anonymized"
        )
        self._feature_extractor = FeatureExtractionAgent()
        self._model_matcher = ModelMatcherAgent()
        self._preprocessing_advisor = PreprocessingRecommendationAgent()

    # ------------------------------------------------------------------
    # Upload pipeline
    # ------------------------------------------------------------------

    async def process_upload(
        self,
        temp_path: Path,
        original_filename: str,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full processing pipeline for a single uploaded file.
        Returns structured metadata for DB persistence.
        """
        upload_id = str(uuid.uuid4())
        dest_dir = settings.UPLOAD_DIR / upload_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(original_filename).suffix.lower()

        if ext == ".zip":
            extract_dir = dest_dir / "extracted"
            org_result = await self._file_identifier.process_zip(temp_path, extract_dir)
        elif temp_path.is_dir():
            org_result = await self._file_identifier.scan_folder(temp_path)
        else:
            # Single file
            result = await self._file_identifier.identify_file(temp_path)
            dest_path = dest_dir / original_filename
            shutil.copy2(temp_path, dest_path)

            org_result = self._file_identifier._organize_studies([result])

        summary = self._file_identifier.generate_metadata_summary(org_result)

        # For the first valid study, get match and preprocessing recommendation
        match_result = None
        preprocessing_config = None

        for study_uid, series_map in org_result.studies.items():
            for series_uid, instances in series_map.items():
                if instances and instances[0].metadata:
                    meta = instances[0].metadata
                    match_result = await self._model_matcher.match(
                        modality=meta.modality,
                        body_part=meta.body_part,
                        study_description=meta.study_description,
                        series_description=meta.series_description,
                    )
                    preprocessing_config = await self._preprocessing_advisor.recommend(
                        modality=meta.modality,
                        body_part=meta.body_part,
                        task=match_result.model.task if match_result.model else None,
                    )
                    break
            break

        return {
            "upload_id": upload_id,
            "summary": summary,
            "organization": org_result,
            "model_match": match_result,
            "preprocessing_config": preprocessing_config.to_dict() if preprocessing_config else None,
            "storage_path": str(dest_dir),
            "owner_id": owner_id,
        }

    async def read_pixel_array(self, dicom_path: Path):
        """Load pixel data from a DICOM file."""
        try:
            ds = pydicom.dcmread(str(dicom_path), force=True)
            return ds.pixel_array
        except Exception as exc:
            raise DICOMParseError(f"Cannot read pixel data: {exc}") from exc

    async def extract_features(
        self, dicom_path: Path
    ) -> RadiomicFeatures:
        return await self._feature_extractor.extract_from_dicom(dicom_path)

    async def anonymize(self, dicom_path: Path) -> Dict[str, Any]:
        result = await self._anonymizer.anonymize_file(dicom_path)
        return {
            "success": result.success,
            "anonymized_path": result.anonymized_path,
            "tags_removed": result.tags_removed,
            "error": result.error_message,
        }
