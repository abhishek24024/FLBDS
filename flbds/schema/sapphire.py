"""SAPPhIRE causal ontology constructs for biological and engineering mechanisms."""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from .quantity import Quantity


class StateChange(BaseModel):
    """SAPPhIRE State Change: change of state property across time or boundary."""

    state_variable: str = Field(
        ...,
        min_length=1,
        description="Physical state variable that changes (e.g. skin_temperature, internal_energy, fluid_saturation)",
    )
    from_value: Optional[str] = Field(
        default=None,
        description="Initial state baseline value or qualitative descriptor",
    )
    to_value: Optional[str] = Field(
        default=None,
        description="Target state value or qualitative descriptor",
    )
    magnitude: Optional[Quantity] = Field(
        default=None,
        description="Quantitative change with verified units if reported in source text",
    )


class Action(BaseModel):
    """SAPPhIRE Action: higher-level purpose or function interpreted from the state change."""

    verb: str = Field(
        ...,
        min_length=1,
        description="Controlled-vocabulary action verb (e.g. regulate, store, dissipate, absorb, insulate)",
    )
    object: str = Field(
        ...,
        min_length=1,
        description="Object or entity receiving the action (e.g. body_temperature, thermal_energy, working_fluid)",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the function",
    )


class Phenomenon(BaseModel):
    """SAPPhIRE Phenomenon: the physical process or behavior underlying the state change."""

    description: str = Field(
        ...,
        min_length=1,
        description="Description of physical phenomenon (e.g. evaporation from a porous mud-coated skin layer)",
    )


class PhysicalEffect(BaseModel):
    """SAPPhIRE Effect: canonical physical law, effect, or governing equation co-activated by organ and input."""

    canonical_name: str = Field(
        ...,
        min_length=1,
        description="Standardized name of physical effect (e.g. latent_heat_of_vaporization, fourier_conduction, darcy_flow)",
    )
    governing_equation: Optional[str] = Field(
        default=None,
        description="Mathematical formulation or law representation (e.g. Q = m * h_fg, q = -k * grad(T))",
    )
    relevant_variables: list[str] = Field(
        default_factory=list,
        description="Key variables governed by this effect",
    )


class ResourceInput(BaseModel):
    """SAPPhIRE Input: energy, material, or signal required to co-activate the effect."""

    input_type: Literal["material", "energy", "signal"] = Field(
        ...,
        description="Category of input resource",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Name of resource (e.g. liquid_water, solar_radiation, ambient_air)",
    )
    rate_or_quantity: Optional[Quantity] = Field(
        default=None,
        description="Quantitative resource rate or amount",
    )


class Organ(BaseModel):
    """SAPPhIRE oRgan: structural properties and morphological conditions enabling the phenomenon."""

    description: str = Field(
        ...,
        min_length=1,
        description="Morphological or structural enabling property (e.g. micro-channelled crevice matrix)",
    )


class Part(BaseModel):
    """SAPPhIRE Part: physical components or constituent elements."""

    description: str = Field(
        ...,
        min_length=1,
        description="Physical component or anatomy (e.g. epidermis, porous mud crust, thermal mass core)",
    )
