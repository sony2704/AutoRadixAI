"""
Unit tests for ModelInferenceAgent.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import torch

from app.agents.inference_agent import ModelInferenceAgent


@pytest.mark.asyncio
class TestModelInferenceAgent:

    async def test_infer_on_ct_dicom_returns_result(self, sample_dicom_file: Path):
        agent = ModelInferenceAgent()
        result = await agent.infer(
            dicom_path=sample_dicom_file,
            model_name="generic_classification",
        )
        assert result is not None
        assert result.top_prediction is not None
        assert 0.0 <= result.top_confidence <= 1.0
        assert result.device_used in ("cpu", "cuda")

    async def test_infer_produces_confidence_scores(self, sample_dicom_file: Path):
        agent = ModelInferenceAgent()
        result = await agent.infer(
            dicom_path=sample_dicom_file,
            model_name="generic_classification",
        )
        assert isinstance(result.confidence_scores, dict)
        assert len(result.confidence_scores) > 0

    async def test_infer_uses_cpu_when_gpu_disabled(self, sample_dicom_file: Path):
        with patch("app.agents.inference_agent.settings") as mock_settings:
            mock_settings.GPU_ENABLED = False
            mock_settings.INFERENCE_TIMEOUT_SECONDS = 60
            mock_settings.MODEL_REGISTRY_PATH = "ai-models/weights"
            agent = ModelInferenceAgent()
            result = await agent.infer(
                dicom_path=sample_dicom_file,
                model_name="generic_classification",
            )
        assert result.device_used == "cpu"

    async def test_infer_unknown_model_raises_or_falls_back(self, sample_dicom_file: Path):
        agent = ModelInferenceAgent()
        try:
            result = await agent.infer(
                dicom_path=sample_dicom_file,
                model_name="nonexistent_model_xyz",
            )
            # Graceful fallback: result is still returned
            assert result is not None
        except Exception as exc:
            assert "not found" in str(exc).lower() or "model" in str(exc).lower()

    async def test_infer_on_numpy_array(self, sample_pixel_array):
        agent = ModelInferenceAgent()
        result = await agent.infer(
            pixel_array=sample_pixel_array,
            model_name="generic_classification",
        )
        assert result.top_confidence >= 0.0
