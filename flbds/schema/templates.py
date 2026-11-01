"""Typed parameter schemas for M5 Physics Templates (TPL-01 to TPL-10) with discriminated union."""

from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator
from .enums import DuctCrossSectionEnum, TemplateEnum


class TPL01Params(BaseModel):
    """TPL-01: Transient conduction and thermal mass."""
    template_id: Literal[TemplateEnum.TPL_01, "TPL_01"] = TemplateEnum.TPL_01
    thickness_m: float = Field(..., gt=0.0, description="Layer thickness in meters")
    density_kg_m3: float = Field(..., gt=0.0, description="Material density in kg/m^3")
    specific_heat_J_kgK: float = Field(..., gt=0.0, description="Specific heat capacity in J/(kg*K)")
    thermal_conductivity_W_mK: float = Field(..., gt=0.0, description="Thermal conductivity in W/(m*K)")
    required_energy_J_m2: float = Field(..., gt=0.0, description="Required stored energy per area in J/m^2")
    period_hours: float = Field(default=24.0, gt=0.0, description="Diurnal cycle period in hours")


class TPL02Params(BaseModel):
    """TPL-02: Solid-liquid PCM storage."""
    template_id: Literal[TemplateEnum.TPL_02, "TPL_02"] = TemplateEnum.TPL_02
    thickness_m: float = Field(..., gt=0.0, description="Layer thickness in meters")
    pcm_density_kg_m3: float = Field(default=820.0, gt=0.0, description="Pure PCM density in kg/m^3")
    pcm_latent_heat_J_kg: float = Field(default=210000.0, gt=0.0, description="PCM latent heat of fusion in J/kg")
    pcm_specific_heat_J_kgK: float = Field(default=2000.0, gt=0.0, description="PCM solid/liquid specific heat in J/(kg*K)")
    matrix_volume_fraction: float = Field(default=0.0, ge=0.0, lt=1.0, description="Metal/matrix volume fraction (e.g. 0.12 for 12% foam)")
    matrix_density_kg_m3: float = Field(default=2700.0, ge=0.0, description="Matrix material density in kg/m^3 (e.g. aluminium)")
    matrix_specific_heat_J_kgK: float = Field(default=900.0, gt=0.0, description="Matrix specific heat in J/(kg*K)")
    k_eff_W_mK: float = Field(..., gt=0.0, description="Effective thermal conductivity in W/(m*K)")
    melting_temp_degC: float = Field(default=28.0, description="PCM melting point in degC")
    superheat_limit_K: float = Field(default=10.0, gt=0.0, description="Maximum allowable end-of-charge surface superheat in K")
    heat_flux_W_m2: float = Field(default=200.0, gt=0.0, description="Constant absorbed heat flux in W/m^2")
    charge_hours: float = Field(default=8.0, gt=0.0, description="Charging duration in hours")
    required_energy_J_m2: float = Field(default=5.76e6, gt=0.0, description="Required storable energy in J/m^2 (e.g. 5.76 MJ/m^2)")


class TPL03Params(BaseModel):
    """TPL-03: Evaporation and condensation."""
    template_id: Literal[TemplateEnum.TPL_03, "TPL_03"] = TemplateEnum.TPL_03
    latent_heat_J_kg: float = Field(default=2.4e6, gt=0.0, description="Latent heat of vaporization in J/kg")
    evaporation_rate_kg_m2_s: float = Field(default=1e-4, gt=0.0, description="Evaporation rate per area in kg/(m^2*s)")
    water_budget_kg_m2: float = Field(default=10.0, ge=0.0, description="Available water mass budget in kg/m^2")
    ambient_relative_humidity: float = Field(default=0.4, ge=0.0, le=1.0, description="Ambient relative humidity")
    air_velocity_m_s: float = Field(default=1.0, ge=0.0, description="Air flow velocity in m/s")
    characteristic_length_m: float = Field(default=1.0, gt=0.0, description="Characteristic surface length in meters")


class TPL04Params(BaseModel):
    """TPL-04: Closed-loop sorption storage."""
    template_id: Literal[TemplateEnum.TPL_04, "TPL_04"] = TemplateEnum.TPL_04
    bulk_density_kg_m3: float = Field(..., gt=0.0, description="Bulk sorbent density in kg/m^3")
    sorption_density_J_kg: float = Field(..., gt=0.0, description="Sorption energy density in J/kg sorbent")
    regeneration_temp_degC: float = Field(..., description="Desorption regeneration temperature in degC")
    ldf_time_constant_s: float = Field(..., gt=0.0, description="Linear driving force adsorption time constant in seconds")
    charge_period_hours: float = Field(default=8.0, gt=0.0, description="Charge period duration in hours")


