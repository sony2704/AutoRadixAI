"""
Unit tests for FileIdentifierAgent.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.agents.file_identifier_agent import (
    FileIdentifierAgent,
    FileType,
    ModalityType,
)


@pytest.mark.asyncio
class TestFileIdentifierAgent:

    async def test_identify_valid_ct_dicom(self, sample_dicom_file: Path):
        agent = FileIdentifierAgent()
        result = await agent.identify_file(sample_dicom_file)

        assert result.is_valid_dicom is True
        assert result.is_corrupted is False
        assert result.file_type == FileType.DICOM
        assert result.modality == ModalityType.CT.value
        assert result.metadata is not None
        assert result.metadata.rows == 64
        assert result.metadata.columns == 64
        assert result.metadata.pixel_spacing == [0.625, 0.625]
        assert result.error_message is None

    async def test_identify_mri_dicom(self, sample_mri_dicom: Path):
        agent = FileIdentifierAgent()
        result = await agent.identify_file(sample_mri_dicom)
        assert result.modality == ModalityType.MRI.value

    async def test_identify_nonexistent_file(self, tmp_path: Path):
        agent = FileIdentifierAgent()
        result = await agent.identify_file(tmp_path / "nonexistent.dcm")
        assert result.is_valid_dicom is False
        assert result.error_message is not None

    async def test_identify_corrupted_dicom(self, tmp_path: Path):
        corrupted = tmp_path / "corrupted.dcm"
        corrupted.write_bytes(b"This is not a DICOM file at all.")
        agent = FileIdentifierAgent()
        result = await agent.identify_file(corrupted)
        assert result.is_valid_dicom is False

    async def test_scan_folder(self, sample_dicom_folder: Path):
        agent = FileIdentifierAgent()
        org = await agent.scan_folder(sample_dicom_folder)
        assert org.valid_dicoms == 5
        assert org.corrupted_files == 0
        assert len(org.studies) == 1
        study_uid = list(org.studies.keys())[0]
        assert len(list(org.studies[study_uid].values())[0]) == 5

    async def test_process_zip(self, sample_dicom_folder: Path, tmp_path: Path):
        zip_path = tmp_path / "test.zip"
        extract_to = tmp_path / "extracted"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for dcm in sample_dicom_folder.glob("*.dcm"):
                zf.write(dcm, dcm.name)

        agent = FileIdentifierAgent()
        org = await agent.process_zip(zip_path, extract_to)
        assert org.valid_dicoms == 5

    async def test_generate_metadata_summary(self, sample_dicom_folder: Path):
        agent = FileIdentifierAgent()
        org = await agent.scan_folder(sample_dicom_folder)
        summary = agent.generate_metadata_summary(org)
        assert summary["valid_dicoms"] == 5
        assert len(summary["studies"]) == 1

    async def test_identifies_png_file(self, tmp_path: Path):
        png = tmp_path / "test.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        agent = FileIdentifierAgent()
        result = await agent.identify_file(png)
        assert result.file_type == FileType.PNG
        assert result.is_valid_dicom is False
