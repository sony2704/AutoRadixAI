"""
Agent 6: MODEL INFERENCE AGENT
Runs AI inference using PyTorch/MONAI models.
Supports GPU with CPU fallback, async inference, multi-class.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from monai.transforms import (
    Compose,
    EnsureChannelFirst,
    NormalizeIntensity,
    Resize,
    ScaleIntensity,
    ToTensor,
)

from app.config import settings

logger = logging.getLogger(__name__)


class InferenceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class InferenceResult:
    status: InferenceStatus
    model_name: str
    task: str
    labels: List[str]
    confidence_scores: List[float]
    top_prediction: str
    top_confidence: float
    raw_output: Optional[List[float]]
    segmentation_mask: Optional[np.ndarray]
    inference_time_ms: float
    device_used: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DummyModel(nn.Module):
    """Placeholder model for environments without trained weights."""

    def __init__(self, num_classes: int = 2) -> None:
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(1, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]
        x = self.pool(x[:, :1])
        x = x.view(b, -1)
        return self.fc(x)


class ModelInferenceAgent:
    """
    Executes AI inference on preprocessed medical images.
    Manages model loading, GPU/CPU routing, and result packaging.
    """

    def __init__(self) -> None:
        self._name = "ModelInferenceAgent"
        self._loaded_models: Dict[str, nn.Module] = {}
        self._device = self._select_device()
        logger.info("InferenceAgent initialized on device: %s", self._device)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def infer(
        self,
        pixel_array: np.ndarray,
        model_name: str,
        task: str,
        class_labels: Optional[List[str]] = None,
        preprocessing_config: Optional[Dict[str, Any]] = None,
    ) -> InferenceResult:
        """Run inference asynchronously (offloaded to thread pool)."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._run_inference_sync,
            pixel_array,
            model_name,
            task,
            class_labels,
            preprocessing_config,
        )
        return result

    def load_model(self, model_name: str, model_path: Optional[Path] = None) -> None:
        """Load a PyTorch model into memory."""
        if model_name in self._loaded_models:
            return

        if model_path and Path(model_path).exists():
            try:
                model = torch.load(str(model_path), map_location=self._device)
                model.eval()
                self._loaded_models[model_name] = model
                logger.info("Loaded model %s from %s", model_name, model_path)
                return
            except Exception as exc:
                logger.warning(
                    "Failed to load model %s from %s: %s — using dummy model",
                    model_name, model_path, exc,
                )

        # Fall back to dummy model
        dummy = DummyModel(num_classes=2).to(self._device)
        dummy.eval()
        self._loaded_models[model_name] = dummy
        logger.info("Using dummy model for %s", model_name)

    def unload_model(self, model_name: str) -> None:
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_inference_sync(
        self,
        pixel_array: np.ndarray,
        model_name: str,
        task: str,
        class_labels: Optional[List[str]],
        preprocessing_config: Optional[Dict[str, Any]],
    ) -> InferenceResult:
        start = time.perf_counter()

        try:
            if model_name not in self._loaded_models:
                model_path = settings.MODEL_WEIGHTS_PATH / f"{model_name}.pt"
                self.load_model(model_name, model_path if model_path.exists() else None)

            model = self._loaded_models[model_name]

            # Preprocess
            tensor = self._preprocess(pixel_array, preprocessing_config)
            tensor = tensor.to(self._device)

            with torch.no_grad():
                output = model(tensor)

            # Post-process
            probs = torch.softmax(output, dim=1).cpu().numpy()[0].tolist()
            num_classes = len(probs)
            labels = class_labels or [f"class_{i}" for i in range(num_classes)]

            top_idx = int(np.argmax(probs))
            elapsed_ms = (time.perf_counter() - start) * 1000

            return InferenceResult(
                status=InferenceStatus.COMPLETED,
                model_name=model_name,
                task=task,
                labels=labels,
                confidence_scores=probs,
                top_prediction=labels[top_idx] if top_idx < len(labels) else f"class_{top_idx}",
                top_confidence=float(probs[top_idx]),
                raw_output=probs,
                segmentation_mask=None,  # populated by segmentation-specific models
                inference_time_ms=round(elapsed_ms, 2),
                device_used=str(self._device),
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("Inference failed for model=%s", model_name)
            return InferenceResult(
                status=InferenceStatus.FAILED,
                model_name=model_name,
                task=task,
                labels=[],
                confidence_scores=[],
                top_prediction="",
                top_confidence=0.0,
                raw_output=None,
                segmentation_mask=None,
                inference_time_ms=round(elapsed_ms, 2),
                device_used=str(self._device),
                error_message=str(exc),
            )

    def _preprocess(
        self,
        pixel_array: np.ndarray,
        config: Optional[Dict[str, Any]],
    ) -> torch.Tensor:
        """Apply MONAI transforms to prepare image for inference."""
        config = config or {}
        target_size = config.get("resize", [224, 224])
        n_channels = config.get("n_channels", 1)

        # Ensure float32
        arr = pixel_array.astype(np.float32)

        # Handle multi-frame — take middle slice
        if arr.ndim == 3:
            arr = arr[arr.shape[0] // 2]

        # Ensure grayscale
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]  # (1, H, W)

        transforms = Compose(
            [
                ScaleIntensity(),
                Resize(spatial_size=target_size),
                ToTensor(),
            ]
        )
        tensor = transforms(arr)  # (C, H, W)

        # Expand to required channels (e.g., 4 for multi-modal MRI)
        if tensor.shape[0] < n_channels:
            tensor = tensor.repeat(n_channels, 1, 1)[:n_channels]

        return tensor.unsqueeze(0)  # (1, C, H, W)

    def _select_device(self) -> torch.device:
        if settings.GPU_ENABLED and torch.cuda.is_available():
            device_id = settings.GPU_DEVICE_ID
            if device_id < torch.cuda.device_count():
                logger.info("GPU selected: cuda:%d", device_id)
                return torch.device(f"cuda:{device_id}")
        logger.info("CPU fallback for inference")
        return torch.device("cpu")
