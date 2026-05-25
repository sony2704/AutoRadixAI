"""
Agent 4: MODEL-DATA MATCHER AGENT
Routes images to the correct AI pipeline based on modality,
body part, and study description using a dynamic registry.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MatchConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class ModelEntry:
    """Registry entry for an AI model pipeline."""

    name: str
    version: str
    task: str
    modalities: List[str]
    body_parts: List[str]
    description_keywords: List[str]
    model_path: Optional[str]
    preprocessing_config: Dict[str, Any]
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    model: Optional[ModelEntry]
    confidence: MatchConfidence
    score: float
    reasoning: str
    alternatives: List[Tuple[ModelEntry, float]]


class ModelMatcherAgent:
    """
    Dynamic model routing engine.
    Matches incoming DICOM studies to registered AI model pipelines.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, ModelEntry] = {}
        self._load_default_registry()

    # ------------------------------------------------------------------
    # Registry management
    # ------------------------------------------------------------------

    def register_model(self, entry: ModelEntry) -> None:
        if entry.name in self._registry:
            logger.warning("Overwriting existing model registry entry: %s", entry.name)
        self._registry[entry.name] = entry
        logger.info("Registered model: %s v%s → task=%s", entry.name, entry.version, entry.task)

    def deregister_model(self, name: str) -> bool:
        if name in self._registry:
            del self._registry[name]
            logger.info("Deregistered model: %s", name)
            return True
        return False

    def list_models(self) -> List[ModelEntry]:
        return [m for m in self._registry.values() if m.enabled]

    def get_model(self, name: str) -> Optional[ModelEntry]:
        return self._registry.get(name)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    async def match(
        self,
        modality: str,
        body_part: Optional[str] = None,
        study_description: Optional[str] = None,
        series_description: Optional[str] = None,
    ) -> MatchResult:
        """
        Find the best model for a given study.
        Returns best match with confidence and alternatives.
        """
        candidates: List[Tuple[ModelEntry, float]] = []

        search_text = " ".join(
            filter(None, [body_part, study_description, series_description])
        ).upper()

        for model in self._registry.values():
            if not model.enabled:
                continue
            score = self._score_model(model, modality, search_text)
            if score > 0:
                candidates.append((model, score))

        if not candidates:
            logger.info(
                "No model match for modality=%s body_part=%s", modality, body_part
            )
            return MatchResult(
                model=None,
                confidence=MatchConfidence.NONE,
                score=0.0,
                reasoning=f"No registered model for modality={modality}, body_part={body_part}",
                alternatives=[],
            )

        candidates.sort(key=lambda x: (-x[1], -x[0].priority))
        best_model, best_score = candidates[0]
        alternatives = candidates[1:5]

        confidence = self._score_to_confidence(best_score)
        reasoning = self._build_reasoning(best_model, modality, body_part, best_score)

        logger.info(
            "Matched study to model=%s (score=%.2f, confidence=%s)",
            best_model.name,
            best_score,
            confidence,
        )
        return MatchResult(
            model=best_model,
            confidence=confidence,
            score=best_score,
            reasoning=reasoning,
            alternatives=alternatives,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _score_model(
        self, model: ModelEntry, modality: str, search_text: str
    ) -> float:
        score = 0.0

        # Modality match (most important)
        if modality.upper() in [m.upper() for m in model.modalities]:
            score += 5.0
        elif "ALL" in [m.upper() for m in model.modalities]:
            score += 2.0
        else:
            return 0.0  # Modality must match

        # Body part match
        for bp in model.body_parts:
            if bp.upper() in search_text:
                score += 3.0
                break

        # Keyword match
        keyword_hits = sum(
            1 for kw in model.description_keywords if kw.upper() in search_text
        )
        score += keyword_hits * 1.5

        # Priority boost
        score += model.priority * 0.1

        return score

    @staticmethod
    def _score_to_confidence(score: float) -> MatchConfidence:
        if score >= 8.0:
            return MatchConfidence.HIGH
        elif score >= 5.0:
            return MatchConfidence.MEDIUM
        elif score > 0:
            return MatchConfidence.LOW
        return MatchConfidence.NONE

    @staticmethod
    def _build_reasoning(
        model: ModelEntry, modality: str, body_part: Optional[str], score: float
    ) -> str:
        return (
            f"Matched '{model.name}' (task={model.task}) for "
            f"modality={modality}, body_part={body_part}, score={score:.1f}"
        )

    def _load_default_registry(self) -> None:
        """Pre-populate with well-known model pipeline definitions."""
        defaults = [
            ModelEntry(
                name="brain_tumor_segmentation",
                version="1.0",
                task="tumor_segmentation",
                modalities=["MR"],
                body_parts=["BRAIN", "HEAD"],
                description_keywords=["tumor", "glioma", "neoplasm", "mass", "brain", "mri"],
                model_path=None,
                preprocessing_config={
                    "resize": [240, 240],
                    "normalize": True,
                    "window": None,
                    "n_channels": 4,
                },
                priority=10,
            ),
            ModelEntry(
                name="chest_xray_pneumonia",
                version="1.0",
                task="pneumonia_detection",
                modalities=["CR", "DX"],
                body_parts=["CHEST", "LUNG"],
                description_keywords=["chest", "pneumonia", "infiltrate", "consolidation"],
                model_path=None,
                preprocessing_config={
                    "resize": [224, 224],
                    "normalize": True,
                    "window": {"center": 40, "width": 400},
                    "n_channels": 1,
                },
                priority=10,
            ),
            ModelEntry(
                name="ct_lung_nodule_detection",
                version="1.0",
                task="nodule_detection",
                modalities=["CT"],
                body_parts=["CHEST", "LUNG"],
                description_keywords=["lung", "nodule", "pulmonary", "thorax"],
                model_path=None,
                preprocessing_config={
                    "resize": [512, 512],
                    "normalize": True,
                    "window": {"center": -600, "width": 1500},
                    "n_channels": 1,
                },
                priority=10,
            ),
            ModelEntry(
                name="ct_liver_segmentation",
                version="1.0",
                task="liver_segmentation",
                modalities=["CT"],
                body_parts=["ABDOMEN", "LIVER"],
                description_keywords=["liver", "hepatic", "abdomen"],
                model_path=None,
                preprocessing_config={
                    "resize": [256, 256],
                    "normalize": True,
                    "window": {"center": 60, "width": 400},
                    "n_channels": 1,
                },
                priority=8,
            ),
            ModelEntry(
                name="generic_classification",
                version="1.0",
                task="general_classification",
                modalities=["ALL"],
                body_parts=[],
                description_keywords=[],
                model_path=None,
                preprocessing_config={
                    "resize": [224, 224],
                    "normalize": True,
                    "window": None,
                    "n_channels": 1,
                },
                priority=0,
            ),
        ]
        for entry in defaults:
            self._registry[entry.name] = entry
