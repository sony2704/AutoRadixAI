"""
Pytest configuration and shared fixtures for AutoRadixAI test suite.
"""
from __future__ import annotations

import io
import os
import struct
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import numpy as np
import pydicom
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.main import app
from app.models.database import Base

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use asyncio event loop."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean in-memory database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def sample_dicom_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a minimal valid DICOM file for testing."""
    tmp_dir = tmp_path_factory.mktemp("dicom")
    return _create_dicom_file(tmp_dir / "sample.dcm", modality="CT")


@pytest.fixture(scope="session")
def sample_mri_dicom(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("mri_dicom")
    return _create_dicom_file(tmp_dir / "brain_mri.dcm", modality="MR")


@pytest.fixture(scope="session")
def sample_xray_dicom(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("xray_dicom")
    return _create_dicom_file(tmp_dir / "chest_xray.dcm", modality="CR")


@pytest.fixture
def sample_pixel_array() -> np.ndarray:
    """256x256 grayscale numpy array simulating CT image."""
    rng = np.random.default_rng(42)
    return rng.normal(50, 100, (256, 256)).astype(np.float32)


@pytest.fixture
def sample_dicom_folder(tmp_path: Path) -> Path:
    """Create a folder with multiple DICOM files."""
    study_uid = generate_uid()
    series_uid = generate_uid()
    for i in range(5):
        _create_dicom_file(
            tmp_path / f"slice_{i:03d}.dcm",
            modality="CT",
            study_uid=study_uid,
            series_uid=series_uid,
            instance_number=i + 1,
        )
    return tmp_path


def _create_dicom_file(
    path: Path,
    modality: str = "CT",
    study_uid: str | None = None,
    series_uid: str | None = None,
    instance_number: int = 1,
) -> Path:
    """Create a syntactically valid DICOM file."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.file_meta = file_meta
    ds.is_implicit_VR = False
    ds.is_little_endian = True

    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = study_uid or generate_uid()
    ds.SeriesInstanceUID = series_uid or generate_uid()
    ds.StudyDate = "20260101"
    ds.StudyDescription = f"Test {modality} Study"
    ds.SeriesDescription = f"Test {modality} Series"
    ds.Modality = modality
    ds.PatientName = "Test^Patient"
    ds.PatientID = "TEST001"
    ds.PatientBirthDate = "19800101"
    ds.BodyPartExamined = "CHEST" if modality in ("CT", "CR") else "BRAIN"
    ds.Rows = 64
    ds.Columns = 64
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0
    ds.PixelSpacing = [0.625, 0.625]
    ds.SliceThickness = 1.5
    ds.InstanceNumber = instance_number
    ds.InstitutionName = "AutoRadixAI Test Hospital"

    # Minimal pixel data (64x64 uint16)
    rng = np.random.default_rng(instance_number)
    pixel_data = rng.integers(0, 4095, (64, 64), dtype=np.uint16)
    ds.PixelData = pixel_data.tobytes()

    pydicom.dcmwrite(str(path), ds)
    return path
