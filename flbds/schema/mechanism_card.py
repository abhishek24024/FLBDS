"""Mechanism Card schema: the primary atomic unit of biological and engineering knowledge."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator
from .evidence import EvidenceSpan
from .quantity import Quantity
from .sapphire import (
    Action,
    Organ,
    Part,
    Phenomenon,
    PhysicalEffect,
    ResourceInput,
    StateChange,
)


class Subject(BaseModel):
    """Organism or engineering artefact under description."""

    name: str = Field(
        ...,
        min_length=1,
        description="Taxon name (common or scientific) for bio; product/artefact name for eng",
    )
    identifier: Optional[str] = Field(
        default=None,
        description="Standardized taxon path / NCBI TaxID for bio; CPC classification / patent number for eng",
    )


class Context(BaseModel):
    """Operating environment, habitat, physical scale, and ambient regime."""

    environment: str = Field(
        ...,
        min_length=1,
        description="Ambient environmental conditions (e.g. arid desert, savanna, building envelope)",
    )
    scale: Optional[str] = Field(
        default=None,
        description="Geometric scale description (e.g. macro, micro, 1-10 meters)",
    )
    regime: Optional[str] = Field(
        default=None,
        description="Operational flow or thermal regime (e.g. natural convection, diurnal thermal cycling)",
    )


class MechanismCard(BaseModel):
    """A verified or extracted causal mechanism card grounded in scientific literature or patents."""

    card_id: str = Field(
        ...,
        min_length=1,
        description="Unique card identifier (e.g. MC-BIO-0001, MC-ENG-0042)",
    )
    domain: Literal["bio", "eng"] = Field(
        ...,
        description="Source domain: 'bio' for biological organisms, 'eng' for engineering artefacts",
    )
    subject: Subject
    context: Context

    # Core SAPPhIRE causal chain
    action: Action
    state_change: StateChange
    phenomenon: Phenomenon
    effect: PhysicalEffect
    inputs: list[ResourceInput] = Field(
        default_factory=list,
        description="Required inputs (energy, material, signal) co-activating the effect",
    )
    organ: Optional[Organ] = Field(
        default=None,
        description="Structural property or morphology enabling the phenomenon",
    )
    part: Optional[Part] = Field(
        default=None,
        description="Physical component parts",
    )

    # Quantitative parameters
    quantities: list[Quantity] = Field(
        default_factory=list,
        description="Extracted physical values with verified units and operational regimes",
    )
    constraints_and_resources: list[str] = Field(
        default_factory=list,
        description="Environmental or material constraints needed for function",
    )

    # Grounding, Provenance & Quality
    evidence: list[EvidenceSpan] = Field(
        default_factory=list,
        description="Exact quoted evidence spans grounding each causal claim",
    )
    license: str = Field(
        ...,
        min_length=1,
        description="License copied from the source document (e.g. 'CC BY 4.0', 'CC0', 'US Patent Public Domain')",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="System confidence score in the extracted card (0.0 to 1.0)",
    )
    tier: Literal["gold", "silver"] = Field(
        default="silver",
        description="Verification tier: 'silver' for teacher-extracted cards, 'gold' for human-written ground truth",
    )
    unsupported_fields: list[str] = Field(
        default_factory=list,
        description="List of fields unsupported by cited evidence and deliberately left empty/unfilled",
    )

    @model_validator(mode="after")
    def validate_gold_tier_evidence(self) -> "MechanismCard":
        # Rule 4: If marked gold, it must be human-verified with evidence
        if self.tier == "gold" and not self.evidence:
            raise ValueError("Gold tier cards must include supporting evidence spans.")
        return self