class TPL05Params(BaseModel):
    """TPL-05: Capillary wicking."""
    template_id: Literal[TemplateEnum.TPL_05, "TPL_05"] = TemplateEnum.TPL_05
    lift_height_m: float = Field(..., gt=0.0, description="Required vertical capillary lift height in meters")
    pore_radius_m: float = Field(..., gt=0.0, description="Effective pore/capillary radius in meters")
    surface_tension_N_m: float = Field(default=0.0728, gt=0.0, description="Fluid surface tension in N/m")
    contact_angle_deg: float = Field(default=0.0, ge=0.0, le=90.0, description="Wetting contact angle in degrees")
    permeability_m2: float = Field(..., gt=0.0, description="Porous medium permeability in m^2")
    dynamic_viscosity_Pa_s: float = Field(default=1e-3, gt=0.0, description="Fluid dynamic viscosity in Pa*s")
    fluid_density_kg_m3: float = Field(default=1000.0, gt=0.0, description="Fluid density in kg/m^3")
    required_mass_flux_kg_m2_s: float = Field(..., gt=0.0, description="Required replenishment mass flux in kg/(m^2*s)")


class TPL06Params(BaseModel):
    """TPL-06: Darcy-Forchheimer flow."""
    template_id: Literal[TemplateEnum.TPL_06, "TPL_06"] = TemplateEnum.TPL_06
    bed_length_m: float = Field(..., gt=0.0, description="Porous bed flow length in meters")
    bed_porosity: float = Field(..., gt=0.0, lt=1.0, description="Bed porosity void fraction")
    mean_pore_diameter_m: float = Field(..., gt=0.0, description="Mean pore/particle diameter in meters")
    fluid_density_kg_m3: float = Field(default=1000.0, gt=0.0, description="Fluid density in kg/m^3")
    fluid_viscosity_Pa_s: float = Field(default=1e-3, gt=0.0, description="Dynamic viscosity in Pa*s")
    superficial_velocity_m_s: float = Field(..., gt=0.0, description="Superficial Darcy velocity in m/s")
    pressure_drop_cap_Pa: float = Field(..., gt=0.0, description="Maximum allowable pressure drop in Pa")
    min_pumping_cop: float = Field(default=10.0, gt=0.0, description="Minimum allowable thermal-to-pumping COP")


class TPL07Params(BaseModel):
    """TPL-07: Fin convection."""
    template_id: Literal[TemplateEnum.TPL_07, "TPL_07"] = TemplateEnum.TPL_07
    fin_thickness_m: float = Field(..., gt=0.0, description="Fin profile thickness in meters")
    fin_spacing_m: float = Field(..., gt=0.0, description="Clearance spacing between adjacent fins in meters")
    fin_length_m: float = Field(..., gt=0.0, description="Fin length in meters")
    fin_conductivity_W_mK: float = Field(..., gt=0.0, description="Fin solid thermal conductivity in W/(m*K)")
    h_conv_W_m2K: float = Field(..., gt=0.0, description="Convective heat transfer coefficient in W/(m^2*K)")
    fluid_thermal_diffusivity_m2_s: float = Field(default=2.2e-5, gt=0.0, description="Fluid thermal diffusivity in m^2/s")


