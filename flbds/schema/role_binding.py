"""Role Binding schema: maps source mechanism elements to target problem elements."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class RoleBinding(BaseModel):
    """An explicit analogical role binding between source and target causal graph nodes."""

    binding_id: Optional[str] = Field(
        default=None,
        description="Unique binding identifier (e.g. RB-001)",
    )
    # v9 primary fields
    source_node: Optional[str] = Field(
        default=None,
        description="Source SAPPhIRE graph node identifier or causal role",
    )
    target_node: Optional[str] = Field(
        default=None,
        description="Target system component, functional role, or boundary",
    )
    source_role: Optional[str] = Field(
        default=None,
        description="Source role descriptor (legacy / descriptive)",
    )
    target_role: Optional[str] = Field(
        default=None,
        description="Target role descriptor (legacy / descriptive)",
    )
    relation: Literal["preserved", "transformed", "substituted", "dropped"] = Field(
        ...,
        description="Categorical relation: preserved, transformed (via operator), substituted, or dropped",
    )
    operator: Optional[str] = Field(
        default=None,
        description="Specific transformation operator applied (e.g. T1, T2, T3, T4, T5)",
    )
    justification: Optional[str] = Field(
        default=None,
        description="Physical rationale justifying the binding and transformation",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Physical rationale (legacy field)",
    )
    source_card_node_ids: list[str] = Field(
        default_factory=list,
        description="List of exact node IDs cited from the source MechanismCard (e.g. ['effect_01', 'input_water'])",
    )
    proof_obligations: list[str] = Field(
        default_factory=list,
        description="Required physics verifier assertions to substantiate the transformed role",
    )

    @model_validator(mode="after")
    def reconcile_aliases(self) -> "RoleBinding":
        if not self.source_node and self.source_role:
            self.source_node = self.source_role
        elif not self.source_role and self.source_node:
            self.source_role = self.source_node

        if not self.target_node and self.target_role:
            self.target_node = self.target_role
        elif not self.target_role and self.target_node:
            self.target_role = self.target_node

        if not self.justification and self.reason:
            self.justification = self.reason
        elif not self.reason and self.justification:
            self.reason = self.justification
        return self
