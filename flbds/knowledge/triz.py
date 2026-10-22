"""The TRIZ contradiction matrix, parameters, principles, and separation operators.

Deterministic symbolic reasoning substrate:
- 39 Engineering Parameters (Altshuller)
- 40 Inventive Principles
- 4+ Separation Operators for Physical Contradictions
- 39x39 Contradiction Matrix
- Lexical Parameter Matcher (keyword / n-gram token overlap without LLM drift)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TrizParameter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=39)
    name: str
    description: str
    keywords: list[str] = Field(default_factory=list)


class TrizPrinciple(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=40)
    name: str
    description: str
    sub_principles: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class SeparationOperator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    description: str
    principles: list[int] = Field(default_factory=list)
    strategy: str = ""


class TrizKnowledge:
    """Authoritative provider of TRIZ engineering knowledge."""

    def __init__(self, data_dir: Path | str | None = None) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data" / "triz"
        self.data_dir = Path(data_dir)

        self._parameters: dict[int, TrizParameter] = {}
        self._principles: dict[int, TrizPrinciple] = {}
        self._separations: list[SeparationOperator] = []
        self._matrix: list[list[list[int]]] = []

        self._load()

    def _load(self) -> None:
        params_file = self.data_dir / "parameters.json"
        if params_file.exists():
            raw_params = json.loads(params_file.read_text(encoding="utf-8"))
            for p in raw_params:
                param = TrizParameter(
                    id=p["id"],
                    name=p["name"],
                    description=p.get("description", ""),
                    keywords=p.get("keywords", []),
                )
                self._parameters[param.id] = param

        principles_file = self.data_dir / "principles.json"
        if principles_file.exists():
            raw_principles = json.loads(principles_file.read_text(encoding="utf-8"))
            for p in raw_principles:
                principle = TrizPrinciple(
                    id=p["id"],
                    name=p["name"],
                    description=p.get("description", ""),
                    sub_principles=p.get("sub_principles", p.get("subprinciples", [])),
                    examples=p.get("examples", []),
                )
                self._principles[principle.id] = principle

        matrix_file = self.data_dir / "matrix.json"
        if matrix_file.exists():
            self._matrix = json.loads(matrix_file.read_text(encoding="utf-8"))

        seps_file = self.data_dir / "separations.json"
        if seps_file.exists():
            raw_seps = json.loads(seps_file.read_text(encoding="utf-8"))
            for s in raw_seps:
                self._separations.append(
                    SeparationOperator(
                        id=s["id"],
                        name=s["name"],
                        description=s.get("description", ""),
                        principles=s.get("principles", []),
                        strategy=s.get("strategy", ""),
                    )
                )

    def get_parameter(self, param_id: int) -> TrizParameter:
        if param_id not in self._parameters:
            raise KeyError(f"TRIZ parameter id {param_id} not in range 1..39")
        return self._parameters[param_id]

    def get_principle(self, principle_id: int) -> TrizPrinciple:
        if principle_id not in self._principles:
            raise KeyError(f"TRIZ principle id {principle_id} not in range 1..40")
        return self._principles[principle_id]

    def all_parameters(self) -> list[TrizParameter]:
        return [self._parameters[i] for i in sorted(self._parameters.keys())]

    def all_principles(self) -> list[TrizPrinciple]:
        return [self._principles[i] for i in sorted(self._principles.keys())]

    def separations(self) -> list[SeparationOperator]:
        return list(self._separations)

    def principles_for(self, improving_param: int, worsening_param: int) -> list[int]:
        """Look up inventive principles in the 39x39 contradiction matrix.

        Args:
            improving_param: 1-indexed parameter id (1..39)
            worsening_param: 1-indexed parameter id (1..39)

        Returns:
            List of inventive principle ids (1..40)
        """
        if not (1 <= improving_param <= 39 and 1 <= worsening_param <= 39):
            raise ValueError(
                f"Parameter indices must be 1..39; got improving={improving_param}, worsening={worsening_param}"
            )
        if not self._matrix:
            return []
        # Matrix is 0-indexed: [improving - 1][worsening - 1]
        return list(self._matrix[improving_param - 1][worsening_param - 1])

    def match_parameter(self, text: str, top_k: int = 3) -> list[tuple[TrizParameter, float]]:
        """Deterministic lexical parameter matching against names, keywords, and descriptions.

        Returns list of (TrizParameter, score) sorted in descending order of score.
        """
        text_tokens = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
        if not text_tokens:
            return []

        scored: list[tuple[TrizParameter, float]] = []
        for param in self._parameters.values():
            param_tokens = set(re.findall(r"[a-zA-Z0-9]+", param.name.lower()))
            kw_tokens = {
                tok
                for kw in param.keywords
                for tok in re.findall(r"[a-zA-Z0-9]+", kw.lower())
            }

            # Exact keyword phrase match bonus
            text_lower = text.lower()
            exact_bonus = 0.0
            if any(kw.lower() in text_lower for kw in param.keywords):
                exact_bonus += 0.5
            if param.name.lower() in text_lower:
                exact_bonus += 0.8

            # Jaccard similarities
            name_jaccard = len(text_tokens & param_tokens) / max(1, len(text_tokens | param_tokens))
            kw_jaccard = len(text_tokens & kw_tokens) / max(1, len(text_tokens | kw_tokens)) if kw_tokens else 0.0

            total_score = exact_bonus + 0.6 * name_jaccard + 0.4 * kw_jaccard
            if total_score > 0.05:
                scored.append((param, round(total_score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
