"""
Agent 7: EXPLAINABILITY AGENT
Generates GradCAM heatmaps, saliency maps, and attention overlays
to explain AI predictions on medical images.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ExplainabilityResult:
    method: str
    heatmap_array: np.ndarray          # Raw float heatmap [0, 1]
    overlay_array: np.ndarray          # Heatmap blended onto original image
    heatmap_path: Optional[str]
    overlay_path: Optional[str]
    clinical_explanation: str
    top_prediction: str
    confidence: float
    metadata: Dict[str, Any]


class GradCAMExtractor:
    """
    Gradient-weighted Class Activation Mapping.
    Hooks into the last convolutional layer to extract spatial attention.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self._model = model
        self._target_layer = target_layer
        self._gradients: Optional[torch.Tensor] = None
        self._activations: Optional[torch.Tensor] = None
        self._hooks: list = []
        self._register_hooks()

    def _register_hooks(self) -> None:
        def save_grad(grad: torch.Tensor) -> None:
            self._gradients = grad

        def save_activation(
            module: nn.Module, input: Any, output: torch.Tensor
        ) -> None:
            self._activations = output
            output.register_hook(save_grad)

        handle = self._target_layer.register_forward_hook(save_activation)
        self._hooks.append(handle)

    def remove_hooks(self) -> None:
        for h in self._hooks:
            h.remove()

    def generate(
        self, input_tensor: torch.Tensor, class_idx: Optional[int] = None
    ) -> np.ndarray:
        """Compute GradCAM heatmap for a given input and class."""
        self._model.eval()
        output = self._model(input_tensor)

        if class_idx is None:
            class_idx = int(torch.argmax(output, dim=1).item())

        self._model.zero_grad()
        one_hot = torch.zeros_like(output)
        one_hot[0][class_idx] = 1.0
        output.backward(gradient=one_hot, retain_graph=True)

        gradients = self._gradients  # (1, C, H, W)
        activations = self._activations  # (1, C, H, W)

        if gradients is None or activations is None:
            return np.zeros((224, 224), dtype=np.float32)

        # Pool gradients across spatial dimensions
        weights = gradients.mean(dim=[2, 3], keepdim=True)  # (1, C, 1, 1)
        cam = (weights * activations).sum(dim=1, keepdim=True)  # (1, 1, H, W)
        cam = F.relu(cam)
        cam = cam.squeeze().detach().cpu().numpy()

        # Normalize to [0, 1]
        if cam.max() > cam.min():
            cam = (cam - cam.min()) / (cam.max() - cam.min())
        return cam.astype(np.float32)


