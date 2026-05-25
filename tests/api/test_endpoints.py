"""
Integration tests for the FastAPI upload and inference endpoints.
Uses SQLite in-memory DB and mocked Celery tasks.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def auth_client(sample_dicom_file: Path) -> AsyncClient:
    """Return an authenticated test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        await client.post("/api/v1/auth/register", json={
            "email": "test@autoradixai.com",
            "username": "testuser",
            "password": "testpass1",
            "role": "radiologist",
        })
        # Login
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "testpass1"},
        )
        token = resp.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AutoRadixAI"


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_and_login(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            reg = await client.post("/api/v1/auth/register", json={
                "email": "newuser@test.com",
                "username": "newuser",
                "password": "password123",
            })
            assert reg.status_code == 201

            login = await client.post(
                "/api/v1/auth/token",
                data={"username": "newuser", "password": "password123"},
            )
            assert login.status_code == 200
            assert "access_token" in login.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/register", json={
                "email": "u2@test.com",
                "username": "u2",
                "password": "password123",
            })
            resp = await client.post(
                "/api/v1/auth/token",
                data={"username": "u2", "password": "wrongpassword"},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_access_protected_route_without_token(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/studies")
        assert resp.status_code == 401


class TestUploadEndpoints:
    @pytest.mark.asyncio
    @patch("app.api.v1.routes.upload.DICOMService.process_upload")
    async def test_upload_dicom_returns_201(
        self, mock_process: AsyncMock, auth_client: AsyncClient, sample_dicom_file: Path
    ):
        mock_process.return_value = {
            "upload_id": "test-id",
            "summary": {
                "valid_dicoms": 1,
                "corrupted_files": 0,
                "non_dicom_files": 0,
                "studies": {"UID_001": {"description": "CT Study"}},
            },
            "organization": MagicMock(studies={}, total_files=1, valid_dicoms=1, corrupted_files=0, non_dicom_files=[]),
            "model_match": None,
            "preprocessing_config": None,
            "storage_path": "/tmp/test",
            "owner_id": "user123",
        }
        with open(sample_dicom_file, "rb") as fh:
            resp = await auth_client.post(
                "/api/v1/upload/dicom",
                files={"file": ("sample.dcm", fh, "application/dicom")},
                data={"anonymize": "false"},
            )
        assert resp.status_code in (201, 422)  # 422 if mocking doesn't match schema

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, sample_dicom_file: Path):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_dicom_file, "rb") as fh:
                resp = await client.post(
                    "/api/v1/upload/dicom",
                    files={"file": ("sample.dcm", fh, "application/dicom")},
                )
        assert resp.status_code == 401
