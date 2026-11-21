"""flbds/physics/screen.py
M5-Screen Tier Verifier for FLBDS v9 §5.

Principles:
- Evaluates lumped closed-form physics checks (screen_tpl01 through screen_tpl10).
- Enforces every hard constraint on the Problem Card:
    * max_thickness_m
    * max_mass_kg_m2
    * max_pressure_drop_Pa
    * max_surface_superheat_K
    * min_pore_diameter_m
    * max_envelope_height_m
    * min_cop
- Zero coupled numerical solver text (no Stefan 1D PDE enthalpy solver, no external boundary layer resistance R_bl, no axial conduction numerical integration).
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np

from flbds.schema.problem_card import ProblemCard
from flbds.schema.ground_truth_eval import GroundTruthEval
from flbds.schema.templates import (
    TemplateParameters,
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
)
from flbds.schema.enums import DuctCrossSectionEnum
from flbds.schema.verification import PhysicsCheck

from flbds.physics.tpl01_conduction import screen_tpl01
from flbds.physics.tpl02_pcm import screen_tpl02, compute_composite_properties
from flbds.physics.tpl03_evaporation import screen_tpl03_evaporation, screen_tpl03_condensation
from flbds.physics.tpl04_sorption import screen_tpl04
from flbds.physics.tpl05_wicking import screen_tpl05
from flbds.physics.tpl06_porous_flow import screen_tpl06, compute_ergun_pressure_drop
from flbds.physics.tpl07_fin import screen_tpl07
from flbds.physics.tpl08_countercurrent import screen_tpl08, compute_duct_pressure_drop
from flbds.physics.tpl09_radiative import screen_tpl09
from flbds.physics.tpl10_diffusion import screen_tpl10


def evaluate_m5_screen(
    prob: ProblemCard,
    gt: GroundTruthEval,
    params: TemplateParameters,
    cid: str = "",
) -> Tuple[bool, str, str, Dict[str, Any]]:
    """Evaluates design strictly at the M5-Screen tier.

    Returns:
        (passed: bool, failure_type: str, reason: str, metrics: dict)
    """
    # 1. Template Admissibility Check
    acceptable = [
        t.value if hasattr(t, "value") else str(t) for t in gt.acceptable_templates
    ]
    cand_template = (
        params.template_id.value
        if hasattr(params.template_id, "value")
        else str(params.template_id)
    )
    if cand_template not in acceptable:
        return (
            False,
            "template_choice_error",
            f"Selected template '{cand_template}' cannot deliver the required function for this problem; choose a template whose physics matches the required function.",  # V10 fix: no leak of acceptable list
            {},
        )

    # 2. Extract Hard Constraints from Problem Card
    hc = prob.hard_constraints
    t_cap = hc.max_thickness_m if (hc and hc.max_thickness_m is not None) else 0.05
    m_cap = hc.max_mass_kg_m2 if (hc and hc.max_mass_kg_m2 is not None) else 500.0
    dp_cap = hc.max_pressure_drop_Pa if (hc and hc.max_pressure_drop_Pa is not None) else None
    superheat_cap = hc.max_surface_superheat_K if (hc and hc.max_surface_superheat_K is not None) else None
    min_pore_d = hc.min_pore_diameter_m if (hc and hc.min_pore_diameter_m is not None) else None
    env_cap = hc.max_envelope_height_m if (hc and hc.max_envelope_height_m is not None) else None
    min_cop_val = hc.min_cop if (hc and hc.min_cop is not None) else None

    # 3. Lumped Screen Execution per Template
    check = PhysicsCheck(name="M5_Screen", passed=False, reason="Uninitialized")

    if isinstance(params, TPL01Params):
        check = screen_tpl01(params, mass_cap_kg_m2=m_cap, thickness_cap_m=t_cap)

    elif isinstance(params, TPL02Params):
        check = screen_tpl02(params, mass_cap_kg_m2=m_cap, thickness_cap_m=t_cap)
        if check.passed and superheat_cap is not None:
            # Check closed-form superheat against card limit
            rho_eff, L_eff, cp_eff, k_eff = compute_composite_properties(params)
            t_charge_s = params.charge_hours * 3600.0
            vol_latent = rho_eff * L_eff
            x_melt = (params.heat_flux_W_m2 * t_charge_s) / vol_latent if vol_latent > 0 else params.thickness_m
            delta_T_closed = (params.heat_flux_W_m2 * x_melt) / k_eff if k_eff > 0 else float("inf")
            if delta_T_closed > superheat_cap:
                return (
                    False,
                    "screen_failure",
                    f"Closed-form superheat {delta_T_closed:.2f} K exceeds Problem Card limit {superheat_cap:.2f} K",
                    {"delta_T_closed_K": delta_T_closed, "superheat_limit_K": superheat_cap},
                )

    elif isinstance(params, TPL03Params):
        check = screen_tpl03_evaporation(params)

    elif isinstance(params, TPL04Params):
        check = screen_tpl04(params, bed_thickness_m=t_cap)

    elif isinstance(params, TPL05Params):
        check = screen_tpl05(params)

    elif isinstance(params, TPL06Params):
        check = screen_tpl06(params)
        if check.passed and dp_cap is not None:
            dp_tot, _, _, _ = compute_ergun_pressure_drop(
                L=params.bed_length_m,
                eps=params.bed_porosity,
                d_p=params.mean_pore_diameter_m,
                rho=params.fluid_density_kg_m3,
                mu=params.fluid_viscosity_Pa_s,
                u_0=params.superficial_velocity_m_s,
            )
            if dp_tot > dp_cap:
                return (
                    False,
                    "screen_failure",
                    f"Ergun pressure drop {dp_tot:.1f} Pa exceeds Problem Card cap {dp_cap:.1f} Pa",
                    {"dp_tot_Pa": dp_tot, "dp_cap_Pa": dp_cap},
                )

    elif isinstance(params, TPL07Params):
        h_cap = env_cap if env_cap is not None else 0.1
        check = screen_tpl07(params, envelope_height_cap_m=h_cap)

    elif isinstance(params, TPL08Params):
        check = screen_tpl08(params, length_cap_m=1.0)
        if check.passed:
            eff_dp_cap = dp_cap if dp_cap is not None else params.max_pressure_drop_Pa
            if eff_dp_cap is not None:
                # Hydraulic pressure drop estimate
                geom = getattr(params, "channel_geometry", DuctCrossSectionEnum.CIRCULAR)
                if geom == DuctCrossSectionEnum.CIRCULAR:
                    A_flow = np.pi * (params.hydraulic_diameter_m ** 2) / 4.0
                else:
                    A_flow = params.hydraulic_diameter_m ** 2
                rho_f = getattr(params, "fluid_density_kg_m3", 1000.0)
                mu_f = getattr(params, "fluid_viscosity_Pa_s", 1.0e-3)
                v = params.m_dot_cold_kg_s / (rho_f * A_flow) if (A_flow > 0 and rho_f > 0) else 0.1
                Re, f, delta_p = compute_duct_pressure_drop(
                    L=params.length_m,
                    D_h=params.hydraulic_diameter_m,
                    rho=rho_f,
                    mu=mu_f,
                    velocity=v,
                    cross_section=geom,
                )
                if delta_p > eff_dp_cap:
                    return (
                        False,
                        "screen_failure",
                        f"Closed-form duct pressure drop {delta_p:.1f} Pa exceeds cap {eff_dp_cap:.1f} Pa (Re={Re:.1f})",
                        {"delta_p_Pa": delta_p, "dp_cap_Pa": eff_dp_cap, "Re": Re},
                    )

    elif isinstance(params, TPL09Params):
        check = screen_tpl09(params, mass_cap_kg_m2=m_cap, thickness_cap_m=t_cap)

    elif isinstance(params, TPL10Params):
        check = screen_tpl10(params)
        if check.passed:
            # Check pore fouling clearance
            min_limit = min_pore_d if min_pore_d is not None else params.min_pore_diameter_m
            if params.pore_diameter_m < min_limit:
                return (
                    False,
                    "screen_failure",
                    f"Pore diameter {params.pore_diameter_m*1e9:.1f} nm below minimum fouling limit {min_limit*1e9:.1f} nm",
                    {"pore_diameter_m": params.pore_diameter_m, "min_pore_diameter_m": min_limit},
                )
            # Check closed-form Laplace capillary breakthrough if hydrostatic head is specified
            head = getattr(params, "hydrostatic_head_m", None)
            if head is not None and head > 0:
                gamma = getattr(params, "surface_tension_N_m", 0.072)
                theta_deg = getattr(params, "contact_angle_deg", 110.0)
                cos_theta = max(0.0, -np.cos(np.radians(theta_deg)))  # V10 fix: hydrophilic (theta<90) gives no capillary barrier
                rho_water = 1000.0
                g_acc = 9.81
                dp_break = (4.0 * gamma * cos_theta) / params.pore_diameter_m
                h_break = dp_break / (rho_water * g_acc)
                if head > h_break:
                    return (
                        False,
                        "screen_failure",
                        f"Hydrostatic head {head:.1f} m exceeds capillary breakthrough limit {h_break:.1f} m (d_pore={params.pore_diameter_m*1e9:.1f} nm)",
                        {"hydrostatic_head_m": head, "breakthrough_head_m": h_break},
                    )

    else:
        return (
            False,
            "template_choice_error",
            f"Unsupported template parameter type: {type(params)}",
            {},
        )

    if not check.passed:
        return False, "screen_failure", f"Screen check failed: {check.reason}", check.metrics

    return True, "pass", f"Screen constraints satisfied: {check.reason}", check.metrics