class TPL08Params(BaseModel):
    """TPL-08: Countercurrent exchanger."""
    template_id: Literal[TemplateEnum.TPL_08, "TPL_08"] = TemplateEnum.TPL_08
    duct_type: DuctCrossSectionEnum = Field(default=DuctCrossSectionEnum.CIRCULAR, description="Cross section geometry")
    mass_flow_rate_kg_s: Optional[float] = Field(default=None, description="Fluid mass flow rate in kg/s")
    m_dot_hot_kg_s: float = Field(default=0.05, gt=0.0, description="Hot fluid mass flow rate in kg/s")
    m_dot_cold_kg_s: float = Field(default=0.05, gt=0.0, description="Cold fluid mass flow rate in kg/s")
    c_p_J_kgK: float = Field(default=4184.0, gt=0.0, description="Fluid specific heat capacity in J/(kg*K)")
    cp_hot_J_kgK: float = Field(default=4184.0, gt=0.0, description="Hot fluid specific heat in J/(kg*K)")
    cp_cold_J_kgK: float = Field(default=4184.0, gt=0.0, description="Cold fluid specific heat in J/(kg*K)")
    u_overall_W_m2K: Optional[float] = Field(default=None, description="Overall heat transfer coefficient in W/(m^2*K)")
    overall_U_W_m2K: float = Field(default=600.0, gt=0.0, description="Overall heat transfer coefficient in W/(m^2*K)")
    exchange_area_m2: Optional[float] = Field(default=None, description="Total exchange surface area in m^2")
    heat_transfer_area_m2: float = Field(default=1.0, gt=0.0, description="Heat transfer surface area in m^2")
    duct_length_m: Optional[float] = Field(default=None, description="Duct channel length in meters")
    length_m: float = Field(default=0.5, gt=0.0, description="Exchanger channel length in meters")
    hydraulic_diameter_m: float = Field(default=0.01, gt=0.0, description="Channel hydraulic diameter in meters")
    fluid_viscosity_Pa_s: float = Field(default=1e-3, gt=0.0, description="Dynamic viscosity in Pa*s")
    fluid_density_kg_m3: float = Field(default=1000.0, gt=0.0, description="Fluid density in kg/m^3")
    pressure_drop_cap_Pa: Optional[float] = Field(default=None, description="Maximum allowable pressure drop in Pa")
    max_pressure_drop_Pa: float = Field(default=500.0, gt=0.0, description="Maximum allowable pressure drop in Pa")
    T_hot_in_degC: float = Field(default=40.0, description="Hot stream inlet temperature in degC")
    T_cold_in_degC: float = Field(default=20.0, description="Cold stream inlet temperature in degC")
    required_duty_W: float = Field(default=1000.0, gt=0.0, description="Required heat exchange duty in Watts")
    wall_conductivity_W_mK: float = Field(default=15.0, gt=0.0, description="Wall solid thermal conductivity in W/(m*K)")
    wall_cross_section_m2: float = Field(default=1e-4, ge=0.0, description="Wall axial conduction cross-sectional area in m^2")

    @model_validator(mode="before")
    @classmethod
    def harmonize_fields(cls, data: dict):
        if not isinstance(data, dict):
            return data
        if "duct_length_m" in data and "length_m" not in data:
            data["length_m"] = data["duct_length_m"]
        elif "length_m" in data and "duct_length_m" not in data:
            data["duct_length_m"] = data["length_m"]

        if "u_overall_W_m2K" in data and "overall_U_W_m2K" not in data:
            data["overall_U_W_m2K"] = data["u_overall_W_m2K"]
        elif "overall_U_W_m2K" in data and "u_overall_W_m2K" not in data:
            data["u_overall_W_m2K"] = data["overall_U_W_m2K"]

        if "exchange_area_m2" in data and "heat_transfer_area_m2" not in data:
            data["heat_transfer_area_m2"] = data["exchange_area_m2"]
        elif "heat_transfer_area_m2" in data and "exchange_area_m2" not in data:
            data["exchange_area_m2"] = data["heat_transfer_area_m2"]

        if "pressure_drop_cap_Pa" in data and "max_pressure_drop_Pa" not in data:
            data["max_pressure_drop_Pa"] = data["pressure_drop_cap_Pa"]
        elif "max_pressure_drop_Pa" in data and "pressure_drop_cap_Pa" not in data:
            data["pressure_drop_cap_Pa"] = data["max_pressure_drop_Pa"]

        if "channel_geometry" in data and "duct_type" not in data:
            data["duct_type"] = data["channel_geometry"]
        elif "duct_type" in data and "channel_geometry" not in data:
            data["channel_geometry"] = data["duct_type"]

        if "mass_flow_rate_kg_s" in data:
            if "m_dot_hot_kg_s" not in data:
                data["m_dot_hot_kg_s"] = data["mass_flow_rate_kg_s"]
            if "m_dot_cold_kg_s" not in data:
                data["m_dot_cold_kg_s"] = data["mass_flow_rate_kg_s"]

        return data

    @property
    def channel_geometry(self) -> DuctCrossSectionEnum:
        return self.duct_type


