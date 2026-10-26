"""Verification Report schema: structured output of the executable lumped-parameter physics verifier."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class AssertionResult(BaseModel):
    """Result of an individual physical assertion (e.g. energy conservation, unit consistency)."""

    assertion_name: str = Field(
        ...,
        min_length=1,
        description="Name of the physical assertion (e.g. 'energy_closure', 'mass_closure', 'units_consistent', 'within_regime')",
    )
    passed: bool = Field(
        ...,
        description="True if the physical assertion was satisfied, False otherwise",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Detailed numerical or physical explanation of pass/fail outcome",
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional diagnostic values, residuals, or dimensionless group values",
    )


class PhysicsCheck(BaseModel):
    """Execution output from a specific lumped-parameter physics template."""

    template_name: str = Field(
        ...,
        min_length=1,
        description="Identifier of the executed physics template (e.g. 'latent_heat_storage_sizing', 'fourier_conduction_1d')",
    )
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of input parameters with unit annotations",
    )
    results: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of computed output quantities with unit annotations",
    )
    assertions: list[AssertionResult] = Field(
        default_factory=list,
        description="List of physical assertions evaluated during template execution",
    )
    verdict: Literal["pass", "fail", "not_modelled"] = Field(
        ...,
        description="Outcome of this template check. 'not_modelled' cannot be counted as a pass.",
    )


class VerificationReport(BaseModel):
    """Complete physics verification report and feasible parameter bounds for a proposed concept."""

    concept_id: str = Field(
        ...,
        min_length=1,
        description="Unique concept identifier evaluated (e.g. C-WALL-001)",
    )
    checks: list[PhysicsCheck] = Field(
        default_factory=list,
        description="List of individual physics template checks",
    )
    feasible_set: dict[str, tuple[float, float]] = Field(
        default_factory=dict,
        description="Feasible bounds [min, max] for design parameters (e.g. {'thickness_m': (0.02, 0.05)})",
    )
    unmodelled_effects: list[str] = Field(
        default_factory=list,
        description="Identified physical phenomena that lack templates and could not be verified",
    )
    overall_verdict: Literal["pass", "fail", "not_modelled"] = Field(
        ...,
        description="Aggregated verdict. If any check fails or is not_modelled, overall cannot be 'pass'.",
    )

    @model_validator(mode="after")
    def validate_overall_verdict(self) -> "VerificationReport":
        # Any check that fails forces overall fail
        any_failed = any(c.verdict == "fail" for c in self.checks)
        any_not_modelled = any(c.verdict == "not_modelled" for c in self.checks) or bool(self.unmodelled_effects)

        if any_failed and self.overall_verdict == "pass":
            raise ValueError("Overall verdict cannot be 'pass' when one or more individual checks fail.")

        if any_not_modelled and self.overall_verdict == "pass":
            raise ValueError(
                "Overall verdict cannot be 'pass' when there are unmodelled effects or 'not_modelled' checks."
            )

        return self
