#!/usr/bin/env python3
"""scripts/test_screen_feedback.py
Tests the real M5-Screen loop and prints 5 representative feedback messages across different templates and constraints.
"""

from pathlib import Path
from flbds.schema.templates import TPL02Params, TPL08Params, TPL09Params, TPL10Params
from flbds.schema.problem_card import ProblemCard
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.enums import DuctCrossSectionEnum
from flbds.physics.screen import evaluate_m5_screen

def main():
    dev_base = Path("flbds/benchmark/dev")

    examples = [
        # 1. DEV-M1-S2 with insufficient thickness -> Latent capacity failure
        (
            "DEV-M1-S2",
            TPL02Params(
                template_id="TPL_02",
                thickness_m=0.005,  # 5 mm (insufficient latent capacity)
                pcm_density_kg_m3=820.0,
                pcm_latent_heat_J_kg=210000.0,
                pcm_specific_heat_J_kgK=2000.0,
                matrix_volume_fraction=0.05,
                matrix_density_kg_m3=2700.0,
                matrix_specific_heat_J_kgK=900.0,
                k_eff_W_mK=8.0,
                melting_temp_degC=25.0,
                superheat_limit_K=10.0,
                heat_flux_W_m2=200.0,
                charge_hours=8.0,
                required_energy_J_m2=5.76e6,
            ),
            "TPL-02 Latent Capacity Failure",
        ),
        # 2. DEV-M1-S2 with excessive thickness -> Hard constraint max_thickness_m failure
        (
            "DEV-M1-S2",
            TPL02Params(
                template_id="TPL_02",
                thickness_m=0.080,  # 80 mm (exceeds 50 mm card cap)
                pcm_density_kg_m3=820.0,
                pcm_latent_heat_J_kg=210000.0,
                pcm_specific_heat_J_kgK=2000.0,
                matrix_volume_fraction=0.05,
                matrix_density_kg_m3=2700.0,
                matrix_specific_heat_J_kgK=900.0,
                k_eff_W_mK=8.0,
                melting_temp_degC=25.0,
                superheat_limit_K=10.0,
                heat_flux_W_m2=200.0,
                charge_hours=8.0,
                required_energy_J_m2=5.76e6,
            ),
            "TPL-02 Thickness Cap Hard Constraint Failure",
        ),
        # 3. DEV-M2-S3 with excessive flow -> Closed-form duct pressure drop failure
        (
            "DEV-M2-S3",
            TPL08Params(
                template_id="TPL_08",
                length_m=0.5,
                hydraulic_diameter_m=0.005,  # small diameter -> high pressure drop
                heat_transfer_area_m2=1.0,
                overall_U_W_m2K=800.0,
                m_dot_hot_kg_s=0.2,
                cp_hot_J_kgK=4184.0,
                m_dot_cold_kg_s=0.2,
                cp_cold_J_kgK=4184.0,
                fluid_density_kg_m3=1000.0,
                fluid_viscosity_Pa_s=0.001,
                T_hot_in_degC=45.0,
                T_cold_in_degC=15.0,
                required_duty_W=800.0,
                max_pressure_drop_Pa=250.0,
                duct_type=DuctCrossSectionEnum.CIRCULAR,
                wall_conductivity_W_mK=200.0,
                wall_cross_section_m2=0.001,
            ),
            "TPL-08 Pressure Drop Cap Hard Constraint Failure",
        ),
        # 4. DEV-M3-S1 with low emissivity / high solar absorption -> Net radiation cooling failure
        (
            "DEV-M3-S1",
            TPL09Params(
                template_id="TPL_09",
                substrate_thickness_m=0.010,
                substrate_density_kg_m3=1200.0,
                substrate_k_W_mK=0.2,
                absorptivity_solar=0.6,  # 60% absorption of 850 W/m2 -> positive heat gain
                emissivity_thermal=0.5,
                solar_irradiance_W_m2=850.0,
                T_ambient_degC=45.0,
                T_sky_degC=15.0,
                T_inner_degC=40.0,
                h_conv_ambient_W_m2K=8.0,
                required_net_cooling_W_m2=10.0,
            ),
            "TPL-09 Lumped Net Radiation Failure",
        ),
        # 5. DEV-M4-S1 with large pore diameter -> Capillary breakthrough failure
        (
            "DEV-M4-S1",
            TPL10Params(
                template_id="TPL_10",
                membrane_thickness_m=0.0001,
                porosity=0.7,
                tortuosity=1.5,
                pore_diameter_m=2000e-9,  # 2000 nm (2 um) -> breakthrough head < 10 m
                min_pore_diameter_m=20e-9,
                molecular_diffusivity_m2_s=2.0e-5,
                molar_mass_kg_mol=0.032,
                temperature_degC=25.0,
                delta_concentration_mol_m3=5.0,
                required_flux_mol_m2_s=0.005,
                hydrostatic_head_m=10.0,
            ),
            "TPL-10 Laplace Capillary Breakthrough Failure",
        ),
    ]

    print("=" * 80)
    print("M5-SCREEN TIER: 5 REPRESENTATIVE FEEDBACK MESSAGES")
    print("=" * 80)

    for i, (cid, p_obj, label) in enumerate(examples, 1):
        with open(dev_base / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        with open(dev_base / cid / "ground_truth_eval.json") as f:
            gt = GroundTruthEval.model_validate_json(f.read())

        passed, ftype, reason, metrics = evaluate_m5_screen(prob, gt, p_obj, cid=cid)

        feedback_msg = (
            f"M5-Screen Physical Evaluation Result:\n"
            f"VERDICT: {'PASS' if passed else 'FAIL'}\n"
            f"FAILURE TYPE: {ftype}\n"
            f"PHYSICAL REASON: {reason}\n"
            f"RELEVANT METRICS: {metrics}"
        )

        print(f"\n--- Feedback Message {i}: {label} ({cid}) ---")
        print(feedback_msg)

if __name__ == "__main__":
    main()
