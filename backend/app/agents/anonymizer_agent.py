"""
Agent 2: DICOM ANONYMIZER AGENT
Removes PHI from DICOM files per DICOM PS3.15 Annex E (Basic Application Level Confidentiality Profile).
Produces audit-logged anonymized copies.
"""
from __future__ import annotations

import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pydicom
from pydicom.errors import InvalidDicomError
from pydicom.sequence import Sequence

logger = logging.getLogger(__name__)


# DICOM tags to remove per HIPAA Safe Harbor / PS3.15 Annex E
PHI_TAGS: Set[str] = {
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAge",
    "PatientWeight",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "PatientMotherBirthName",
    "OtherPatientIDs",
    "OtherPatientIDsSequence",
    "OtherPatientNames",
    "PatientBirthName",
    "MilitaryRank",
    "BranchOfService",
    "PatientInsurancePlanCodeSequence",
    "MedicalRecordLocator",
    "ReferencedPatientSequence",
    "PatientComments",
    "ResponsiblePerson",
    "ResponsibleOrganization",
    "PatientSpeciesDescription",
    "PatientSpeciesCodeSequence",
    "PatientBreedDescription",
    "PatientBreedCodeSequence",
    "BreedRegistrationSequence",
    "DeidentificationMethod",
    "DeidentificationMethodCodeSequence",
    # Physician / institution
    "ReferringPhysicianName",
    "ReferringPhysicianAddress",
    "ReferringPhysicianTelephoneNumbers",
    "ReferringPhysicianIdentificationSequence",
    "PhysiciansOfRecord",
    "PhysiciansOfRecordIdentificationSequence",
    "PerformingPhysicianName",
    "PerformingPhysicianIdentificationSequence",
    "NameOfPhysiciansReadingStudy",
    "PhysiciansReadingStudyIdentificationSequence",
    "OperatorsName",
    "OperatorIdentificationSequence",
    "InstitutionName",
    "InstitutionAddress",
    "InstitutionalDepartmentName",
    "RequestingPhysician",
    "RequestingService",
    "CurrentPatientLocation",
    # Dates / times (may be kept depending on profile — zeroed here)
    "StudyDate",
    "SeriesDate",
    "AcquisitionDate",
    "ContentDate",
    "StudyTime",
    "SeriesTime",
    "AcquisitionTime",
    "ContentTime",
    # UIDs that could link back to original patient
    "StudyID",
    "AccessionNumber",
    "RequestAttributesSequence",
    "ScheduledProcedureStepSequence",
    "RequestedProcedureID",
    "RequestedProcedureDescription",
    "AdmissionID",
    "AdmittingDiagnosesDescription",
    "IssuerOfPatientID",
    "IssuersOfPatientIDQualifiersSequence",
}

# Tags that should be replaced with pseudonyms rather than removed
PSEUDONYMIZE_TAGS: Dict[str, str] = {
    "PatientName": "ANON^PATIENT",
    "PatientID": "",  # filled at runtime
}


