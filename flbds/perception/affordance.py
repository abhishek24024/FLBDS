"""Task-conditioned Affordance Segmentation and Mechanical Keep-Out Masks.

Extracts:
1. M_Eng: binary modifiable functional part mask in {0, 1}^{H x W}
2. 1 - M_Eng: strictly locked mechanical keep-out mask protecting datums, bolt circles, flanges
Guarantees bit-level mutual exclusion between M_Eng and keep-out interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from flbds.perception.vlm import GroundedBox


@dataclass
class AffordanceMasks:
    m_eng: np.ndarray        # uint8 array of shape (H, W), values in {0, 1}
    keep_out: np.ndarray     # uint8 array of shape (H, W), values in {0, 1}
    height: int
    width: int
    modifiable_ratio: float

    def verify_disjoint(self) -> bool:
        """Verify that M_Eng and Keep-Out masks are strictly mutually exclusive."""
        overlap = np.logical_and(self.m_eng > 0, self.keep_out > 0)
        return not np.any(overlap)


class AffordanceSegmenter:
    """Generates functional modifiable and locked keep-out masks for Image_Eng."""

    def segment_masks(
        self, image: Image.Image | str | Path, boxes: list[GroundedBox] | None = None
    ) -> AffordanceMasks:
        """Produce watertight modifiable and keep-out masks."""
        if isinstance(image, (str, Path)):
            img = Image.open(image).convert("RGB")
        else:
            img = image.convert("RGB")
        w, h = img.size

        m_eng = np.zeros((h, w), dtype=np.uint8)
        keep_out = np.zeros((h, w), dtype=np.uint8)

        if boxes:
            for b in boxes:
                y1, x1, y2, x2 = b.bbox
                if "modifiable" in b.label.lower():
                    m_eng[y1:y2, x1:x2] = 1
                elif "keepout" in b.label.lower() or "datum" in b.label.lower():
                    keep_out[y1:y2, x1:x2] = 1
        else:
            # Default affordance partition: central 60% modifiable, perimeter locked
            pad_y = int(h * 0.15)
            pad_x = int(w * 0.15)
            m_eng[pad_y : h - pad_y, pad_x : w - pad_x] = 1
            keep_out[0:pad_y, :] = 1
            keep_out[h - pad_y : h, :] = 1
            keep_out[:, 0:pad_x] = 1
            keep_out[:, w - pad_x : w] = 1

        # Enforce strict disjointness: keep-out takes absolute priority
        m_eng[keep_out == 1] = 0

        # Any unassigned pixel goes to keep-out to protect interfaces
        keep_out[m_eng == 0] = 1

        mod_ratio = float(np.sum(m_eng) / (h * w))
        return AffordanceMasks(
            m_eng=m_eng,
            keep_out=keep_out,
            height=h,
            width=w,
            modifiable_ratio=mod_ratio,
        )
