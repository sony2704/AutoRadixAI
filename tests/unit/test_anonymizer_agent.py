"""
Unit tests for DICOMAnonymizerAgent.
"""
from __future__ import annotations

from pathlib import Path

import pydicom
import pytest

from app.agents.anonymizer_agent import DICOMAnonymizerAgent


@pytest.mark.asyncio
class TestDICOMAnonymizerAgent:

    async def test_anonymize_removes_phi(self, sample_dicom_file: Path, tmp_path: Path):
        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        result = await agent.anonymize_file(sample_dicom_file)

        assert result.success is True
        assert result.anonymized_path is not None
        assert result.error_message is None
        assert len(result.tags_removed) > 0

        # Verify PHI is gone in output file
        anon_ds = pydicom.dcmread(result.anonymized_path)
        assert str(anon_ds.PatientName) == "ANON^PATIENT"
        assert str(anon_ds.PatientID).startswith("ANON-")

    async def test_anonymize_marks_deidentification(self, sample_dicom_file: Path, tmp_path: Path):
        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        result = await agent.anonymize_file(sample_dicom_file)
        anon_ds = pydicom.dcmread(result.anonymized_path)
        assert anon_ds.PatientIdentityRemoved == "YES"

    async def test_anonymize_remaps_uids(self, sample_dicom_file: Path, tmp_path: Path):
        orig_ds = pydicom.dcmread(str(sample_dicom_file))
        orig_uid = str(orig_ds.StudyInstanceUID)

        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        result = await agent.anonymize_file(sample_dicom_file, remap_uids=True)
        anon_ds = pydicom.dcmread(result.anonymized_path)
        assert str(anon_ds.StudyInstanceUID) != orig_uid

    async def test_anonymize_corrupted_file(self, tmp_path: Path):
        bad = tmp_path / "bad.dcm"
        bad.write_bytes(b"not a dicom")
        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        result = await agent.anonymize_file(bad)
        assert result.success is False
        assert result.error_message is not None

    async def test_batch_anonymization(
        self, sample_dicom_folder: Path, tmp_path: Path
    ):
        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        files = list(sample_dicom_folder.glob("*.dcm"))
        results = await agent.anonymize_batch(files)
        assert len(results) == len(files)
        assert all(r.success for r in results)

    async def test_audit_log_populated(self, sample_dicom_file: Path, tmp_path: Path):
        agent = DICOMAnonymizerAgent(output_dir=tmp_path / "anon")
        await agent.anonymize_file(sample_dicom_file)
        log = agent.get_audit_log()
        assert len(log) == 1
        assert log[0]["success"] is True
