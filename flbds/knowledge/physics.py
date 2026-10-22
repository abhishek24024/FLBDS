"""The physical laws catalog and dimensionless similitude groups.

Provides canonical :Effect bridge nodes for G_MCKG, variable declarations for the
abductive causal check, and dimensionless numbers for the Buckingham Pi regime auditor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LawVariable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    dimension: str = ""
    unit: str = ""
    role: str = "governing"


class RegimeInterval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float
    max: float


class DimensionlessGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    definition: str
    formula: str
    length_exponent: int
    variables: list[str] = Field(default_factory=list)
    critical_regimes: dict[str, RegimeInterval] = Field(default_factory=dict)
    typical_limit: float = 1.0


class PhysicalLaw(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    equation: str
    domain: str
    description: str
    dimensionless_groups: list[str] = Field(default_factory=list)
    variables: list[LawVariable] = Field(default_factory=list)

    def variable_symbols(self) -> set[str]:
        return {v.symbol.lower() for v in self.variables}


class PhysicalLawsCatalog:
    """Catalog of physical laws and Buckingham Pi dimensionless numbers."""

    def __init__(self, data_path: Path | str | None = None) -> None:
        if data_path is None:
            data_path = Path(__file__).resolve().parent.parent / "data" / "physics" / "laws.json"
        self.data_path = Path(data_path)
        self._laws: dict[str, PhysicalLaw] = {}
        self._groups: dict[str, DimensionlessGroup] = {}
        self._load()

    def _load(self) -> None:
        if not self.data_path.exists():
            return
        data = json.loads(self.data_path.read_text(encoding="utf-8"))
        for g in data.get("dimensionless_groups", []):
            regimes = {}
            for k, v in g.get("critical_regimes", {}).items():
                regimes[k] = RegimeInterval(min=v["min"], max=v["max"])
            group = DimensionlessGroup(
                symbol=g["symbol"],
                name=g["name"],
                definition=g.get("definition", ""),
                formula=g.get("formula", ""),
                length_exponent=g.get("length_exponent", 1),
                variables=g.get("variables", []),
                critical_regimes=regimes,
                typical_limit=g.get("typical_limit", 1.0),
            )
            self._groups[group.symbol] = group

        for l in data.get("laws", []):
            vars_list = [
                LawVariable(
                    symbol=v["symbol"],
                    name=v["name"],
                    dimension=v.get("dimension", ""),
                    unit=v.get("unit", ""),
                    role=v.get("role", "governing"),
                )
                for v in l.get("variables", [])
            ]
            law = PhysicalLaw(
                id=l["id"],
                name=l["name"],
                equation=l.get("equation", ""),
                domain=l.get("domain", ""),
                description=l.get("description", ""),
                dimensionless_groups=l.get("dimensionless_groups", []),
                variables=vars_list,
            )
            self._laws[law.id] = law

    def get_law(self, law_id: str) -> PhysicalLaw:
        if law_id not in self._laws:
            # Try case-insensitive / normalized lookup
            for k, v in self._laws.items():
                if k.lower() == law_id.lower() or v.name.lower() == law_id.lower():
                    return v
            raise KeyError(f"Physical law '{law_id}' not found in catalog")
        return self._laws[law_id]

    def get_group(self, symbol: str) -> DimensionlessGroup:
        if symbol not in self._groups:
            raise KeyError(f"Dimensionless group '{symbol}' not found in catalog")
        return self._groups[symbol]

    def all_laws(self) -> list[PhysicalLaw]:
        return list(self._laws.values())

    def all_groups(self) -> list[DimensionlessGroup]:
        return list(self._groups.values())

    def find_laws_for_variable(self, symbol: str) -> list[PhysicalLaw]:
        sym = symbol.lower()
        return [l for l in self._laws.values() if sym in l.variable_symbols()]

    def find_laws_by_domain(self, domain: str) -> list[PhysicalLaw]:
        dom = domain.lower()
        return [l for l in self._laws.values() if dom in l.domain.lower()]
