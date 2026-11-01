"""Controlled vocabularies and enums for FLBDS v9."""

from enum import Enum


class ResourceEnum(str, Enum):
    """Resources available or absent in problem environment."""
    LIQUID_WATER = "liquid_water"
    WATER_VAPOUR = "water_vapour"
    AMBIENT_AIR = "ambient_air"
    DRY_INERT_GAS = "dry_inert_gas"
    SOLAR_IRRADIANCE = "solar_irradiance"
    NIGHT_SKY_SINK = "night_sky_sink"
    WASTE_HEAT_STREAM = "waste_heat_stream"
    GRID_ELECTRICITY = "grid_electricity"
    PRESSURISED_GAS = "pressurised_gas"


class HazardEnum(str, Enum):
    """Environmental hazards and operational penalties."""
    NONE = "none"
    HIGH_HUMIDITY = "high_humidity"
    DUST_FOULING = "dust_fouling"
    ICING = "icing"
    LOW_SOURCE_TEMPERATURE = "low_source_temperature"


class DirectionEnum(str, Enum):
    """Functional direction of physical state change."""
    INCREASE = "increase"
    DECREASE = "decrease"
    STABILISE = "stabilise"
    STORE_AND_RELEASE = "store-and-release"
    TRANSPORT_DIRECTIONAL = "transport-directional"


class TimeModeEnum(str, Enum):
    """Operational temporal regime."""
    CONTINUOUS = "continuous"
    CYCLIC_DIURNAL = "cyclic_diurnal"
    PULSED = "pulsed"
    STEADY = "steady"


class BoundaryTypeEnum(str, Enum):
    """Boundary condition type for thermal/fluid solver."""
    BC_FLUX = "BC_FLUX"
    BC_TEMP = "BC_TEMP"


class DuctCrossSectionEnum(str, Enum):
    """Duct geometries and analytical Poiseuille friction numbers."""
    CIRCULAR = "circular"
    SQUARE = "square"
    RECTANGULAR_2TO1 = "rectangular_2to1"
    PARALLEL_PLATES = "parallel_plates"

    @property
    def poiseuille_number(self) -> float:
        """Return the laminar Poiseuille friction number (f * Re_Dh)."""
        mapping = {
            DuctCrossSectionEnum.CIRCULAR: 64.0,
            DuctCrossSectionEnum.SQUARE: 56.9,
            DuctCrossSectionEnum.RECTANGULAR_2TO1: 62.2,
            DuctCrossSectionEnum.PARALLEL_PLATES: 96.0,
        }
        return mapping[self]


class TemplateEnum(str, Enum):
    """M5-Screen and M5-Eval physics template identifiers."""
    TPL_01 = "TPL_01"  # Transient conduction and thermal mass
    TPL_02 = "TPL_02"  # Solid-liquid PCM storage
    TPL_03 = "TPL_03"  # Evaporation and condensation
    TPL_04 = "TPL_04"  # Closed-loop sorption storage
    TPL_05 = "TPL_05"  # Capillary wicking
    TPL_06 = "TPL_06"  # Darcy-Forchheimer flow
    TPL_07 = "TPL_07"  # Fin convection
    TPL_08 = "TPL_08"  # Countercurrent exchanger
    TPL_09 = "TPL_09"  # Radiative-convective exchange
    TPL_10 = "TPL_10"  # Fickian and Knudsen diffusion
