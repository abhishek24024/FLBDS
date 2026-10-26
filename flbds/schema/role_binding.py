"""Role Binding schema: structural mapping and transformation of source roles to target roles."""

from typing import Literal
from pydantic import BaseModel, Field


class RoleBinding(BaseModel):
    """Mapping between a biological source role and an engineering target role with transformation operators."""

    binding_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this role binding (e.g. RB-001)",
    )
    source_role: str = Field(
        ...,
        min_length=1,
        description="Source SAPPhIRE role identifier or description (e.g. 'Input: liquid water')",
    )
    target_role: str = Field(
        ...,
        min_length=1,
        description="Target engineering role or element (e.g. 'Working fluid in sealed phase-change matrix')",
    )
    relation: Literal["preserved", "transformed", "substituted", "dropped"] = Field(
        ...,
        description="Status of mapping: preserved, transformed by operator, substituted, or explicitly dropped",
    )
    operator: Literal["none", "T1", "T2", "T3", "T4"] = Field(
        default="none",
        description="Transformation operator applied: none, T1 (loop closing), T2 (flow inversion), T3 (phase shift), T4 (mechanism substitution)",
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Causal, environmental, or thermodynamic rationale for the transformation",
    )
    proof_obligations: list[str] = Field(
        default_factory=list,
        description="List of verifier test obligations (e.g. ['mass_closure', 'energy_sign_check', 'cycle_closure'])",
    )
