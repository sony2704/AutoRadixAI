"""
Unit tests for PreprocessingRecommendationAgent.
"""
from __future__ import annotations

import pytest

from app.agents.preprocessing_agent import PreprocessingRecommendationAgent


@pytest.mark.asyncio
class TestPreprocessingRecommendationAgent:

    async def test_ct_lung_gets_lung_window(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="CT", body_part="LUNG")
        assert config.convert_to_hu is True
        assert config.window is not None
        assert config.window.center == -600
        assert config.window.width == 1500

    async def test_ct_brain_gets_brain_window(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="CT", body_part="BRAIN")
        assert config.window.center == 40
        assert config.window.width == 80

    async def test_mri_no_windowing(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="MR", body_part="BRAIN")
        assert config.window is None
        assert config.normalize.method == "zscore"

    async def test_xray_uses_minmax(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="CR", body_part="CHEST")
        assert config.normalize.method == "minmax"

    async def test_segmentation_task_returns_unet(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="CT", task="tumor_segmentation")
        assert config.segmentation.strategy == "unet"

    async def test_to_dict_is_serializable(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="CT", body_part="CHEST")
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "resize" in d
        assert "normalize" in d

    async def test_us_denoising_recommended(self):
        agent = PreprocessingRecommendationAgent()
        config = await agent.recommend(modality="US", body_part="ABDOMEN")
        assert config.denoise.method == "nlm"