class ExplainabilityAgent:
    """
    Generates visual explanations (GradCAM, saliency maps, attention overlays)
    for AI predictions on medical images.
    """

    COLORMAP = cv2.COLORMAP_JET

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def explain_gradcam(
        self,
        model: nn.Module,
        input_tensor: torch.Tensor,
        original_image: np.ndarray,
        class_idx: Optional[int],
        prediction_label: str,
        confidence: float,
        output_filename: str,
    ) -> ExplainabilityResult:
        """Generate GradCAM explanation."""
        # Find last conv layer
        target_layer = self._find_last_conv(model)
        if target_layer is None:
            return self._fallback_result(prediction_label, confidence)

        extractor = GradCAMExtractor(model, target_layer)
        try:
            cam = extractor.generate(input_tensor, class_idx)
        finally:
            extractor.remove_hooks()

        heatmap_uint8, overlay = self._create_overlay(cam, original_image)

        heatmap_path = str(self.output_dir / f"{output_filename}_gradcam.png")
        overlay_path = str(self.output_dir / f"{output_filename}_overlay.png")

        Image.fromarray(heatmap_uint8).save(heatmap_path)
        Image.fromarray(overlay).save(overlay_path)

        explanation = self._generate_clinical_explanation(
            method="GradCAM", prediction=prediction_label, confidence=confidence
        )

        return ExplainabilityResult(
            method="GradCAM",
            heatmap_array=cam,
            overlay_array=overlay,
            heatmap_path=heatmap_path,
            overlay_path=overlay_path,
            clinical_explanation=explanation,
            top_prediction=prediction_label,
            confidence=confidence,
            metadata={"class_idx": class_idx},
        )

    async def explain_saliency(
        self,
        model: nn.Module,
        input_tensor: torch.Tensor,
        original_image: np.ndarray,
        class_idx: Optional[int],
        prediction_label: str,
        confidence: float,
        output_filename: str,
    ) -> ExplainabilityResult:
        """Generate gradient-based saliency map."""
        model.eval()
        inp = input_tensor.clone().requires_grad_(True)
        output = model(inp)

        if class_idx is None:
            class_idx = int(torch.argmax(output, dim=1).item())

        model.zero_grad()
        output[0][class_idx].backward()

        saliency = inp.grad.data.abs()
        saliency = saliency.squeeze().cpu().numpy()
        if saliency.ndim == 3:
            saliency = saliency.max(axis=0)

        # Normalize
        if saliency.max() > saliency.min():
            saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min())
        saliency = saliency.astype(np.float32)

        heatmap_uint8, overlay = self._create_overlay(saliency, original_image)

        heatmap_path = str(self.output_dir / f"{output_filename}_saliency.png")
        overlay_path = str(self.output_dir / f"{output_filename}_saliency_overlay.png")
        Image.fromarray(heatmap_uint8).save(heatmap_path)
        Image.fromarray(overlay).save(overlay_path)

        explanation = self._generate_clinical_explanation(
            method="Saliency", prediction=prediction_label, confidence=confidence
        )

        return ExplainabilityResult(
            method="Saliency",
            heatmap_array=saliency,
            overlay_array=overlay,
            heatmap_path=heatmap_path,
            overlay_path=overlay_path,
            clinical_explanation=explanation,
            top_prediction=prediction_label,
            confidence=confidence,
            metadata={"class_idx": class_idx},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_overlay(
        self, heatmap: np.ndarray, original: np.ndarray, alpha: float = 0.4
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Resize heatmap to image size and blend."""
        h, w = original.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)

        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, self.COLORMAP)
        heatmap_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

        # Normalize original to uint8
        if original.dtype != np.uint8:
            mn, mx = original.min(), original.max()
            if mx > mn:
                orig_u8 = ((original - mn) / (mx - mn) * 255).astype(np.uint8)
            else:
                orig_u8 = np.zeros_like(original, dtype=np.uint8)
        else:
            orig_u8 = original

        if orig_u8.ndim == 2:
            orig_u8 = cv2.cvtColor(orig_u8, cv2.COLOR_GRAY2RGB)
        if orig_u8.shape[2] == 4:
            orig_u8 = orig_u8[:, :, :3]

        overlay = cv2.addWeighted(orig_u8, 1 - alpha, heatmap_rgb, alpha, 0)
        return heatmap_uint8, overlay

    @staticmethod
    def _find_last_conv(model: nn.Module) -> Optional[nn.Module]:
        """Find the last convolutional layer in the model."""
        last_conv = None
        for module in model.modules():
            if isinstance(module, (nn.Conv2d, nn.Conv3d)):
                last_conv = module
        return last_conv

    @staticmethod
    def _generate_clinical_explanation(
        method: str, prediction: str, confidence: float
    ) -> str:
        pct = confidence * 100
        level = "high" if confidence >= 0.8 else "moderate" if confidence >= 0.5 else "low"
        return (
            f"The AI model predicts '{prediction}' with {pct:.1f}% confidence ({level} confidence). "
            f"The {method} visualization highlights regions that most influenced this prediction. "
            f"Bright/warm regions indicate areas of highest diagnostic relevance. "
            f"This analysis is AI-assisted and should be reviewed by a qualified radiologist."
        )

    @staticmethod
    def _fallback_result(prediction_label: str, confidence: float) -> ExplainabilityResult:
        blank = np.zeros((224, 224), dtype=np.float32)
        return ExplainabilityResult(
            method="none",
            heatmap_array=blank,
            overlay_array=np.zeros((224, 224, 3), dtype=np.uint8),
            heatmap_path=None,
            overlay_path=None,
            clinical_explanation="Explainability not available for this model architecture.",
            top_prediction=prediction_label,
            confidence=confidence,
            metadata={},
        )
