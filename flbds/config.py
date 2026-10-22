"""Typed configuration.

Precedence: explicit argument > ``FLBDS_*`` environment variable > YAML file >
defaults. Paths are resolved relative to the repository root so the package can
be run from anywhere.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent


class Paths(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: Path = ROOT
    data: Path = ROOT / "data"
    seeds: Path = ROOT / "flbds" / "data" / "seeds"
    graph_db: Path = ROOT / "data" / "flbds.sqlite3"
    runs: Path = ROOT / "runs"
    cache: Path = ROOT / ".cache" / "flbds"

    def ensure(self) -> "Paths":
        for p in (self.data, self.runs, self.cache, self.graph_db.parent):
            p.mkdir(parents=True, exist_ok=True)
        return self


class GraphRAGConfig(BaseModel):
    """Weights of the hybrid retrieval objective J_GraphRAG."""

    model_config = ConfigDict(extra="forbid")

    alpha_txt: float = Field(0.65, ge=0.0, le=1.0, description="text vs. image embedding weight")
    top_k: int = 20
    beam_width: int = 12
    max_depth: int = 4
    w_vec: float = 0.45
    w_causal: float = 0.30
    w_community: float = 0.15
    w_phylo: float = 0.10


class ExtractionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strict_abductive: bool = True
    require_evidence: bool = True
    groundedness_threshold: float = Field(0.76, ge=0.0, le=1.0)
    max_followups: int = 3
    top_k_chunks: int = 8
    min_confidence: float = 0.0


class ScaleConfig(BaseModel):
    """Critical regimes for the Buckingham Pi audit (Stage 4)."""

    model_config = ConfigDict(extra="forbid")

    length_scale_min: float = 0.01
    length_scale_max: float = 1000.0
    error_on_violation: bool = False


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["openai_compatible", "ollama", "none"] = "openai_compatible"
    base_url: str = "http://127.0.0.1:8000/v1"
    model: str = "Qwen/Qwen2.5-72B-Instruct"
    api_key_env: str = "FLBDS_LLM_API_KEY"
    temperature: float = 0.0
    max_tokens: int = 2048
    timeout_s: float = 120.0


class VisionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vlm_model: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    sam_checkpoint: str | None = None
    device: str = "cuda"
    max_pixels: int = 1280 * 28 * 28


class SynthesisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_backend: Literal["diffusers", "reference"] = "reference"
    svg_backend: Literal["starvector", "geometry"] = "geometry"
    cad_backend: Literal["cadquery", "geometry"] = "geometry"
    guidance_scale: float = 30.0
    steps: int = 30


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paths: Paths = Field(default_factory=Paths)
    graphrag: GraphRAGConfig = Field(default_factory=GraphRAGConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    scale: ScaleConfig = Field(default_factory=ScaleConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    synthesis: SynthesisConfig = Field(default_factory=SynthesisConfig)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        payload: dict[str, Any] = {}
        cfg_path = Path(path) if path else ROOT / "configs" / "default.yaml"
        if cfg_path.exists():
            payload = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        payload = _apply_env(payload)
        return cls.model_validate(payload)


def _apply_env(payload: dict[str, Any]) -> dict[str, Any]:
    """``FLBDS_GRAPH_DB``, ``FLBDS_LLM_MODEL``, ... -> nested dict overrides."""

    flat = {
        "FLBDS_GRAPH_DB": ("paths", "graph_db"),
        "FLBDS_DATA_DIR": ("paths", "data"),
        "FLBDS_RUNS_DIR": ("paths", "runs"),
        "FLBDS_LLM_BASE_URL": ("llm", "base_url"),
        "FLBDS_LLM_MODEL": ("llm", "model"),
        "FLBDS_VLM_MODEL": ("vision", "vlm_model"),
        "FLBDS_SAM_CHECKPOINT": ("vision", "sam_checkpoint"),
        "FLBDS_DEVICE": ("vision", "device"),
        "FLBDS_IMAGE_BACKEND": ("synthesis", "image_backend"),
    }
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in payload.items()}
    for env, (section, key) in flat.items():
        if (val := os.environ.get(env)) is not None:
            out.setdefault(section, {})
            out[section][key] = val
    return out


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.load().ensure_dirs()


def _ensure(self: Settings) -> Settings:
    self.paths.ensure()
    return self


Settings.ensure_dirs = _ensure  # type: ignore[attr-defined]
