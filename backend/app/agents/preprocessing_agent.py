"""
Agent 5: PREPROCESSING RECOMMENDATION AGENT
Auto-recommends preprocessing pipeline configuration
based on modality, body part, and image statistics.
Outputs a preprocessing configuration JSON.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WindowConfig:
    center: float
    width: float


@dataclass
class ResizeConfig:
    height: int
    width: int
    interpolation: str = "bilinear"


@dataclass
class DenoiseConfig:
    method: str  # "gaussian" | "bilateral" | "nlm" | "none"
    sigma: float = 1.0
    strength: float = 0.1


@dataclass
class NormalizationConfig:
    method: str  # "minmax" | "zscore" | "percentile" | "none"
    clip_min: Optional[float] = None
    clip_max: Optional[float] = None


@dataclass
class SegmentationConfig:
    strategy: str  # "threshold" | "watershed" | "deeplab" | "unet" | "none"
    threshold_method: str = "otsu"


@dataclass
class PreprocessingConfig:
    """Complete preprocessing recommendation for a study."""

    modality: str
    body_part: Optional[str]
    task: Optional[str]
    resize: ResizeConfig
    window: Optional[WindowConfig]
    normalize: NormalizationConfig
    denoise: DenoiseConfig
    segmentation: SegmentationConfig
    flip_horizontal: bool = False
    flip_vertical: bool = False
    rotate_degrees: float = 0.0
    convert_to_hu: bool = False
    clip_hu_range: Optional[Tuple[float, float]] = None
    augmentation_enabled: bool = False
    augmentation_strategy: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------------
# Modality-specific windowing presets (Hounsfield Units for CT)
# ------------------------------------------------------------------
HU_WINDOWS: Dict[str, WindowConfig] = {
    "brain": WindowConfig(center=40, width=80),
    "subdural": WindowConfig(center=75, width=215),
    "stroke": WindowConfig(center=32, width=8),
    "temporal_bones": WindowConfig(center=600, width=2800),
    "soft_tissue": WindowConfig(center=50, width=400),
    "lung": WindowConfig(center=-600, width=1500),
    "bone": WindowConfig(center=400, width=1800),
    "liver": WindowConfig(center=60, width=160),
    "spine": WindowConfig(center=30, width=300),
    "default_ct": WindowConfig(center=40, width=400),
}


class PreprocessingRecommendationAgent:
    """
    Recommends optimal preprocessing configuration for medical images
    based on modality, body part, clinical task, and image statistics.
    """

    def __init__(self) -> None:
        self._name = "PreprocessingRecommendationAgent"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def recommend(
        self,
        modality: str,
        body_part: Optional[str] = None,
        task: Optional[str] = None,
        image_stats: Optional[Dict[str, Any]] = None,
    ) -> PreprocessingConfig:
        """Generate a preprocessing configuration recommendation."""
        modality = modality.upper()
        body_part_upper = (body_part or "").upper()

        notes: List[str] = []

        # ---- Windowing ----
        window = self._recommend_window(modality, body_part_upper, notes)

        # ---- Resize ----
        resize = self._recommend_resize(modality, task)

        # ---- Normalization ----
        normalize = self._recommend_normalization(modality, window)

        # ---- Denoising ----
        denoise = self._recommend_denoising(modality, body_part_upper, image_stats, notes)

        # ---- Segmentation strategy ----
        segmentation = self._recommend_segmentation(modality, task, body_part_upper)

        # ---- HU conversion ----
        convert_to_hu = modality == "CT"
        clip_hu_range = self._recommend_hu_range(modality, body_part_upper)

        config = PreprocessingConfig(
            modality=modality,
            body_part=body_part,
            task=task,
            resize=resize,
            window=window,
            normalize=normalize,
            denoise=denoise,
            segmentation=segmentation,
            convert_to_hu=convert_to_hu,
            clip_hu_range=clip_hu_range,
            notes=notes,
        )
        logger.info(
            "Preprocessing recommendation: modality=%s body_part=%s task=%s",
            modality,
            body_part,
            task,
        )
        return config

    # ------------------------------------------------------------------
    # Private recommendation logic
    # ------------------------------------------------------------------

    def _recommend_window(
        self, modality: str, body_part: str, notes: List[str]
    ) -> Optional[WindowConfig]:
        if modality != "CT":
            return None

        if "BRAIN" in body_part or "HEAD" in body_part:
            notes.append("CT brain window applied (C=40, W=80)")
            return HU_WINDOWS["brain"]
        if "LUNG" in body_part or "CHEST" in body_part or "THORAX" in body_part:
            notes.append("CT lung window applied (C=-600, W=1500)")
            return HU_WINDOWS["lung"]
        if "BONE" in body_part or "SPINE" in body_part:
            notes.append("CT bone window applied (C=400, W=1800)")
            return HU_WINDOWS["bone"]
        if "LIVER" in body_part or "ABDOMEN" in body_part:
            notes.append("CT soft tissue / liver window applied")
            return HU_WINDOWS["liver"]

        notes.append("Default CT window applied")
        return HU_WINDOWS["default_ct"]

    def _recommend_resize(self, modality: str, task: Optional[str]) -> ResizeConfig:
        task = (task or "").lower()
        if "segmentation" in task:
            return ResizeConfig(height=256, width=256)
        if modality in ("CR", "DX"):
            return ResizeConfig(height=224, width=224)
        if modality == "MR":
            return ResizeConfig(height=240, width=240)
        if modality == "CT":
            return ResizeConfig(height=512, width=512)
        return ResizeConfig(height=224, width=224)

    @staticmethod
    def _recommend_normalization(
        modality: str, window: Optional[WindowConfig]
    ) -> NormalizationConfig:
        if modality == "CT":
            if window:
                lo = window.center - window.width / 2
                hi = window.center + window.width / 2
                return NormalizationConfig(method="minmax", clip_min=lo, clip_max=hi)
            return NormalizationConfig(method="percentile", clip_min=0.5, clip_max=99.5)
        if modality == "MR":
            return NormalizationConfig(method="zscore")
        return NormalizationConfig(method="minmax")

    @staticmethod
    def _recommend_denoising(
        modality: str,
        body_part: str,
        image_stats: Optional[Dict[str, Any]],
        notes: List[str],
    ) -> DenoiseConfig:
        # Use noise estimate if available
        if image_stats:
            noise_level = image_stats.get("std", 0.0)
            if noise_level > 200:
                notes.append(f"High noise detected (std={noise_level:.1f}); bilateral filter recommended.")
                return DenoiseConfig(method="bilateral", sigma=2.0, strength=0.15)

        if modality == "US":
            notes.append("Ultrasound speckle reduction recommended")
            return DenoiseConfig(method="nlm", sigma=1.5, strength=0.1)
        if modality in ("CR", "DX"):
            return DenoiseConfig(method="gaussian", sigma=0.5)
        return DenoiseConfig(method="none")

    @staticmethod
    def _recommend_segmentation(
        modality: str, task: Optional[str], body_part: str
    ) -> SegmentationConfig:
        task_l = (task or "").lower()
        if "segmentation" in task_l:
            if modality in ("MR", "CT"):
                return SegmentationConfig(strategy="unet")
            return SegmentationConfig(strategy="threshold", threshold_method="otsu")
        if modality == "CT" and ("LUNG" in body_part or "CHEST" in body_part):
            return SegmentationConfig(strategy="threshold", threshold_method="otsu")
        return SegmentationConfig(strategy="none")

    @staticmethod
    def _recommend_hu_range(
        modality: str, body_part: str
    ) -> Optional[Tuple[float, float]]:
        if modality != "CT":
            return None
        if "BRAIN" in body_part:
            return (-1000, 1000)
        if "LUNG" in body_part or "CHEST" in body_part:
            return (-1500, 500)
        if "BONE" in body_part:
            return (-200, 2000)
        return (-1000, 3000)
