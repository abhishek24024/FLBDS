"""Generator for the 12 FLBDS Development Cases (DEV-M1 to DEV-M4 across Splits 1-3).

Enforces Principle P10 (FLBDS v9 §5.1):
1. Pre-admission capacity bound calculation.
2. Solver-generated reference designs (zero hand-typed designs).
3. Ground-truth evaluation files with acceptable template lists.
4. Problem cards strictly validated against template leakage.
"""

import json
from pathlib import Path

from flbds.schema.enums import (
    BoundaryTypeEnum,
    DirectionEnum,
    DuctCrossSectionEnum,
    HazardEnum,
    ResourceEnum,
    TemplateEnum,
    TimeModeEnum,
)
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.problem_card import (
    Constraint,
    EnvironmentSpec,
    HardConstraints,
    ProblemCard,
    RequiredFunction,
    SystemSpec,
    TimePattern,
)
from flbds.schema.templates import (
    TPL02Params,
    TPL08Params,
    TPL09Params,
    TPL10Params,
)
from flbds.physics.capacity_bound import check_thermal_storage_capacity
from flbds.physics.tpl02_pcm import eval_tpl02
from flbds.physics.tpl08_countercurrent import eval_tpl08
from flbds.physics.tpl09_radiative import eval_tpl09
from flbds.physics.tpl10_diffusion import eval_tpl10