class TPL09Params(BaseModel):
    """TPL-09: Radiative-convective exchange."""
    template_id: Literal[TemplateEnum.TPL_09, "TPL_09"] = TemplateEnum.TPL_09
    surface_emissivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Longwave infrared emissivity")
    emissivity_thermal: float = Field(default=0.90, ge=0.0, le=1.0, description="Thermal IR emissivity")
    solar_absorptivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Solar absorptivity")
    absorptivity_solar: float = Field(default=0.10, ge=0.0, le=1.0, description="Solar absorptivity")
    h_conv_ambient_W_m2K: Optional[float] = Field(default=None, gt=0.0, description="Convective coefficient in W/(m^2*K)")
    h_conv_W_m2K: float = Field(default=8.0, gt=0.0, description="Convective coefficient in W/(m^2*K)")
    t_ambient_K: Optional[float] = Field(default=None, gt=0.0, description="Ambient air temperature in K")
    T_ambient_degC: float = Field(default=25.0, description="Ambient air temperature in degC")
    t_sky_K: Optional[float] = Field(default=None, gt=0.0, description="Sky temperature in K")
    T_sky_degC: float = Field(default=10.0, description="Equivalent sky temperature in degC")
    q_solar_W_m2: Optional[float] = Field(default=None, ge=0.0, description="Solar irradiance in W/m^2")
    solar_irradiance_W_m2: float = Field(default=0.0, ge=0.0, description="Incident solar irradiance in W/m^2")
    thickness_m: Optional[float] = Field(default=None, gt=0.0, description="Substrate thickness in meters")
    substrate_thickness_m: float = Field(default=0.02, gt=0.0, description="Substrate thickness in meters")
    thermal_conductivity_W_mK: Optional[float] = Field(default=None, gt=0.0, description="Substrate thermal conductivity in W/(m*K)")
    substrate_k_W_mK: float = Field(default=0.05, gt=0.0, description="Substrate thermal conductivity in W/(m*K)")
    substrate_density_kg_m3: float = Field(default=50.0, gt=0.0, description="Substrate density in kg/m^3")
    T_inner_degC: float = Field(default=22.0, description="Interior space temperature in degC")
    max_inner_leakage_W_m2: float = Field(default=50.0, gt=0.0, description="Maximum allowable conductive leakage to interior in W/m^2")
    required_net_cooling_W_m2: float = Field(default=0.0, ge=0.0, description="Required net cooling flux in W/m^2")

    @model_validator(mode="before")
    @classmethod
    def harmonize_fields(cls, data: dict):
        if not isinstance(data, dict):
            return data
        # Emissivity
        if "emissivity_thermal" in data and "surface_emissivity" not in data:
            data["surface_emissivity"] = data["emissivity_thermal"]
        elif "surface_emissivity" in data and "emissivity_thermal" not in data:
            data["emissivity_thermal"] = data["surface_emissivity"]

        # Solar absorptivity
        if "absorptivity_solar" in data and "solar_absorptivity" not in data:
            data["solar_absorptivity"] = data["absorptivity_solar"]
        elif "solar_absorptivity" in data and "absorptivity_solar" not in data:
            data["absorptivity_solar"] = data["solar_absorptivity"]

        # Convection
        if "h_conv_W_m2K" in data and "h_conv_ambient_W_m2K" not in data:
            data["h_conv_ambient_W_m2K"] = data["h_conv_W_m2K"]
        elif "h_conv_ambient_W_m2K" in data and "h_conv_W_m2K" not in data:
            data["h_conv_W_m2K"] = data["h_conv_ambient_W_m2K"]

        # Thickness
        if "substrate_thickness_m" in data and "thickness_m" not in data:
            data["thickness_m"] = data["substrate_thickness_m"]
        elif "thickness_m" in data and "substrate_thickness_m" not in data:
            data["substrate_thickness_m"] = data["thickness_m"]

        # Conductivity
        if "substrate_k_W_mK" in data and "thermal_conductivity_W_mK" not in data:
            data["thermal_conductivity_W_mK"] = data["substrate_k_W_mK"]
        elif "thermal_conductivity_W_mK" in data and "substrate_k_W_mK" not in data:
            data["substrate_k_W_mK"] = data["thermal_conductivity_W_mK"]

        # Solar irradiance
        if "solar_irradiance_W_m2" in data and "q_solar_W_m2" not in data:
            data["q_solar_W_m2"] = data["solar_irradiance_W_m2"]
        elif "q_solar_W_m2" in data and "solar_irradiance_W_m2" not in data:
            data["solar_irradiance_W_m2"] = data["q_solar_W_m2"]

        # Temperatures
        if "t_ambient_K" in data and "T_ambient_degC" not in data:
            data["T_ambient_degC"] = data["t_ambient_K"] - 273.15
        elif "T_ambient_degC" in data and "t_ambient_K" not in data:
            data["t_ambient_K"] = data["T_ambient_degC"] + 273.15

        if "t_sky_K" in data and "T_sky_degC" not in data:
            data["T_sky_degC"] = data["t_sky_K"] - 273.15
        elif "T_sky_degC" in data and "t_sky_K" not in data:
            data["t_sky_K"] = data["T_sky_degC"] + 273.15

        return data


