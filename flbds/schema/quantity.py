"""Physical quantities with unit validation and regime of validity."""

from typing import Optional
from pydantic import BaseModel, Field, model_validator
import pint

# Shared UnitRegistry for physical dimensional checks
ureg = pint.UnitRegistry()


class Quantity(BaseModel):
    """A physical quantity carrying numerical magnitude, verified unit, and valid operational regime."""

    name: str = Field(
        ...,
        min_length=1,
        description="Physical quantity name (e.g. thermal_diffusivity, latent_heat, thickness)",
    )
    value: float = Field(
        ...,
        description="Numerical magnitude of the quantity",
    )
    unit: str = Field(
        ...,
        min_length=1,
        description="Pint-compatible unit string (e.g. 'W / (m * K)', 'kJ / kg', 'mm', 'kg / m^2')",
    )
    regime_of_validity: Optional[str] = Field(
        default=None,
        description="Operational regime or validity boundary (e.g., 'Biot < 0.1', '25-45 degC', 'dry air')",
    )

    @model_validator(mode="after")
    def validate_unit_string(self) -> "Quantity":
        try:
            ureg.parse_units(self.unit)
        except Exception as exc:
            raise ValueError(f"Unparseable or invalid unit string '{self.unit}': {exc}") from exc
        return self
