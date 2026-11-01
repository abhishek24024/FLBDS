"""Ground Truth Evaluation schema (hidden from generator, used by locked evaluation harness)."""

from typing import Any, Optional, Union
from pydantic import BaseModel, Field
from .enums import TemplateEnum


class GroundTruthEval(BaseModel):
    """Hidden evaluation benchmark contract for a case."""
    case_id: str = Field(..., description="Unique case identifier, e.g. DEV-M1-S1, TEST-M01-S2")
    source_card_id: str = Field(..., description="Source biological Mechanism Card ID")
    cluster: str = Field(..., description="Mechanism cluster identifier, e.g. DEV-M1")
    split: int = Field(..., ge=1, le=3, description="Evaluation split (1, 2, or 3)")
    expected_conflicts: list[str] = Field(
        default_factory=list,
        description="Expected conflict flags (resource, direction, timing, regime, medium)",
    )
    expected_operators: list[str] = Field(
        default_factory=list,
        description="Expected operators to resolve conflicts (T1, T2, T3, T4, T5)",
    )
    acceptable_templates: list[Union[TemplateEnum, str]] = Field(
        ...,
        min_length=1,
        description="List of acceptable physical templates (T4 deliberately permits alternative templates)",
    )
    reference_design_file: Optional[str] = Field(
        default=None,
        description="Path to reference design JSON file",
    )
    reference_design: Optional[dict[str, Any]] = Field(
        default=None,
        description="Solver-generated reference parameter design",
    )
    notes: Optional[str] = Field(default=None)