class TPL10Params(BaseModel):
    """TPL-10: Fickian and Knudsen diffusion."""
    template_id: Literal[TemplateEnum.TPL_10, "TPL_10"] = TemplateEnum.TPL_10
    membrane_thickness_m: float = Field(..., gt=0.0, description="Membrane thickness in meters")
    porosity: float = Field(..., gt=0.0, lt=1.0, description="Membrane porosity")
    mean_pore_radius_m: Optional[float] = Field(default=None, description="Mean pore radius in meters")
    pore_diameter_m: float = Field(default=50e-9, gt=0.0, description="Mean pore diameter in meters")
    min_pore_diameter_m: float = Field(default=20e-9, gt=0.0, description="Minimum allowable pore diameter against fouling in meters")
    tortuosity: float = Field(default=2.0, ge=1.0, description="Pore tortuosity factor")
    species_diffusivity_m2_s: Optional[float] = Field(default=None, description="Bulk molecular diffusivity in m^2/s")
    molecular_diffusivity_m2_s: float = Field(default=2.0e-5, gt=0.0, description="Bulk molecular diffusivity in m^2/s")
    molecular_mass_kg_mol: Optional[float] = Field(default=None, description="Species molecular weight in kg/mol")
    molar_mass_kg_mol: float = Field(default=0.032, gt=0.0, description="Species molar mass in kg/mol")
    temperature_K: Optional[float] = Field(default=None, description="Temperature in Kelvin")
    temperature_degC: float = Field(default=25.0, description="Temperature in Celsius")
    delta_concentration_mol_m3: float = Field(default=5.0, gt=0.0, description="Concentration driving potential across membrane in mol/m^3")
    required_flux_mol_m2_s: float = Field(..., gt=0.0, description="Required target diffusion molar flux in mol/(m^2*s)")

    @model_validator(mode="before")
    @classmethod
    def harmonize_fields(cls, data: dict):
        if not isinstance(data, dict):
            return data
        if "pore_diameter_m" in data and "mean_pore_radius_m" not in data:
            data["mean_pore_radius_m"] = data["pore_diameter_m"] / 2.0
        elif "mean_pore_radius_m" in data and "pore_diameter_m" not in data:
            data["pore_diameter_m"] = data["mean_pore_radius_m"] * 2.0

        if "molecular_diffusivity_m2_s" in data and "species_diffusivity_m2_s" not in data:
            data["species_diffusivity_m2_s"] = data["molecular_diffusivity_m2_s"]
        elif "species_diffusivity_m2_s" in data and "molecular_diffusivity_m2_s" not in data:
            data["molecular_diffusivity_m2_s"] = data["species_diffusivity_m2_s"]

        if "molar_mass_kg_mol" in data and "molecular_mass_kg_mol" not in data:
            data["molecular_mass_kg_mol"] = data["molar_mass_kg_mol"]
        elif "molecular_mass_kg_mol" in data and "molar_mass_kg_mol" not in data:
            data["molar_mass_kg_mol"] = data["molecular_mass_kg_mol"]

        if "temperature_degC" in data and "temperature_K" not in data:
            data["temperature_K"] = data["temperature_degC"] + 273.15
        elif "temperature_K" in data and "temperature_degC" not in data:
            data["temperature_degC"] = data["temperature_K"] - 273.15

        return data


TemplateParameters = Annotated[
    Union[
        TPL01Params,
        TPL02Params,
        TPL03Params,
        TPL04Params,
        TPL05Params,
        TPL06Params,
        TPL07Params,
        TPL08Params,
        TPL09Params,
        TPL10Params,
    ],
    Field(discriminator="template_id"),
]
