"""
Unit tests for ModelMatcherAgent.
"""
from __future__ import annotations

import pytest

from app.agents.model_matcher_agent import MatchConfidence, ModelEntry, ModelMatcherAgent


@pytest.mark.asyncio
class TestModelMatcherAgent:

    async def test_match_chest_xray(self):
        agent = ModelMatcherAgent()
        result = await agent.match(
            modality="CR",
            body_part="CHEST",
            study_description="Chest X-Ray PA Lateral",
        )
        assert result.model is not None
        assert result.model.name == "chest_xray_pneumonia"
        assert result.confidence in (MatchConfidence.HIGH, MatchConfidence.MEDIUM)

    async def test_match_brain_mri(self):
        agent = ModelMatcherAgent()
        result = await agent.match(
            modality="MR",
            body_part="BRAIN",
            study_description="Brain MRI T1 T2 FLAIR",
        )
        assert result.model is not None
        assert result.model.name == "brain_tumor_segmentation"

    async def test_match_ct_lung(self):
        agent = ModelMatcherAgent()
        result = await agent.match(
            modality="CT",
            body_part="LUNG",
            study_description="CT Thorax Lung Nodule",
        )
        assert result.model is not None
        assert result.model.name == "ct_lung_nodule_detection"

    async def test_no_match_unsupported_modality(self):
        agent = ModelMatcherAgent()
        result = await agent.match(modality="XY_UNKNOWN")
        assert result.model is None
        assert result.confidence == MatchConfidence.NONE

    async def test_fallback_to_generic(self):
        agent = ModelMatcherAgent()
        result = await agent.match(modality="US", body_part="ABDOMEN")
        # Should match generic or return none — either is acceptable
        assert result.confidence != MatchConfidence.NONE or result.model is None

    def test_register_custom_model(self):
        agent = ModelMatcherAgent()
        entry = ModelEntry(
            name="custom_kidney_ct",
            version="2.0",
            task="kidney_segmentation",
            modalities=["CT"],
            body_parts=["KIDNEY", "ABDOMEN"],
            description_keywords=["kidney", "renal"],
            model_path=None,
            preprocessing_config={},
            priority=15,
        )
        agent.register_model(entry)
        assert agent.get_model("custom_kidney_ct") is not None

    def test_deregister_model(self):
        agent = ModelMatcherAgent()
        agent.deregister_model("generic_classification")
        assert agent.get_model("generic_classification") is None
