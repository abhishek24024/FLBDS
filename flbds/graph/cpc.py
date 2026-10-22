"""Cooperative Patent Classification (CPC) hierarchies and Patent ROI linking."""

from __future__ import annotations

import re
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
        # Section A: Human Necessities
        "A01": "Agriculture; forestry; animal husbandry; hunting; trapping; fishing",
        "A61": "Medical or veterinary science; hygiene; prosthetics; surgical instruments",
        "A62": "Life-saving; fire-fighting",

        # Section B: Performing Operations; Transporting
        "B01": "Physical or chemical processes or apparatus in general (filtration, separation)",
        "B05": "Spraying or atomising; applying liquids to surfaces in general (coatings, superhydrophobic films)",
        "B08": "Cleaning (self-cleaning surfaces, ultrasonic cleaning)",
        "B25": "Hand tools; portable power-driven tools; manipulators (robotic grippers, dry adhesives)",
        "B60": "Vehicles in general (high-speed railways, aerodynamic nose cones, passive suspension)",
        "B60L": "Electric equipment or propulsion of electrically-propelled vehicles",
        "B64": "Aircraft; aviation; cosmonautics (aerodynamic winglets, boundary layer control, riblets)",
        "B64C": "Aeroplanes; helicopters (airfoils, boundary layer controls, wings)",
        "B81": "Microstructural technology; micro-electromechanical devices (MEMS)",
        "B82": "Nanotechnology; nano-structures; nano-materials",

        # Section C: Chemistry; Metallurgy
        "C02": "Treatment of water, waste water, sewage (filtration membranes, water harvesting)",
        "C03": "Glass; mineral or slag wool (structural color glass, anti-reflective coatings)",
        "C08": "Organic macromolecular compounds (elastomers, hydrogels, biopolymers)",
        "C09": "Dyes; paints; polishes; natural resins; adhesives; materials not otherwise provided for",
        "C12": "Biochemistry; beer; spirits; wine; vinegar; microbiology; enzymology",

        # Section D: Textiles; Paper
        "D06": "Treatment of textiles or the like; laundering; flexible materials not otherwise provided for",
        "D06M": "Treatment of fibres, threads, yarns, fabrics with liquids, gases or vapours",

        # Section E: Fixed Constructions
        "E04": "Building; construction of buildings (passive cooling, facade ventilation, lightweight trusses)",
        "E04B": "General building constructions; walls, facades, roofs, thermal insulation",
        "E06": "Doors, windows, shutters, or roller blinds in general; ladders",

        # Section F: Mechanical Engineering; Lighting; Heating; Weapons; Blasting
        "F01": "Machines or engines in general (steam, gas, combustion)",
        "F03": "Machines or engines for liquids; wind motors (turbine blades, tubercle hydrofoils)",
        "F03D": "Wind motors (airfoils, lift-enhancement, passive vortex generators)",
        "F15": "Fluid-pressure actuators; hydraulics or pneumatics in general",
        "F16": "Engineering elements and units; general measures for producing and maintaining effective functioning of machines",
        "F16C": "Shafts; flexible shafts; mechanical gearings; bearings",
        "F16F": "Springs; shock-absorbers; means for damping vibration",
        "F16L": "Pipes; joints or fittings for pipes; tubes (drag reduction conduits)",
        "F28": "Heat exchange in general (microchannel heat sinks, heat pipes, passive cooling radiators)",
        "F28F": "Details of heat-exchange or heat-transfer apparatus (fin arrays, turbulent promoters)",

        # Section G: Physics
        "G01": "Measuring; testing (sensors, biomimetic artificial vision, tactile sensing)",
        "G02": "Optics (lenses, antireflective arrays, photonic crystals)",

        # Section H: Electricity
        "H01": "Basic electric elements (capacitors, batteries, piezoelectric transducers)",
        "H02": "Generation, conversion, or distribution of electric power",
    }

    KEYWORD_TO_CPC: list[tuple[str, str]] = [
        (r"\b(?:heat|thermal|cool|cooling|radiator|heat\s*sink|exchanger)\b", "F28F"),
        (r"\b(?:aerodynamic|aircraft|wing|fuselage|airfoil|flight|aviation)\b", "B64C"),
        (r"\b(?:train|rail|vehicle|automotive|car|nose\s*cone)\b", "B60"),
        (r"\b(?:building|facade|architecture|wall|roof|ventilation|cooling\s*tower)\b", "E04B"),
        (r"\b(?:gripper|adhesive|adhesion|tape|fastener|clamp|robot)\b", "B25"),
        (r"\b(?:drag|friction|fluid|pipe|conduit|valve|nozzle)\b", "F16L"),
        (r"\b(?:turbine|blade|wind|hydrofoil|propeller)\b", "F03D"),
        (r"\b(?:water|filter|membrane|harvest|desalination|purification)\b", "C02"),
        (r"\b(?:textile|fabric|fiber|cloth|yarn|wearable)\b", "D06M"),
        (r"\b(?:optical|lens|color|refractive|photonic|display)\b", "G02"),
        (r"\b(?:sensor|detector|measurement|acoustic|sonar)\b", "G01"),
        (r"\b(?:nano|mems|microstructure|micropattern)\b", "B81"),
    ]

    @classmethod
    def get_description(cls, cpc_symbol: str) -> str:
        code = cpc_symbol.strip().upper()
        for prefix in (code[:4], code[:3], code[:1]):
            if prefix in cls.CPC_DESCRIPTIONS:
                return cls.CPC_DESCRIPTIONS[prefix]
        return "Mechanical or structural engineering contraption"

    @classmethod
    def infer_cpc(cls, text: str) -> str:
        """Infer canonical CPC classification from problem or application description."""
        for pat, code in cls.KEYWORD_TO_CPC:
            if re.search(pat, text, re.IGNORECASE):
                return code
        return "F16"  # Default general mechanical engineering elements
