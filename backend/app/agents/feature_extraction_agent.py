"""
Agent 3: FEATURE EXTRACTION AGENT
Extracts radiomic features, embeddings, texture, shape,
histogram, and spatial metadata from DICOM/image data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import pydicom
from pydicom.errors import InvalidDicomError
from skimage import exposure, feature, measure

logger = logging.getLogger(__name__)


@dataclass
class RadiomicFeatures:
    """Extracted radiomic feature vector."""

    # First-order statistics
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    median: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    energy: float = 0.0
    entropy: float = 0.0
    rms: float = 0.0
    uniformity: float = 0.0
    percentile_10: float = 0.0
    percentile_90: float = 0.0

    # Histogram
    histogram_bins: List[float] = field(default_factory=list)
    histogram_counts: List[int] = field(default_factory=list)

    # Texture (GLCM — Gray Level Co-occurrence Matrix)
    glcm_contrast: float = 0.0
    glcm_dissimilarity: float = 0.0
    glcm_homogeneity: float = 0.0
    glcm_energy: float = 0.0
    glcm_correlation: float = 0.0

    # Shape
    area: float = 0.0
    perimeter: float = 0.0
    eccentricity: float = 0.0
    extent: float = 0.0
    solidity: float = 0.0

    # Spatial metadata
    pixel_spacing: Optional[List[float]] = None
    slice_thickness: Optional[float] = None
    orientation: Optional[List[float]] = None

    # Image properties
    rows: int = 0
    columns: int = 0
    num_frames: int = 1
    bits_allocated: Optional[int] = None

    # LBP (Local Binary Pattern) texture
    lbp_histogram: List[float] = field(default_factory=list)

    # Embedding placeholder (filled by DL model)
    embedding: Optional[List[float]] = None


class FeatureExtractionAgent:
    """
    Extracts multi-dimensional radiomic and handcrafted features
    from DICOM pixel data.
    """

    N_HISTOGRAM_BINS = 64
    LBP_RADIUS = 3
    LBP_N_POINTS = 24
    GLCM_DISTANCES = [1, 2]
    GLCM_ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]

    def __init__(self) -> None:
        self._name = "FeatureExtractionAgent"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_from_dicom(self, dicom_path: Path) -> RadiomicFeatures:
        """Load DICOM, extract pixel array, and compute features."""
        dicom_path = Path(dicom_path)
        try:
            ds = pydicom.dcmread(str(dicom_path), force=True)
            pixel_array = ds.pixel_array.astype(np.float32)
        except (InvalidDicomError, AttributeError) as exc:
            logger.error("Cannot read pixel data from %s: %s", dicom_path.name, exc)
            raise

        # Apply windowing/rescale if present
        pixel_array = self._apply_rescale(ds, pixel_array)

        # Spatial metadata
        pixel_spacing = None
        try:
            pixel_spacing = [float(v) for v in ds.PixelSpacing]
        except AttributeError:
            pass

        slice_thickness = None
        try:
            slice_thickness = float(ds.SliceThickness)
        except AttributeError:
            pass

        orientation: Optional[List[float]] = None
        try:
            orientation = [float(v) for v in ds.ImageOrientationPatient]
        except AttributeError:
            pass

        # Work on 2D slice (first frame for multi-frame)
        if pixel_array.ndim == 3:
            frame = pixel_array[0]
        else:
            frame = pixel_array

        features = self._compute_features(frame)
        features.pixel_spacing = pixel_spacing
        features.slice_thickness = slice_thickness
        features.orientation = orientation
        features.rows = int(getattr(ds, "Rows", frame.shape[0]))
        features.columns = int(getattr(ds, "Columns", frame.shape[1]))
        features.num_frames = int(getattr(ds, "NumberOfFrames", 1) or 1)
        features.bits_allocated = getattr(ds, "BitsAllocated", None)
        return features

    async def extract_from_numpy(self, pixel_array: np.ndarray) -> RadiomicFeatures:
        """Extract features from a raw numpy array."""
        frame = pixel_array.astype(np.float32)
        if frame.ndim == 3:
            frame = frame[0]
        return self._compute_features(frame)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_features(self, frame: np.ndarray) -> RadiomicFeatures:
        features = RadiomicFeatures()

        # ---- First-order statistics ----
        flat = frame.flatten()
        features.mean = float(np.mean(flat))
        features.std = float(np.std(flat))
        features.min_val = float(np.min(flat))
        features.max_val = float(np.max(flat))
        features.median = float(np.median(flat))
        features.energy = float(np.sum(flat ** 2))
        features.rms = float(np.sqrt(np.mean(flat ** 2)))
        features.percentile_10 = float(np.percentile(flat, 10))
        features.percentile_90 = float(np.percentile(flat, 90))

        from scipy.stats import skew, kurtosis
        features.skewness = float(skew(flat))
        features.kurtosis = float(kurtosis(flat))

        # Entropy
        hist, _ = np.histogram(flat, bins=self.N_HISTOGRAM_BINS, density=True)
        hist = hist[hist > 0]
        features.entropy = float(-np.sum(hist * np.log2(hist)))
        features.uniformity = float(np.sum(hist ** 2))

        # ---- Histogram ----
        counts, bin_edges = np.histogram(flat, bins=self.N_HISTOGRAM_BINS)
        features.histogram_bins = bin_edges[:-1].tolist()
        features.histogram_counts = counts.tolist()

        # ---- Texture: GLCM ----
        try:
            frame_uint8 = self._normalize_to_uint8(frame)
            glcm = feature.graycomatrix(
                frame_uint8,
                distances=self.GLCM_DISTANCES,
                angles=self.GLCM_ANGLES,
                levels=256,
                symmetric=True,
                normed=True,
            )
            features.glcm_contrast = float(np.mean(feature.graycoprops(glcm, "contrast")))
            features.glcm_dissimilarity = float(np.mean(feature.graycoprops(glcm, "dissimilarity")))
            features.glcm_homogeneity = float(np.mean(feature.graycoprops(glcm, "homogeneity")))
            features.glcm_energy = float(np.mean(feature.graycoprops(glcm, "energy")))
            features.glcm_correlation = float(np.mean(feature.graycoprops(glcm, "correlation")))
        except Exception as exc:
            logger.debug("GLCM computation skipped: %s", exc)

        # ---- LBP texture ----
        try:
            frame_uint8 = self._normalize_to_uint8(frame)
            lbp = feature.local_binary_pattern(
                frame_uint8, self.LBP_N_POINTS, self.LBP_RADIUS, method="uniform"
            )
            lbp_hist, _ = np.histogram(
                lbp.ravel(), bins=self.LBP_N_POINTS + 2, range=(0, self.LBP_N_POINTS + 2)
            )
            lbp_hist = lbp_hist.astype(float)
            lbp_hist /= lbp_hist.sum() + 1e-8
            features.lbp_histogram = lbp_hist.tolist()
        except Exception as exc:
            logger.debug("LBP computation skipped: %s", exc)

        # ---- Shape features (largest connected component) ----
        try:
            binary = frame > np.mean(frame)
            labeled = measure.label(binary)
            regions = measure.regionprops(labeled)
            if regions:
                largest = max(regions, key=lambda r: r.area)
                features.area = float(largest.area)
                features.perimeter = float(largest.perimeter)
                features.eccentricity = float(largest.eccentricity)
                features.extent = float(largest.extent)
                features.solidity = float(largest.solidity)
        except Exception as exc:
            logger.debug("Shape feature extraction skipped: %s", exc)

        return features

    @staticmethod
    def _normalize_to_uint8(frame: np.ndarray) -> np.ndarray:
        mn, mx = frame.min(), frame.max()
        if mx - mn < 1e-6:
            return np.zeros(frame.shape, dtype=np.uint8)
        normalized = (frame - mn) / (mx - mn) * 255
        return normalized.astype(np.uint8)

    @staticmethod
    def _apply_rescale(ds: pydicom.Dataset, pixel_array: np.ndarray) -> np.ndarray:
        """Apply RescaleSlope and RescaleIntercept if available."""
        slope = getattr(ds, "RescaleSlope", 1.0)
        intercept = getattr(ds, "RescaleIntercept", 0.0)
        try:
            return pixel_array * float(slope) + float(intercept)
        except Exception:
            return pixel_array
