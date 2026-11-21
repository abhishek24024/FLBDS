"""flbds/v10/gen.py -- backend-neutral generation parameters and output mimics (vLLM-like)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenParams:
    temperature: float = 0.7
    top_p: float = 0.9
    seed: int = 0
    max_tokens: int = 350
    json_schema: dict[str, Any] | None = (
        None  # ignored by the HF backend (no constrained decoding)
    )
    choice: list[str] | None = None  # ignored by the HF backend


@dataclass
class Completion:
    text: str
    token_ids: list[int] = field(default_factory=list)


@dataclass
class RequestOutput:
    outputs: list[Completion]


def derive_seed(key: tuple[int, ...]) -> int:
    """Deterministic 31-bit seed from an integer tuple (FNV-style, platform independent)."""
    s = 1469598103934665603
    for k in key:
        s = ((s ^ (int(k) + 0x9E3779B9)) * 1099511628211) % (2**61 - 1)
    return int(s % (2**31 - 1))
