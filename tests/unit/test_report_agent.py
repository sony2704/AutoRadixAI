"""
Unit tests for ReportGenerationAgent.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.report_agent import AIReport, ReportGenerationAgent


@pytest.mark.asyncio
class TestReportGenerationAgent:

    async def test_generate_json_report(self, tmp_path: Path, sample_dicom_file: Path):
        agent = ReportGenerationAgent(output_dir=tmp_path)
        report = AIReport(
            study_id="STUDY-001",
            patient_id="ANON-abc123",
            modality="CT",
            body_part="CHEST",
            study_description="CT Chest",
            top_prediction="Pneumonia",
            top_confidence=0.87,
            labels=["Pneumonia", "Normal", "Effusion"],
            confidence_scores={"Pneumonia": 0.87, "Normal": 0.10, "Effusion": 0.03},
            model_name="chest_xray_pneumonia",
            severity="HIGH",
            findings="High confidence detection of pneumonia pattern in lower lobes.",
            recommendations="Correlate with clinical findings. Consider antibiotics.",
        )
        paths = await agent.generate_report(report, formats=["json"])
        assert "json" in paths
        json_path = Path(paths["json"])
        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert data["top_prediction"] == "Pneumonia"
        assert data["top_confidence"] == pytest.approx(0.87)

    async def test_generate_html_report(self, tmp_path: Path):
        agent = ReportGenerationAgent(output_dir=tmp_path)
        report = AIReport(
            study_id="STUDY-002",
            patient_id="ANON-def456",
            modality="MR",
            body_part="BRAIN",
            study_description="Brain MRI",
            top_prediction="Tumor",
            top_confidence=0.93,
            labels=["Tumor", "Normal"],
            confidence_scores={"Tumor": 0.93, "Normal": 0.07},
            model_name="brain_tumor_segmentation",
            severity="CRITICAL",
            findings="Large enhancing mass in right frontal lobe.",
            recommendations="Urgent neurosurgery referral recommended.",
        )
        paths = await agent.generate_report(report, formats=["html"])
        assert "html" in paths
        html_path = Path(paths["html"])
        assert html_path.exists()
        content = html_path.read_text()
        assert "AutoRadixAI" in content
        assert "Tumor" in content

    async def test_report_includes_disclaimer(self, tmp_path: Path):
        agent = ReportGenerationAgent(output_dir=tmp_path)
        report = AIReport(
            study_id="STUDY-003",
            patient_id="ANON-ghi789",
            modality="CR",
            body_part="CHEST",
            study_description="CXR",
            top_prediction="Normal",
            top_confidence=0.95,
            labels=["Normal", "Pneumonia"],
            confidence_scores={"Normal": 0.95, "Pneumonia": 0.05},
            model_name="chest_xray_pneumonia",
            severity="LOW",
            findings="No significant findings.",
            recommendations="Routine follow-up.",
        )
        paths = await agent.generate_report(report, formats=["json"])
        data = json.loads(Path(paths["json"]).read_text())
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 10
