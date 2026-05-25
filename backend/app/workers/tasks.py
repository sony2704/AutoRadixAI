"""
Celery Tasks — async background jobs for inference, anonymization, reporting.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pydicom

from app.agents.anonymizer_agent import DICOMAnonymizerAgent
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.feature_extraction_agent import FeatureExtractionAgent
from app.agents.inference_agent import ModelInferenceAgent
from app.agents.report_agent import AIReport, Finding, Measurement, ReportGenerationAgent
from app.config import settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine inside a Celery sync task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_inference_task",
    max_retries=2,
    default_retry_delay=10,
)
def run_inference_task(
    self,
    dicom_path: str,
    model_name: str,
    task: str,
    class_labels: Optional[List[str]] = None,
    preprocessing_config: Optional[Dict[str, Any]] = None,
    study_id: Optional[str] = None,
    prediction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run AI inference on a DICOM file (executed in Celery worker)."""
    logger.info("Starting inference task: model=%s study=%s", model_name, study_id)
    start = time.perf_counter()

    try:
        ds = pydicom.dcmread(dicom_path, force=True)
        pixel_array = ds.pixel_array.astype(np.float32)
    except Exception as exc:
        logger.error("Cannot read DICOM for inference: %s", exc)
        return {"status": "failed", "error": str(exc), "prediction_id": prediction_id}

    agent = ModelInferenceAgent()
    result = _run_async(
        agent.infer(
            pixel_array=pixel_array,
            model_name=model_name,
            task=task,
            class_labels=class_labels,
            preprocessing_config=preprocessing_config,
        )
    )

    # Explainability
    heatmap_path = None
    overlay_path = None
    try:
        explainer = ExplainabilityAgent(output_dir=settings.OUTPUT_DIR / "heatmaps")
        if model_name in agent._loaded_models:
            import torch
            tensor = agent._preprocess(pixel_array, preprocessing_config)
            explain_result = _run_async(
                explainer.explain_gradcam(
                    model=agent._loaded_models[model_name],
                    input_tensor=tensor.to(agent._device),
                    original_image=pixel_array,
                    class_idx=None,
                    prediction_label=result.top_prediction,
                    confidence=result.top_confidence,
                    output_filename=prediction_id or str(uuid.uuid4()),
                )
            )
            heatmap_path = explain_result.heatmap_path
            overlay_path = explain_result.overlay_path
    except Exception as exc:
        logger.warning("Explainability generation failed: %s", exc)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "status": result.status.value,
        "prediction_id": prediction_id,
        "study_id": study_id,
        "model_name": result.model_name,
        "task": result.task,
        "labels": result.labels,
        "confidence_scores": result.confidence_scores,
        "top_prediction": result.top_prediction,
        "top_confidence": result.top_confidence,
        "heatmap_path": heatmap_path,
        "overlay_path": overlay_path,
        "inference_time_ms": round(elapsed_ms, 2),
        "device_used": result.device_used,
        "error": result.error_message,
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_anonymization_task",
    max_retries=2,
)
def run_anonymization_task(
    self,
    dicom_path: str,
    study_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Anonymize a DICOM file asynchronously."""
    agent = DICOMAnonymizerAgent(output_dir=settings.OUTPUT_DIR / "anonymized")
    result = _run_async(agent.anonymize_file(Path(dicom_path)))
    return {
        "study_id": study_id,
        "success": result.success,
        "anonymized_path": result.anonymized_path,
        "tags_removed_count": len(result.tags_removed),
        "error": result.error_message,
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_feature_extraction_task",
)
def run_feature_extraction_task(
    self,
    dicom_path: str,
    study_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract radiomic features from a DICOM file."""
    agent = FeatureExtractionAgent()
    try:
        features = _run_async(agent.extract_from_dicom(Path(dicom_path)))
        from dataclasses import asdict
        return {"study_id": study_id, "status": "completed", "features": asdict(features)}
    except Exception as exc:
        logger.exception("Feature extraction failed")
        return {"study_id": study_id, "status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_report_task",
)
def generate_report_task(
    self,
    report_data: Dict[str, Any],
    formats: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a structured radiology report."""
    formats = formats or ["json", "html"]

    findings = [
        Finding(**f) for f in report_data.get("findings", [])
    ]
    measurements = [
        Measurement(**m) for m in report_data.get("measurements", [])
    ]

    report = AIReport(
        report_id=report_data.get("report_id", str(uuid.uuid4())),
        study_id=report_data["study_id"],
        patient_pseudo_id=report_data.get("patient_pseudo_id", "UNKNOWN"),
        study_date=report_data.get("study_date"),
        modality=report_data["modality"],
        body_part=report_data.get("body_part"),
        model_name=report_data["model_name"],
        model_version=report_data.get("model_version", "1.0"),
        task=report_data["task"],
        top_prediction=report_data["top_prediction"],
        overall_confidence=report_data["overall_confidence"],
        findings=findings,
        measurements=measurements,
        clinical_summary=report_data.get("clinical_summary", ""),
        clinical_explanation=report_data.get("clinical_explanation", ""),
        heatmap_path=report_data.get("heatmap_path"),
        overlay_path=report_data.get("overlay_path"),
        preprocessing_config=report_data.get("preprocessing_config"),
    )

    agent = ReportGenerationAgent(output_dir=settings.OUTPUT_DIR / "reports")
    paths = _run_async(agent.generate_report(report, formats=formats))
    return {"status": "completed", "report_id": report.report_id, "paths": paths}
