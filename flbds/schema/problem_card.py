"""Problem Card schema: represents target engineering requirements, environment, and constraints."""

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator
from .enums import BoundaryTypeEnum, DirectionEnum, HazardEnum, ResourceEnum, TimeModeEnum


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
    """Target environment resource availability, absence inventory, and hazards."""

    climate: str = Field(
        ...,
        min_length=1,
        description="Target climate zone (e.g. arid hot desert, marine, sub-arctic)",
    )
    temperature_range: Optional[tuple[float, float]] = Field(
        default=None,
        description="Operating ambient temperature range (T_min, T_max) in degC",
    )
    relative_humidity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Ambient relative humidity (0.0 to 1.0)",
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
    resources_available: list[Union[ResourceEnum, str]] = Field(
        default_factory=list,
        description="Typed inventory of available environmental resources",
    )
    resources_absent: list[Union[ResourceEnum, str]] = Field(
        default_factory=list,
        description="Critical absent resources (e.g. liquid water, mains electricity, pressurized coolant)",
    )
    hazards: list[Union[HazardEnum, str]] = Field(
        default_factory=list,
        description="Environmental hazards (e.g. high_humidity, dust_fouling, icing)",
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
    target_direction: Optional[Union[DirectionEnum, str]] = Field(
        default=None,
        description="Controlled functional direction enum (increase, decrease, stabilise, store-and-release)",
    )
    boundary_type: Optional[Union[BoundaryTypeEnum, str]] = Field(
        default=None,
        description="Thermodynamic boundary condition type (BC_FLUX or BC_TEMP)",
    )
    flux_or_load: Optional[float] = Field(
        default=None,
        description="Target thermal or fluid flux/duty magnitude (e.g. 200 W/m^2)",
    )


class TimePattern(BaseModel):
    """Cyclic timing, period, and operational phases."""

    cycle_type: str = Field(
        ...,
        min_length=1,
        description="Cycle characterization (e.g. diurnal 24h, periodic pulse, steady continuous)",
    )
    time_mode: Optional[Union[TimeModeEnum, str]] = Field(
        default=None,
        description="Operational temporal mode enum (continuous, cyclic_diurnal, pulsed, steady)",
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


class HardConstraints(BaseModel):
    """Typed hard engineering constraints enforced by M5-Screen and M5-Eval."""

    max_thickness_m: Optional[float] = Field(default=None, gt=0.0)
    max_mass_kg_m2: Optional[float] = Field(default=None, gt=0.0)
    max_pressure_drop_Pa: Optional[float] = Field(default=None, gt=0.0)
    max_surface_superheat_K: Optional[float] = Field(default=None, gt=0.0)
    min_pore_diameter_m: Optional[float] = Field(default=None, gt=0.0)
    min_cop: Optional[float] = Field(default=None, gt=0.0)
    max_envelope_height_m: Optional[float] = Field(default=None, gt=0.0)

    @model_validator(mode="before")
    @classmethod
    def harmonize_constraints(cls, data: Any):
        if not isinstance(data, dict):
            return data
        if "thickness_max_m" in data and "max_thickness_m" not in data:
            data["max_thickness_m"] = data["thickness_max_m"]
        if "mass_per_area_max_kg_m2" in data and "max_mass_kg_m2" not in data:
            data["max_mass_kg_m2"] = data["mass_per_area_max_kg_m2"]
        if "pressure_drop_max_Pa" in data and "max_pressure_drop_Pa" not in data:
            data["max_pressure_drop_Pa"] = data["pressure_drop_max_Pa"]
        if "surface_superheat_max_K" in data and "max_surface_superheat_K" not in data:
            data["max_surface_superheat_K"] = data["surface_superheat_max_K"]
        if "minimum_pore_diameter_m" in data and "min_pore_diameter_m" not in data:
            data["min_pore_diameter_m"] = data["minimum_pore_diameter_m"]
        if "envelope_height_max_m" in data and "max_envelope_height_m" not in data:
            data["max_envelope_height_m"] = data["envelope_height_max_m"]
        return data

    @property
    def thickness_max_m(self) -> Optional[float]:
        return self.max_thickness_m

    @property
    def mass_per_area_max_kg_m2(self) -> Optional[float]:
        return self.max_mass_kg_m2


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
    hard_constraints: Optional[HardConstraints] = Field(
        default=None,
        description="Explicit typed hard constraints per v9 specification",
    )
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

    @model_validator(mode="after")
    def verify_no_template_leakage(self) -> "ProblemCard":
        """Verify that ProblemCard strictly contains NO template names (v9 principle P7)."""
        card_str = str(self.model_dump()).upper()
        for tpl_num in range(1, 11):
            bad_key = f"TPL_{tpl_num:02d}"
            bad_key2 = f"TPL-{tpl_num:02d}"
            if bad_key in card_str or bad_key2 in card_str:
                raise ValueError(f"Template leakage detected: ProblemCard must not contain template name {bad_key}")
        return self
