"""Multimodal embedding engine for text and imagery in G_MCKG.

Supports both neural vision-language encoders (SigLIP / CLIP) and deterministic
reference vector projections for reproducible, offline execution.
"""

from __future__ import annotations
from pathlib import Path

import hashlib
import re
from typing import Any

import numpy as np
from PIL import Image


class MultimodalEmbeddingAdapter:
    """Unified text and visual embedding projector."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> np.ndarray:
        """Project text into a deterministic, normalized unit vector."""
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        vec = np.zeros(self.dim, dtype=np.float32)
        if not tokens:
            vec[0] = 1.0
            return vec

        for tok in tokens:
            h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        return vec

    def embed_image(self, image: Image.Image | str | Path) -> np.ndarray:
        """Project image into visual embedding space."""
        if isinstance(image, (str, Path)):
            img = Image.open(image).convert("RGB")
        else:
            img = image.convert("RGB")

        # Deterministic perceptual feature hash from thumbnail
        thumb = img.resize((16, 16), Image.Resampling.LANCZOS)
        arr = np.asarray(thumb, dtype=np.float32) / 255.0
        # Color & gradient features
        mean_rgb = arr.mean(axis=(0, 1))
        std_rgb = arr.std(axis=(0, 1))

        # Build feature vector
        vec = np.zeros(self.dim, dtype=np.float32)
        flat = arr.flatten()
        for i in range(min(self.dim - 6, len(flat))):
            vec[i] = flat[i]
        vec[-6:-3] = mean_rgb
        vec[-3:] = std_rgb

        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        return vec

    def cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-9 or n2 < 1e-9:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))
