"""
Agent 1: FILE IDENTIFIER AGENT
Detects file type, validates DICOM, detects modality,
organizes studies/series, generates metadata summary.
"""
from __future__ import annotations

import io
import logging
import mimetypes
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pydicom
from pydicom.errors import InvalidDicomError
from pydicom.uid import UID

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    DICOM = "dicom"
    ZIP = "zip"
    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"
    FOLDER = "folder"
    UNKNOWN = "unknown"


class ModalityType(str, Enum):
    CT = "CT"
    MRI = "MR"
    XRAY = "CR"
    DX = "DX"
    US = "US"
    PT = "PT"
    NM = "NM"
    MG = "MG"
    UNKNOWN = "UNKNOWN"


MODALITY_MAP: Dict[str, ModalityType] = {
    "CT": ModalityType.CT,
    "MR": ModalityType.MRI,
    "CR": ModalityType.XRAY,
    "DX": ModalityType.DX,
    "US": ModalityType.US,
    "PT": ModalityType.PT,
    "NM": ModalityType.NM,
    "MG": ModalityType.MG,
}

DICOM_MAGIC = b"DICM"
DICOM_MAGIC_OFFSET = 128


@dataclass
class DICOMMetadata:
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    study_instance_uid: Optional[str] = None
    series_instance_uid: Optional[str] = None
    sop_instance_uid: Optional[str] = None
    study_date: Optional[str] = None
    study_description: Optional[str] = None
    series_description: Optional[str] = None
    modality: str = ModalityType.UNKNOWN.value
    body_part: Optional[str] = None
    institution: Optional[str] = None
    manufacturer: Optional[str] = None
    rows: Optional[int] = None
    columns: Optional[int] = None
    slice_thickness: Optional[float] = None
    pixel_spacing: Optional[List[float]] = None
    num_frames: int = 1
    bits_allocated: Optional[int] = None
    photometric_interpretation: Optional[str] = None
    transfer_syntax_uid: Optional[str] = None
    series_number: Optional[int] = None
    instance_number: Optional[int] = None
    accession_number: Optional[str] = None
    referring_physician: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileIdentificationResult:
    file_path: str
    file_type: FileType
    is_valid_dicom: bool
    is_corrupted: bool
    modality: str
    metadata: Optional[DICOMMetadata]
    error_message: Optional[str]
    file_size_bytes: int


@dataclass
class StudyOrganizationResult:
    studies: Dict[str, Dict[str, List[FileIdentificationResult]]]
    total_files: int
    valid_dicoms: int
    corrupted_files: int
    non_dicom_files: List[FileIdentificationResult]