@dataclass
class AnonymizationResult:
    original_path: str
    anonymized_path: Optional[str]
    success: bool
    patient_id_original: Optional[str]
    patient_id_pseudo: Optional[str]
    study_instance_uid_original: Optional[str]
    study_instance_uid_new: Optional[str]
    tags_removed: List[str]
    error_message: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DICOMAnonymizerAgent:
    """
    Anonymizes DICOM files by removing/replacing PHI.
    Supports single-file and batch anonymization.
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._audit_log: List[AnonymizationResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def anonymize_file(
        self,
        input_path: Path,
        remap_uids: bool = True,
        keep_descriptors: bool = False,
    ) -> AnonymizationResult:
        """Anonymize a single DICOM file and write to output_dir."""
        input_path = Path(input_path)
        try:
            ds = pydicom.dcmread(str(input_path), force=True)
        except InvalidDicomError as exc:
            result = AnonymizationResult(
                original_path=str(input_path),
                anonymized_path=None,
                success=False,
                patient_id_original=None,
                patient_id_pseudo=None,
                study_instance_uid_original=None,
                study_instance_uid_new=None,
                tags_removed=[],
                error_message=f"Invalid DICOM: {exc}",
            )
            self._audit_log.append(result)
            return result

        original_patient_id = getattr(ds, "PatientID", None)
        original_study_uid = getattr(ds, "StudyInstanceUID", None)
        pseudo_id = f"ANON-{uuid.uuid4().hex[:8].upper()}"
        new_study_uid = self._generate_uid() if remap_uids else original_study_uid

        tags_removed: List[str] = []
        ds_anon = copy.deepcopy(ds)

        # Walk and remove/replace PHI tags
        self._process_dataset(
            ds_anon,
            pseudo_id,
            tags_removed,
            keep_descriptors=keep_descriptors,
        )

        # Remap UIDs to prevent study linkage
        if remap_uids:
            self._remap_uids(ds_anon)

        # Add de-identification markers
        ds_anon.PatientIdentityRemoved = "YES"
        ds_anon.DeidentificationMethod = "DICOM PS3.15 Annex E - Basic Application Level Confidentiality"

        # Save
        output_path = self.output_dir / f"anon_{input_path.name}"
        ds_anon.save_as(str(output_path))
        logger.info("Anonymized %s → %s", input_path.name, output_path.name)

        result = AnonymizationResult(
            original_path=str(input_path),
            anonymized_path=str(output_path),
            success=True,
            patient_id_original=str(original_patient_id) if original_patient_id else None,
            patient_id_pseudo=pseudo_id,
            study_instance_uid_original=str(original_study_uid) if original_study_uid else None,
            study_instance_uid_new=new_study_uid,
            tags_removed=tags_removed,
            error_message=None,
        )
        self._audit_log.append(result)
        return result

    async def anonymize_batch(
        self,
        input_paths: List[Path],
        remap_uids: bool = True,
    ) -> List[AnonymizationResult]:
        """Anonymize multiple DICOM files, maintaining UID consistency within a batch."""
        results: List[AnonymizationResult] = []
        uid_map: Dict[str, str] = {}

        for path in input_paths:
            result = await self.anonymize_file(path, remap_uids=remap_uids)
            results.append(result)

        logger.info(
            "Batch anonymization complete: %d/%d succeeded",
            sum(1 for r in results if r.success),
            len(results),
        )
        return results

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return the in-memory audit log as a list of dicts."""
        return [
            {
                "original_path": r.original_path,
                "anonymized_path": r.anonymized_path,
                "success": r.success,
                "patient_id_pseudo": r.patient_id_pseudo,
                "tags_removed_count": len(r.tags_removed),
                "timestamp": r.timestamp,
                "error": r.error_message,
            }
            for r in self._audit_log
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _process_dataset(
        self,
        ds: pydicom.Dataset,
        pseudo_id: str,
        tags_removed: List[str],
        keep_descriptors: bool,
    ) -> None:
        for tag_name in list(PHI_TAGS):
            if hasattr(ds, tag_name):
                if tag_name == "PatientName":
                    ds.PatientName = "ANON^PATIENT"
                    tags_removed.append(tag_name)
                elif tag_name == "PatientID":
                    ds.PatientID = pseudo_id
                    tags_removed.append(tag_name)
                elif keep_descriptors and tag_name.endswith("Description"):
                    pass  # preserve clinical descriptions if requested
                else:
                    try:
                        delattr(ds, tag_name)
                        tags_removed.append(tag_name)
                    except AttributeError:
                        pass

        # Recurse into sequences
        for elem in ds:
            if elem.VR == "SQ" and elem.value:
                for item in elem.value:
                    if isinstance(item, pydicom.Dataset):
                        self._process_dataset(item, pseudo_id, tags_removed, keep_descriptors)

    @staticmethod
    def _remap_uids(ds: pydicom.Dataset) -> None:
        """Replace identifying UIDs with newly generated ones."""
        uid_fields = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID",
        ]
        for field_name in uid_fields:
            if hasattr(ds, field_name):
                setattr(ds, field_name, pydicom.uid.generate_uid())

    @staticmethod
    def _generate_uid() -> str:
        return str(pydicom.uid.generate_uid())
