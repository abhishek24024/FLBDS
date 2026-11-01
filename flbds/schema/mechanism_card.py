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


class AbstractionLadder(BaseModel):
    """Five-level abstraction ladder for cross-domain retrieval (L0 to L4)."""

    L0_specimen: Optional[str] = Field(default=None, description="L0 Specimen description or organism instance")
    L1_mechanism: Optional[str] = Field(default=None, description="L1 Specific domain mechanism description")
    L2_causal_chain: Optional[str] = Field(default=None, description="L2 SAPPhIRE causal chain graph summary")
    L3_solution_neutral_principle: Optional[str] = Field(default=None, description="L3 Solution-neutral physical principle")
    L4_function: Optional[str] = Field(default=None, description="L4 High-level abstract functional goal")


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
    figure_regions: list[str] = Field(
        default_factory=list,
        description="Citations to specific figure panels or ROI bounding boxes (e.g. ['Fig 2B [100,50,400,300]'])",
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
    human_verified: bool = Field(
        default=False,
        description="Explicit flag indicating whether card has been reviewed and certified by a human expert",
    )
    extraction_agreement: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Agreement score across independent teacher extraction runs",
    )
    unsupported_fields: list[str] = Field(
        default_factory=list,
        description="List of fields unsupported by cited evidence and deliberately left empty/unfilled",
    )

    # v9 Abstraction Ladder & Multimodal Embeddings
    abstraction_ladder: Optional[AbstractionLadder] = Field(
        default=None,
        description="Five-tier abstraction ladder from L0 specimen to L4 function",
    )
    purpose_embedding: Optional[list[float]] = Field(
        default=None,
        description="Functional purpose vector embedding (from L4)",
    )
    mechanism_embedding: Optional[list[float]] = Field(
        default=None,
        description="Solution-neutral mechanism vector embedding (from L3)",
    )
    effect_embedding: Optional[list[float]] = Field(
        default=None,
        description="Physical effect vector embedding (from L2)",
    )

    @model_validator(mode="after")
    def validate_gold_tier_evidence(self) -> "MechanismCard":
        # Rule 4: If marked gold, it must be human-verified with evidence
        if self.tier == "gold" and not self.evidence:
            raise ValueError("Gold tier cards must include supporting evidence spans.")
        if self.tier == "gold":
            self.human_verified = True
        return self