class FileIdentifierAgent:
    """
    Identifies and organizes medical imaging files.
    Supports single files, folder uploads, and ZIP archives.
    """

    def __init__(self) -> None:
        self._name = "FileIdentifierAgent"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def identify_file(self, file_path: Path) -> FileIdentificationResult:
        """Identify a single file and extract metadata."""
        file_path = Path(file_path)
        if not file_path.exists():
            return FileIdentificationResult(
                file_path=str(file_path),
                file_type=FileType.UNKNOWN,
                is_valid_dicom=False,
                is_corrupted=False,
                modality=ModalityType.UNKNOWN.value,
                metadata=None,
                error_message=f"File not found: {file_path}",
                file_size_bytes=0,
            )
        file_size = file_path.stat().st_size
        file_type = self._detect_file_type(file_path)
        logger.debug("Identified %s as %s", file_path.name, file_type)

        if file_type == FileType.DICOM:
            return await self._process_dicom(file_path, file_type, file_size)
        else:
            return FileIdentificationResult(
                file_path=str(file_path),
                file_type=file_type,
                is_valid_dicom=False,
                is_corrupted=False,
                modality=ModalityType.UNKNOWN.value,
                metadata=None,
                error_message=None,
                file_size_bytes=file_size,
            )

    async def scan_folder(self, folder_path: Path) -> StudyOrganizationResult:
        """Recursively scan a folder and organize DICOM files by Study/Series."""
        folder_path = Path(folder_path)
        all_results: List[FileIdentificationResult] = []

        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                result = await self.identify_file(file_path)
                all_results.append(result)

        return self._organize_studies(all_results)

    async def process_zip(self, zip_path: Path, extract_to: Path) -> StudyOrganizationResult:
        """Extract a ZIP archive and scan its contents."""
        extract_to.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Security: prevent path traversal
                for member in zf.namelist():
                    member_path = (extract_to / member).resolve()
                    if not str(member_path).startswith(str(extract_to.resolve())):
                        logger.warning("Skipping suspicious zip path: %s", member)
                        continue
                zf.extractall(extract_to)
        except zipfile.BadZipFile as exc:
            logger.error("Invalid ZIP archive: %s — %s", zip_path, exc)
            raise
        return await self.scan_folder(extract_to)

    def generate_metadata_summary(
        self, org_result: StudyOrganizationResult
    ) -> Dict[str, Any]:
        """Generate a human-readable metadata summary."""
        summary: Dict[str, Any] = {
            "total_files": org_result.total_files,
            "valid_dicoms": org_result.valid_dicoms,
            "corrupted_files": org_result.corrupted_files,
            "non_dicom_files": len(org_result.non_dicom_files),
            "studies": {},
        }
        for study_uid, series_map in org_result.studies.items():
            modalities = set()
            study_desc = None
            total_instances = 0
            series_summaries: Dict[str, Any] = {}
            for series_uid, instances in series_map.items():
                if instances and instances[0].metadata:
                    meta = instances[0].metadata
                    modalities.add(meta.modality)
                    study_desc = meta.study_description
                series_summaries[series_uid] = {
                    "num_instances": len(instances),
                    "description": (
                        instances[0].metadata.series_description
                        if instances and instances[0].metadata
                        else None
                    ),
                }
                total_instances += len(instances)

            summary["studies"][study_uid] = {
                "description": study_desc,
                "modalities": list(modalities),
                "num_series": len(series_map),
                "num_instances": total_instances,
                "series": series_summaries,
            }
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_file_type(self, path: Path) -> FileType:
        """Determine file type by magic bytes + extension."""
        ext = path.suffix.lower()
        if ext == ".zip":
            return FileType.ZIP
        if ext in {".png"}:
            return FileType.PNG
        if ext in {".jpg", ".jpeg"}:
            return FileType.JPEG
        if ext == ".pdf":
            return FileType.PDF
        if ext == ".dcm":
            return FileType.DICOM

        # Fallback: check DICOM magic bytes
        try:
            with open(path, "rb") as fh:
                fh.seek(DICOM_MAGIC_OFFSET)
                magic = fh.read(4)
            if magic == DICOM_MAGIC:
                return FileType.DICOM
        except OSError:
            pass

        # Try implicit DICOM (no preamble)
        try:
            ds = pydicom.dcmread(str(path), force=True, stop_before_pixels=True)
            if hasattr(ds, "SOPClassUID"):
                return FileType.DICOM
        except Exception:
            pass

        return FileType.UNKNOWN

    async def _process_dicom(
        self, path: Path, file_type: FileType, file_size: int
    ) -> FileIdentificationResult:
        """Parse a DICOM file and extract metadata."""
        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
            metadata = self._extract_metadata(ds)
            return FileIdentificationResult(
                file_path=str(path),
                file_type=file_type,
                is_valid_dicom=True,
                is_corrupted=False,
                modality=metadata.modality,
                metadata=metadata,
                error_message=None,
                file_size_bytes=file_size,
            )
        except InvalidDicomError as exc:
            logger.warning("Corrupted DICOM file %s: %s", path.name, exc)
            return FileIdentificationResult(
                file_path=str(path),
                file_type=file_type,
                is_valid_dicom=False,
                is_corrupted=True,
                modality=ModalityType.UNKNOWN.value,
                metadata=None,
                error_message=str(exc),
                file_size_bytes=file_size,
            )
        except Exception as exc:
            logger.exception("Unexpected error reading DICOM %s", path.name)
            return FileIdentificationResult(
                file_path=str(path),
                file_type=file_type,
                is_valid_dicom=False,
                is_corrupted=True,
                modality=ModalityType.UNKNOWN.value,
                metadata=None,
                error_message=str(exc),
                file_size_bytes=file_size,
            )

    def _extract_metadata(self, ds: pydicom.Dataset) -> DICOMMetadata:
        """Safely extract fields from a pydicom Dataset."""

        def safe_get(tag: str, default: Any = None) -> Any:
            try:
                val = getattr(ds, tag, None)
                if val is None:
                    return default
                if hasattr(val, "original_string"):
                    return str(val)
                return val
            except Exception:
                return default

        raw_modality = safe_get("Modality", "UNKNOWN")
        modality = MODALITY_MAP.get(str(raw_modality).upper(), ModalityType.UNKNOWN).value

        pixel_spacing: Optional[List[float]] = None
        raw_ps = safe_get("PixelSpacing")
        if raw_ps is not None:
            try:
                pixel_spacing = [float(v) for v in raw_ps]
            except Exception:
                pass

        transfer_syntax: Optional[str] = None
        if hasattr(ds, "file_meta") and hasattr(ds.file_meta, "TransferSyntaxUID"):
            transfer_syntax = str(ds.file_meta.TransferSyntaxUID)

        return DICOMMetadata(
            patient_id=safe_get("PatientID"),
            patient_name=str(safe_get("PatientName", "")),
            study_instance_uid=safe_get("StudyInstanceUID"),
            series_instance_uid=safe_get("SeriesInstanceUID"),
            sop_instance_uid=safe_get("SOPInstanceUID"),
            study_date=safe_get("StudyDate"),
            study_description=safe_get("StudyDescription"),
            series_description=safe_get("SeriesDescription"),
            modality=modality,
            body_part=safe_get("BodyPartExamined"),
            institution=safe_get("InstitutionName"),
            manufacturer=safe_get("Manufacturer"),
            rows=safe_get("Rows"),
            columns=safe_get("Columns"),
            slice_thickness=_to_float(safe_get("SliceThickness")),
            pixel_spacing=pixel_spacing,
            num_frames=int(safe_get("NumberOfFrames", 1) or 1),
            bits_allocated=safe_get("BitsAllocated"),
            photometric_interpretation=safe_get("PhotometricInterpretation"),
            transfer_syntax_uid=transfer_syntax,
            series_number=_to_int(safe_get("SeriesNumber")),
            instance_number=_to_int(safe_get("InstanceNumber")),
            accession_number=safe_get("AccessionNumber"),
            referring_physician=str(safe_get("ReferringPhysicianName", "") or ""),
        )

    @staticmethod
    def _organize_studies(
        results: List[FileIdentificationResult],
    ) -> StudyOrganizationResult:
        """Organize identified files into Study → Series → Instance hierarchy."""
        studies: Dict[str, Dict[str, List[FileIdentificationResult]]] = {}
        non_dicom: List[FileIdentificationResult] = []
        valid_count = 0
        corrupted_count = 0

        for result in results:
            if result.is_corrupted:
                corrupted_count += 1
                non_dicom.append(result)
                continue
            if not result.is_valid_dicom or result.metadata is None:
                non_dicom.append(result)
                continue

            valid_count += 1
            study_uid = result.metadata.study_instance_uid or "UNKNOWN_STUDY"
            series_uid = result.metadata.series_instance_uid or "UNKNOWN_SERIES"

            if study_uid not in studies:
                studies[study_uid] = {}
            if series_uid not in studies[study_uid]:
                studies[study_uid][series_uid] = []
            studies[study_uid][series_uid].append(result)

        # Sort instances by instance number within each series
        for study_uid in studies:
            for series_uid in studies[study_uid]:
                studies[study_uid][series_uid].sort(
                    key=lambda r: r.metadata.instance_number or 0
                )

        return StudyOrganizationResult(
            studies=studies,
            total_files=len(results),
            valid_dicoms=valid_count,
            corrupted_files=corrupted_count,
            non_dicom_files=non_dicom,
        )


def _to_float(val: Any) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(val: Any) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None
