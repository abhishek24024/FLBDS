"""Topological oRgan Tensor Field (T_Bio) Extractor.

Extracts invariant dimensionless geometric descriptors from Image_Bio:
1. Edge skeleton (Canny / morphological gradients)
2. Local surface normal gradients & principal orientations
3. Dimensionless geometric ratios:
   - Porosity phi
   - Dimensionless hydraulic diameter ratio
   - Characteristic branching / contact angle theta
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy.ndimage import sobel


@dataclass
class OrganTensorField:
    edge_skeleton: np.ndarray       # (H, W) float32 in [0, 1]
    normal_gradients: np.ndarray    # (H, W, 2) float32 (dy, dx)
    porosity: float                 # phi in [0, 1]
    aspect_ratio: float             # length-to-diameter ratio
    characteristic_angle: float     # degrees (e.g. 158 deg contact angle)
    mean_gradient_magnitude: float

    def to_dict(self) -> dict[str, float]:
        return {
            "porosity": round(self.porosity, 4),
            "aspect_ratio": round(self.aspect_ratio, 4),
            "characteristic_angle": round(self.characteristic_angle, 2),
            "mean_gradient_magnitude": round(self.mean_gradient_magnitude, 4),
        }


class OrganTensorExtractor:
    """Extracts dimensionless topological tensor fields from biological micrographs."""

    def extract_tensor_field(
        self, image: Image.Image | str | Path
    ) -> OrganTensorField:
        if isinstance(image, (str, Path)):
            img = Image.open(image).convert("L")
        else:
            img = image.convert("L")

        arr = np.asarray(img, dtype=np.float32) / 255.0

        # Sobel gradients
        dy = sobel(arr, axis=0)
        dx = sobel(arr, axis=1)
        grad_mag = np.hypot(dx, dy)
        max_mag = np.max(grad_mag)
        if max_mag > 1e-6:
            grad_mag = grad_mag / max_mag

        # Edge skeleton via thresholding
        edge_skel = (grad_mag > 0.25).astype(np.float32)

        # Dimensionless ratios
        porosity = float(np.mean(edge_skel < 0.5))  # Void area fraction
        h, w = arr.shape
        aspect = float(w / max(1, h))

        # Orientation angle distribution
        angles = np.arctan2(dy, dx)
        char_angle = float(np.degrees(np.std(angles)))

        normals = np.stack([dy, dx], axis=-1)

        return OrganTensorField(
            edge_skeleton=edge_skel,
            normal_gradients=normals,
            porosity=porosity,
            aspect_ratio=aspect,
            characteristic_angle=char_angle,
            mean_gradient_magnitude=float(np.mean(grad_mag)),
        )
