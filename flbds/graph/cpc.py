"""Cooperative Patent Classification (CPC) hierarchies and Patent ROI linking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PatentFigureROI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    figure_id: str
    patent_number: str
    callout_numeral: str
    bbox: list[float] = Field(default_factory=list, description="[ymin, xmin, ymax, xmax]")
    depicts_part_id: str | None = None
    illustrates_organ_id: str | None = None
    caption: str = ""


class CPCHierarchy:
    """CPC classification mapper for engineering contraption streams."""

    CPC_DESCRIPTIONS = {
        "F16": "Engineering elements and units; general measures for producing and maintaining effective functioning of machines",
        "F16C": "Shafts; flexible shafts; mechanical gearings; bearings",
        "B64": "Aircraft; aviation; cosmonautics",
        "B64C": "Aeroplanes; helicopters (airfoils, boundary layer controls, wings)",
        "B60": "Vehicles in general (high-speed railways, aerodynamic nose cones)",
        "B60L": "Electric equipment or propulsion of electrically-propelled vehicles",
        "E04": "Building; construction of buildings",
        "E04B": "General building constructions; walls, facades, roofs, thermal insulation",
        "F28": "Heat exchange in general",
        "F28F": "Details of heat-exchange or heat-transfer apparatus",
        "B81": "Microstructural technology; micro-electromechanical devices (MEMS)",
        "B82": "Nanotechnology",
    }

    @classmethod
    def get_description(cls, cpc_symbol: str) -> str:
        code = cpc_symbol.strip().upper()
        for prefix in (code[:4], code[:3], code[:1]):
            if prefix in cls.CPC_DESCRIPTIONS:
                return cls.CPC_DESCRIPTIONS[prefix]
        return "Mechanical or structural engineering contraption"
