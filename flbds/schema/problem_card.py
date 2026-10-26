"""Problem Card schema: represents target engineering requirements, environment, and constraints."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class SystemSpec(BaseModel):
    """Specification of the target engineering system."""

    name: str = Field(
        ...,
        min_length=1,
        description="Name of the engineering artefact or structure (e.g. desert shelter wall panel)",
    )
    components: list[str] = Field(
        default_factory=list,
        description="Constituent structural components known a priori",
    )
    geometry_summary: Optional[str] = Field(
        default=None,
        description="High-level geometry or dimensional envelope",
    )
    scale: Optional[str] = Field(
        default=None,
        description="Characteristic physical scale (e.g. 10-100 m^2, building envelope)",
    )


class EnvironmentSpec(BaseModel):
    """Target environment resource availability and absence inventory."""

    climate: str = Field(
        ...,
        min_length=1,
        description="Target climate zone (e.g. arid hot desert, marine, sub-arctic)",
    )
    temperature_range: Optional[tuple[float, float]] = Field(
        default=None,
        description="Operating ambient temperature range (T_min, T_max) in degC",
    )
    radiation: Optional[str] = Field(
        default=None,
        description="Solar or ambient radiation profile (e.g. high daytime insolation, clear night sky)",
    )
    fluids_available: list[str] = Field(
        default_factory=list,
        description="Fluids present in target environment (e.g. dry ambient air, wind)",
    )
    energy_available: list[str] = Field(
        default_factory=list,
        description="Energy resources present (e.g. solar direct, nocturnal radiative cooling)",
    )
    resources_absent: list[str] = Field(
        default_factory=list,
        description="Critical absent resources (e.g. liquid water, mains electricity, pressurized coolant)",
    )


class RequiredFunction(BaseModel):
    """Target functional goal formulated in domain-neutral causal terms."""

    action: str = Field(
        ...,
        min_length=1,
        description="Controlled functional verb (e.g. store, regulate, cool, insulate)",
    )
    target_object: str = Field(
        ...,
        min_length=1,
        description="Target object or parameter receiving the function (e.g. thermal energy, indoor air)",
    )
    state_variable: str = Field(
        ...,
        min_length=1,
        description="Target state variable to alter or buffer (e.g. indoor temperature, heat flux)",
    )
    target_change: str = Field(
        ...,
        min_length=1,
        description="Explicit direction and timing of desired change (e.g. store daytime heat, discharge at night)",
    )


class TimePattern(BaseModel):
    """Cyclic timing, period, and operational phases."""

    cycle_type: str = Field(
        ...,
        min_length=1,
        description="Cycle characterization (e.g. diurnal 24h, periodic pulse, steady continuous)",
    )
    period_hours: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Period duration in hours (e.g. 24.0)",
    )
    phases: list[str] = Field(
        default_factory=list,
        description="Ordered sequence of phases (e.g. ['charge_8h_day', 'discharge_12h_night'])",
    )


class Constraint(BaseModel):
    """Hard or soft design boundaries."""

    variable: str = Field(
        ...,
        min_length=1,
        description="Constrained parameter (e.g. mass_per_area, water_consumption, maximum_thickness)",
    )
    bound: str = Field(
        ...,
        min_length=1,
        description="Mathematical inequality or limit (e.g. '<= 40 kg/m^2', '== 0 kg/cycle')",
    )
    hard_or_soft: Literal["hard", "soft"] = Field(
        default="hard",
        description="Classification of constraint: hard (inviolable) or soft (optimizable)",
    )


class Contradiction(BaseModel):
    """Engineering contradiction formulating trade-offs."""

    improving_parameter: str = Field(
        ...,
        min_length=1,
        description="Parameter desired to improve (e.g. heat storage capacity)",
    )
    worsening_parameter: str = Field(
        ...,
        min_length=1,
        description="Parameter that degrades as a consequence (e.g. wall mass or thickness)",
    )
    triz_parameters: list[str] = Field(
        default_factory=list,
        description="Optional TRIZ engineering parameters mapped to the trade-off",
    )


class ProblemCard(BaseModel):
    """Complete specification of target engineering problem, constraints, and environment."""

    problem_id: str = Field(
        ...,
        min_length=1,
        description="Unique problem identifier (e.g. PROB-WALL-001)",
    )
    source_image: Optional[str] = Field(
        default=None,
        description="Optional path or URI to the engineering target image",
    )
    system: SystemSpec
    environment: EnvironmentSpec
    required_function: RequiredFunction
    time_pattern: TimePattern
    constraints: list[Constraint] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    evidence: list[str] = Field(
        default_factory=list,
        description="Design brief statements or patent claims grounding requirements",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of problem parsing",
    )
