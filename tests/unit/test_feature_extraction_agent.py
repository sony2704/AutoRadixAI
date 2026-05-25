"""
Unit tests for FeatureExtractionAgent.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.agents.feature_extraction_agent import FeatureExtractionAgent


@pytest.mark.asyncio
class TestFeatureExtractionAgent:

    async def test_extract_from_dicom(self, sample_dicom_file: Path):
        agent = FeatureExtractionAgent()
        features = await agent.extract_from_dicom(sample_dicom_file)

        assert features.rows == 64
        assert features.columns == 64
        assert features.mean != 0.0
        assert features.std > 0.0
        assert features.entropy >= 0.0
        assert len(features.histogram_bins) == 64
        assert len(features.histogram_counts) == 64
        assert features.pixel_spacing == [0.625, 0.625]
        assert features.slice_thickness == 1.5

    async def test_extract_from_numpy(self, sample_pixel_array: np.ndarray):
        agent = FeatureExtractionAgent()
        features = await agent.extract_from_numpy(sample_pixel_array)
        assert features.mean == pytest.approx(np.mean(sample_pixel_array), abs=0.1)
        assert features.std == pytest.approx(np.std(sample_pixel_array), abs=0.1)

    async def test_glcm_features_present(self, sample_pixel_array: np.ndarray):
        agent = FeatureExtractionAgent()
        features = await agent.extract_from_numpy(sample_pixel_array)
        # GLCM values should be non-trivial for random noise
        assert features.glcm_energy >= 0.0
        assert features.glcm_homogeneity >= 0.0

    async def test_lbp_histogram_normalized(self, sample_pixel_array: np.ndarray):
        agent = FeatureExtractionAgent()
        features = await agent.extract_from_numpy(sample_pixel_array)
        if features.lbp_histogram:
            total = sum(features.lbp_histogram)
            assert total == pytest.approx(1.0, abs=1e-5)

    async def test_shape_features_present(self, sample_pixel_array: np.ndarray):
        agent = FeatureExtractionAgent()
        features = await agent.extract_from_numpy(sample_pixel_array)
        assert features.area >= 0.0
        assert features.perimeter >= 0.0