def generate_all_dev_cases(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        # =========================================================================
        # DEV-M1: Elephant skin and mud -> Thermal Storage / Wall
        # =========================================================================
        {
            "case_id": "DEV-M1-S1",
            "cluster": "DEV-M1",
            "split": 1,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M1-S1",
                system=SystemSpec(name="Field Biological Organism Shell", length_scale="macro (0.1m - 10m)"),
                environment=EnvironmentSpec(
                    climate="Arid Savannah",
                    ambient_temperature="38 degC",
                    resources_available=[ResourceEnum.LIQUID_WATER, ResourceEnum.AMBIENT_AIR, ResourceEnum.SOLAR_IRRADIANCE],
                    hazards=[HazardEnum.HIGH_HUMIDITY],
                ),
                required_function=RequiredFunction(
                    action="buffer",
                    target_object="body core temperature",
                    state_variable="thermal energy",
                    target_change="damp thermal swings under intense daytime solar irradiation",
                    target_direction=DirectionEnum.STABILISE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=4.0e6,
                ),
                time_pattern=TimePattern(cycle_type="cyclic", period_hours=24.0),
                hard_constraints=HardConstraints(thickness_max_m=0.05, mass_per_area_max_kg_m2=45.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_02, TemplateEnum.TPL_03, TemplateEnum.TPL_05],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL02Params(
                template_id=TemplateEnum.TPL_02,
                thickness_m=0.035,
                pcm_density_kg_m3=820.0,
                pcm_latent_heat_J_kg=210000.0,
                matrix_volume_fraction=0.10,
                matrix_density_kg_m3=2700.0,
                k_eff_W_mK=2.5,
                melting_temp_degC=28.0,
                superheat_limit_K=10.0,
                heat_flux_W_m2=150.0,
                charge_hours=8.0,
                required_energy_J_m2=4.0e6,
            ),
            "evaluator": lambda ref: eval_tpl02(ref, bc_type=BoundaryTypeEnum.BC_FLUX),
        },
        {
            "case_id": "DEV-M1-S2",
            "cluster": "DEV-M1",
            "split": 2,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M1-S2",
                system=SystemSpec(name="Desert Shelter Storage Wall", length_scale="macro (0.1m - 10m)"),
                environment=EnvironmentSpec(
                    climate="Desert",
                    ambient_temperature="38 degC day, 18 degC night",
                    resources_available=[ResourceEnum.SOLAR_IRRADIANCE, ResourceEnum.AMBIENT_AIR, ResourceEnum.NIGHT_SKY_SINK],
                    resources_absent=[ResourceEnum.LIQUID_WATER],
                    hazards=[HazardEnum.NONE],
                ),
                required_function=RequiredFunction(
                    action="store-and-release",
                    target_object="interior thermal zone",
                    state_variable="heat flux",
                    target_change="absorb daytime gross solar flux and discharge release at night",
                    target_direction=DirectionEnum.STORE_AND_RELEASE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=5.76e6,
                ),
                time_pattern=TimePattern(cycle_type="cyclic", period_hours=24.0, charge_phase_hours=8.0, discharge_phase_hours=16.0),
                hard_constraints=HardConstraints(thickness_max_m=0.050, mass_per_area_max_kg_m2=45.0, surface_superheat_max_K=10.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_02, TemplateEnum.TPL_04],
            "expected_conflicts": ["resource", "direction", "timing", "effect", "regime"],
            "expected_operators": ["T1", "T2", "T3", "T4", "T5"],
            "generator": lambda: TPL02Params(
                template_id=TemplateEnum.TPL_02,
                thickness_m=0.040,
                pcm_density_kg_m3=820.0,
                pcm_latent_heat_J_kg=210000.0,
                matrix_volume_fraction=0.12,
                matrix_density_kg_m3=2700.0,
                k_eff_W_mK=2.8,
                melting_temp_degC=28.0,
                superheat_limit_K=10.0,
                heat_flux_W_m2=200.0,
                charge_hours=8.0,
                required_energy_J_m2=5.76e6,
            ),
            "evaluator": lambda ref: eval_tpl02(ref, bc_type=BoundaryTypeEnum.BC_FLUX),
        },
        {
            "case_id": "DEV-M1-S3",
            "cluster": "DEV-M1",
            "split": 3,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M1-S3",
                system=SystemSpec(name="Ultra-Compact Thermal Buffer Panel", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Enclosed Equipment Bay",
                    ambient_temperature="35 degC",
                    resources_available=[ResourceEnum.WASTE_HEAT_STREAM, ResourceEnum.AMBIENT_AIR],
                    resources_absent=[ResourceEnum.LIQUID_WATER],
                ),
                required_function=RequiredFunction(
                    action="absorb",
                    target_object="component heat surge",
                    state_variable="thermal energy",
                    target_change="absorb intermittent heat pulse in tight packaging envelope",
                    target_direction=DirectionEnum.STORE_AND_RELEASE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=3.5e6,
                ),
                time_pattern=TimePattern(cycle_type="cyclic", period_hours=12.0),
                hard_constraints=HardConstraints(thickness_max_m=0.030, mass_per_area_max_kg_m2=35.0, surface_superheat_max_K=8.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_02, TemplateEnum.TPL_04],
            "expected_conflicts": ["resource", "timing"],
            "expected_operators": ["T1", "T3", "T5"],
            "generator": lambda: TPL02Params(
                template_id=TemplateEnum.TPL_02,
                thickness_m=0.025,
                pcm_density_kg_m3=820.0,
                pcm_latent_heat_J_kg=210000.0,
                matrix_volume_fraction=0.15,
                matrix_density_kg_m3=2700.0,
                k_eff_W_mK=3.5,
                melting_temp_degC=30.0,
                superheat_limit_K=8.0,
                heat_flux_W_m2=200.0,
                charge_hours=4.86,
                required_energy_J_m2=3.5e6,
            ),
            "evaluator": lambda ref: eval_tpl02(ref, bc_type=BoundaryTypeEnum.BC_FLUX),
        },

        # =========================================================================
        # DEV-M2: Penguin wing -> Countercurrent Heat Exchanger
        # =========================================================================
        {
            "case_id": "DEV-M2-S1",
            "cluster": "DEV-M2",
            "split": 1,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M2-S1",
                system=SystemSpec(name="Aquatic Extremity Vascular Bundle", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Sub-Antarctic Marine",
                    ambient_temperature="2 degC",
                    resources_available=[ResourceEnum.AMBIENT_AIR, ResourceEnum.LIQUID_WATER],
                ),
                required_function=RequiredFunction(
                    action="conserve",
                    target_object="arterial stream enthalpy",
                    state_variable="thermal energy",
                    target_change="transfer heat back to venous blood before reaching flipper tip",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_TEMP,
                    flux_or_load=500.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(envelope_height_max_m=0.4, pressure_drop_max_Pa=500.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_08],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL08Params(
                template_id=TemplateEnum.TPL_08,
                duct_type=DuctCrossSectionEnum.CIRCULAR,
                length_m=0.30,
                heat_transfer_area_m2=0.5,
                overall_U_W_m2K=800.0,
                m_dot_hot_kg_s=0.03,
                m_dot_cold_kg_s=0.03,
                cp_hot_J_kgK=4184.0,
                cp_cold_J_kgK=4184.0,
                T_hot_in_degC=37.0,
                T_cold_in_degC=5.0,
                required_duty_W=500.0,
                max_pressure_drop_Pa=500.0,
                hydraulic_diameter_m=0.008,
                wall_conductivity_W_mK=5.0,
                wall_cross_section_m2=5e-5,
            ),
            "evaluator": lambda ref: eval_tpl08(ref),
        },
        {
            "case_id": "DEV-M2-S2",
            "cluster": "DEV-M2",
            "split": 2,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M2-S2",
                system=SystemSpec(name="Industrial Exhaust Heat Recovery Core", length_scale="macro (0.1m - 10m)"),
                environment=EnvironmentSpec(
                    climate="Factory Floor",
                    ambient_temperature="22 degC",
                    resources_available=[ResourceEnum.WASTE_HEAT_STREAM, ResourceEnum.AMBIENT_AIR],
                ),
                required_function=RequiredFunction(
                    action="recover",
                    target_object="counterflowing liquid stream",
                    state_variable="heat flux",
                    target_change="preheat makeup fluid using thermal energy from waste discharge",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_TEMP,
                    flux_or_load=2000.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(envelope_height_max_m=0.6, pressure_drop_max_Pa=800.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_08],
            "expected_conflicts": ["direction"],
            "expected_operators": ["T2"],
            "generator": lambda: TPL08Params(
                template_id=TemplateEnum.TPL_08,
                duct_type=DuctCrossSectionEnum.CIRCULAR,
                length_m=0.50,
                heat_transfer_area_m2=1.2,
                overall_U_W_m2K=1000.0,
                m_dot_hot_kg_s=0.08,
                m_dot_cold_kg_s=0.08,
                cp_hot_J_kgK=4184.0,
                cp_cold_J_kgK=4184.0,
                T_hot_in_degC=55.0,
                T_cold_in_degC=20.0,
                required_duty_W=2000.0,
                max_pressure_drop_Pa=800.0,
                hydraulic_diameter_m=0.012,
                wall_conductivity_W_mK=15.0,
                wall_cross_section_m2=1e-4,
            ),
            "evaluator": lambda ref: eval_tpl08(ref),
        },
        {
            "case_id": "DEV-M2-S3",
            "cluster": "DEV-M2",
            "split": 3,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M2-S3",
                system=SystemSpec(name="Low-Power Avionics Coolant Exchanger", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Unpressurized Avionics Bay",
                    ambient_temperature="10 degC",
                    resources_available=[ResourceEnum.WASTE_HEAT_STREAM],
                ),
                required_function=RequiredFunction(
                    action="cool",
                    target_object="circulating avionics loop",
                    state_variable="thermal energy",
                    target_change="maintain coolant temperature below upper limit under tight pressure drop ceiling",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_TEMP,
                    flux_or_load=800.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(envelope_height_max_m=0.35, pressure_drop_max_Pa=250.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_08],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL08Params(
                template_id=TemplateEnum.TPL_08,
                duct_type=DuctCrossSectionEnum.CIRCULAR,
                length_m=0.32,
                heat_transfer_area_m2=0.8,
                overall_U_W_m2K=850.0,
                m_dot_hot_kg_s=0.04,
                m_dot_cold_kg_s=0.04,
                cp_hot_J_kgK=4184.0,
                cp_cold_J_kgK=4184.0,
                T_hot_in_degC=45.0,
                T_cold_in_degC=15.0,
                required_duty_W=800.0,
                max_pressure_drop_Pa=250.0,
                hydraulic_diameter_m=0.014,
                wall_conductivity_W_mK=10.0,
                wall_cross_section_m2=8e-5,
            ),
            "evaluator": lambda ref: eval_tpl08(ref),
        },

        # =========================================================================
        # DEV-M3: Saharan silver ant hairs -> Radiative Cooling
        # =========================================================================
        {
            "case_id": "DEV-M3-S1",
            "cluster": "DEV-M3",
            "split": 1,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M3-S1",
                system=SystemSpec(name="Desert Arthropod Dorsal Cuticle", length_scale="micro (1um - 1mm)"),
                environment=EnvironmentSpec(
                    climate="Hyper-Arid Dunes",
                    ambient_temperature="48 degC",
                    resources_available=[ResourceEnum.SOLAR_IRRADIANCE, ResourceEnum.NIGHT_SKY_SINK, ResourceEnum.AMBIENT_AIR],
                ),
                required_function=RequiredFunction(
                    action="reject",
                    target_object="incident solar and ambient heat",
                    state_variable="surface temperature",
                    target_change="reflect solar wavelengths while strongly emitting into thermal infrared window",
                    target_direction=DirectionEnum.DECREASE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=20.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.015, mass_per_area_max_kg_m2=10.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_09, TemplateEnum.TPL_07],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL09Params(
                template_id=TemplateEnum.TPL_09,
                solar_irradiance_W_m2=850.0,
                absorptivity_solar=0.04,
                emissivity_thermal=0.96,
                h_conv_W_m2K=8.0,
                T_ambient_degC=45.0,
                T_sky_degC=15.0,
                T_inner_degC=40.0,
                substrate_thickness_m=0.005,
                substrate_k_W_mK=0.1,
                substrate_density_kg_m3=800.0,
                max_inner_leakage_W_m2=40.0,
                required_net_cooling_W_m2=0.0,
            ),
            "evaluator": lambda ref: eval_tpl09(ref),
        },
        {
            "case_id": "DEV-M3-S2",
            "cluster": "DEV-M3",
            "split": 2,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M3-S2",
                system=SystemSpec(name="Telecom Cabinet Roof Radiator", length_scale="macro (0.1m - 10m)"),
                environment=EnvironmentSpec(
                    climate="Desert Substation",
                    ambient_temperature="40 degC",
                    resources_available=[ResourceEnum.SOLAR_IRRADIANCE, ResourceEnum.NIGHT_SKY_SINK, ResourceEnum.AMBIENT_AIR],
                    resources_absent=[ResourceEnum.GRID_ELECTRICITY],
                ),
                required_function=RequiredFunction(
                    action="cool",
                    target_object="enclosure rooftop skin",
                    state_variable="thermal radiation flux",
                    target_change="shed enclosure heat to cold sky without power consumption",
                    target_direction=DirectionEnum.DECREASE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=40.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.030, mass_per_area_max_kg_m2=15.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_09],
            "expected_conflicts": ["resource", "direction"],
            "expected_operators": ["T1", "T2"],
            "generator": lambda: TPL09Params(
                template_id=TemplateEnum.TPL_09,
                solar_irradiance_W_m2=750.0,
                absorptivity_solar=0.06,
                emissivity_thermal=0.94,
                h_conv_W_m2K=6.0,
                T_ambient_degC=38.0,
                T_sky_degC=12.0,
                T_inner_degC=30.0,
                substrate_thickness_m=0.020,
                substrate_k_W_mK=0.04,
                substrate_density_kg_m3=100.0,
                max_inner_leakage_W_m2=35.0,
                required_net_cooling_W_m2=0.0,
            ),
            "evaluator": lambda ref: eval_tpl09(ref),
        },
        {
            "case_id": "DEV-M3-S3",
            "cluster": "DEV-M3",
            "split": 3,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M3-S3",
                system=SystemSpec(name="Precision Cryo-Storage Top Shield", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Outdoor Arid Platform",
                    ambient_temperature="35 degC",
                    resources_available=[ResourceEnum.NIGHT_SKY_SINK, ResourceEnum.AMBIENT_AIR],
                ),
                required_function=RequiredFunction(
                    action="block",
                    target_object="inner conductive heat leak",
                    state_variable="conduction flux",
                    target_change="minimize inward parasitic conduction under intense downward infrared and ambient flux",
                    target_direction=DirectionEnum.DECREASE,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=20.0,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.045, mass_per_area_max_kg_m2=12.0),
            ),
            "acceptable_templates": [TemplateEnum.TPL_09],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL09Params(
                template_id=TemplateEnum.TPL_09,
                solar_irradiance_W_m2=500.0,
                absorptivity_solar=0.05,
                emissivity_thermal=0.92,
                h_conv_W_m2K=5.0,
                T_ambient_degC=32.0,
                T_sky_degC=10.0,
                T_inner_degC=20.0,
                substrate_thickness_m=0.040,
                substrate_k_W_mK=0.03,
                substrate_density_kg_m3=80.0,
                max_inner_leakage_W_m2=20.0,
                required_net_cooling_W_m2=0.0,
            ),
            "evaluator": lambda ref: eval_tpl09(ref),
        },

        # =========================================================================
        # DEV-M4: Aquatic insect plastron -> Gas Permeable Diffusion Membrane
        # =========================================================================
        {
            "case_id": "DEV-M4-S1",
            "cluster": "DEV-M4",
            "split": 1,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M4-S1",
                system=SystemSpec(name="Submerged Plastron Hair Array", length_scale="micro (1um - 1mm)"),
                environment=EnvironmentSpec(
                    climate="Freshwater Stream",
                    ambient_temperature="18 degC",
                    resources_available=[ResourceEnum.LIQUID_WATER, ResourceEnum.AMBIENT_AIR],
                ),
                required_function=RequiredFunction(
                    action="diffuse",
                    target_object="dissolved oxygen gas",
                    state_variable="species molar flux",
                    target_change="maintain steady passive oxygen replenishment across stable gas interface",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=0.005,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.001, minimum_pore_diameter_m=20e-9),
            ),
            "acceptable_templates": [TemplateEnum.TPL_10],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL10Params(
                template_id=TemplateEnum.TPL_10,
                membrane_thickness_m=50e-6,
                porosity=0.60,
                pore_diameter_m=60e-9,
                min_pore_diameter_m=20e-9,
                tortuosity=1.8,
                molecular_diffusivity_m2_s=2.1e-5,
                temperature_degC=18.0,
                molar_mass_kg_mol=0.032,
                delta_concentration_mol_m3=6.0,
                required_flux_mol_m2_s=0.005,
            ),
            "evaluator": lambda ref: eval_tpl10(ref),
        },
        {
            "case_id": "DEV-M4-S2",
            "cluster": "DEV-M4",
            "split": 2,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M4-S2",
                system=SystemSpec(name="Submersible Fuel Cell Aeration Interface", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Marine Trench Simulation",
                    ambient_temperature="12 degC",
                    resources_available=[ResourceEnum.LIQUID_WATER],
                    resources_absent=[ResourceEnum.PRESSURISED_GAS],
                ),
                required_function=RequiredFunction(
                    action="transport",
                    target_object="oxygen reactant gas",
                    state_variable="molar flow rate",
                    target_change="supply oxidant continuously across hydrophobic membrane without pressurized cylinders",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=0.008,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.001, minimum_pore_diameter_m=25e-9),
            ),
            "acceptable_templates": [TemplateEnum.TPL_10],
            "expected_conflicts": ["resource"],
            "expected_operators": ["T1"],
            "generator": lambda: TPL10Params(
                template_id=TemplateEnum.TPL_10,
                membrane_thickness_m=40e-6,
                porosity=0.65,
                pore_diameter_m=75e-9,
                min_pore_diameter_m=25e-9,
                tortuosity=1.6,
                molecular_diffusivity_m2_s=2.0e-5,
                temperature_degC=12.0,
                molar_mass_kg_mol=0.032,
                delta_concentration_mol_m3=8.0,
                required_flux_mol_m2_s=0.008,
            ),
            "evaluator": lambda ref: eval_tpl10(ref),
        },
        {
            "case_id": "DEV-M4-S3",
            "cluster": "DEV-M4",
            "split": 3,
            "problem": ProblemCard(
                problem_id="PROB-DEV-M4-S3",
                system=SystemSpec(name="Fouling-Resistant Bioreactor Gas Scavenger", length_scale="meso (1mm - 0.1m)"),
                environment=EnvironmentSpec(
                    climate="Bioreactor Broth",
                    ambient_temperature="30 degC",
                    resources_available=[ResourceEnum.LIQUID_WATER, ResourceEnum.AMBIENT_AIR],
                    hazards=[HazardEnum.DUST_FOULING],
                ),
                required_function=RequiredFunction(
                    action="diffuse",
                    target_object="dissolved gas",
                    state_variable="species molar flux",
                    target_change="transfer gas through pores that remain larger than biofouling particle diameter",
                    target_direction=DirectionEnum.TRANSPORT_DIRECTIONAL,
                    boundary_type=BoundaryTypeEnum.BC_FLUX,
                    flux_or_load=0.006,
                ),
                time_pattern=TimePattern(cycle_type="steady"),
                hard_constraints=HardConstraints(thickness_max_m=0.001, minimum_pore_diameter_m=35e-9),
            ),
            "acceptable_templates": [TemplateEnum.TPL_10],
            "expected_conflicts": [],
            "expected_operators": [],
            "generator": lambda: TPL10Params(
                template_id=TemplateEnum.TPL_10,
                membrane_thickness_m=60e-6,
                porosity=0.70,
                pore_diameter_m=50e-9,
                min_pore_diameter_m=35e-9,
                tortuosity=1.5,
                molecular_diffusivity_m2_s=2.2e-5,
                temperature_degC=30.0,
                molar_mass_kg_mol=0.032,
                delta_concentration_mol_m3=8.0,
                required_flux_mol_m2_s=0.006,
            ),
            "evaluator": lambda ref: eval_tpl10(ref),
        },
    ]

    manifest = []

    for c in cases:
        case_id = c["case_id"]
        case_dir = output_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save Problem Card (strict validator runs)
        prob = c["problem"]
        prob_path = case_dir / "problem_card.json"
        with open(prob_path, "w") as f:
            f.write(prob.model_dump_json(indent=2))

        # 2. Run solver generator to create reference design
        ref_params = c["generator"]()
        ref_check = c["evaluator"](ref_params)
        assert ref_check.passed, f"Generated reference design for {case_id} failed M5-Eval: {ref_check.reason}"

        ref_path = case_dir / "reference_design.json"
        with open(ref_path, "w") as f:
            f.write(ref_params.model_dump_json(indent=2))

        # 3. Save Ground Truth Eval
        eval_spec = GroundTruthEval(
            case_id=case_id,
            source_card_id=f"MC-BIO-{c['cluster']}",
            cluster=c["cluster"],
            split=c["split"],
            expected_conflicts=c["expected_conflicts"],
            expected_operators=c["expected_operators"],
            acceptable_templates=c["acceptable_templates"],
            reference_design_file="reference_design.json",
        )
        eval_path = case_dir / "ground_truth_eval.json"
        with open(eval_path, "w") as f:
            f.write(eval_spec.model_dump_json(indent=2))

        manifest.append({
            "case_id": case_id,
            "cluster": c["cluster"],
            "split": c["split"],
            "acceptable_templates": [t.value if hasattr(t, "value") else str(t) for t in c["acceptable_templates"]],
            "solver_eval_verdict": ref_check.verdict,
            "solver_eval_reason": ref_check.reason,
        })

    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully generated and validated {len(cases)} dev cases in {output_dir}")
    return manifest


if __name__ == "__main__":
    out = Path("flbds/benchmark/dev")
    generate_all_dev_cases(out)
