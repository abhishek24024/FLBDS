"""TPL-08: Countercurrent Heat Exchanger Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5, §4.3:
- Screen: epsilon-NTU thermal duty vs required heat transfer rate; length cap.
- Eval: Axial conduction degradation (Kroeger / Incropera correlation);
  hydraulic pressure drop using Poiseuille number from DuctCrossSectionEnum;
  pumping pressure drop constraint check.
"""

from typing import Dict, Tuple
import numpy as np

from flbds.schema.enums import DuctCrossSectionEnum
from flbds.schema.templates import TPL08Params
from flbds.schema.verification import PhysicsCheck


def compute_countercurrent_ntu_effectiveness(
    NTU: float,
    Cr: float,
) -> float:
    """Computes countercurrent effectiveness epsilon given NTU and capacity ratio Cr = C_min / C_max.

    Textbook reference: Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, Eq 11.29-11.30.
    """
    if NTU <= 0.0:
        return 0.0
    if abs(Cr - 1.0) < 1e-5:
        return NTU / (1.0 + NTU)
    exp_term = np.exp(-NTU * (1.0 - Cr))
    return float((1.0 - exp_term) / (1.0 - Cr * exp_term))


def compute_axial_conduction_degradation(
    epsilon_ideal: float,
    Cr: float,
    lambda_axial: float,
) -> float:
    """Computes degraded effectiveness due to axial heat conduction along the wall.

    Reference: Kroeger (1967), Incropera & DeWitt / Kays & London.
    lambda_axial = (k_w * A_w) / (L * C_min)
    """
    if lambda_axial <= 0.0:
        return epsilon_ideal
    # Kroeger relation for axial conduction
    if abs(Cr - 1.0) < 1e-5:
        return epsilon_ideal / (1.0 + lambda_axial * epsilon_ideal)
    return float(epsilon_ideal / (1.0 + lambda_axial * epsilon_ideal * (1.0 - Cr)))


def compute_duct_pressure_drop(
    L: float,
    D_h: float,
    rho: float,
    mu: float,
    velocity: float,
    cross_section: DuctCrossSectionEnum,
) -> Tuple[float, float, float]:
    """Computes laminar/turbulent friction factor and pressure drop across duct geometry.

    Returns:
        (Re, friction_factor, delta_p_Pa)
    """
    Re = (rho * velocity * D_h) / mu if mu > 0 else 1.0
    po_number = cross_section.poiseuille_number

    if Re < 2300:  # Laminar regime
        f = po_number / Re
    else:  # Turbulent regime (Blasius or Petukhov)
        f = 0.3164 * (Re ** -0.25)

    delta_p = f * (L / D_h) * 0.5 * rho * (velocity ** 2)
    return float(Re), float(f), float(delta_p)


def screen_tpl08(
    params: TPL08Params,
    length_cap_m: float = 1.0,
) -> PhysicsCheck:
    """M5-Screen: Lumped epsilon-NTU duty and length cap."""
    if params.length_m > length_cap_m:
        return PhysicsCheck(
            name="TPL08_M5_Screen",
            passed=False,
            reason=f"Exchanger length {params.length_m:.3f} m exceeds cap {length_cap_m:.3f} m",
            metrics={"length_m": params.length_m, "length_cap_m": length_cap_m},
        )

    C_hot = params.m_dot_hot_kg_s * params.cp_hot_J_kgK
    C_cold = params.m_dot_cold_kg_s * params.cp_cold_J_kgK

    C_min = min(C_hot, C_cold)
    C_max = max(C_hot, C_cold)
    Cr = C_min / C_max if C_max > 0 else 1.0

    UA = params.overall_U_W_m2K * params.heat_transfer_area_m2
    NTU = UA / C_min if C_min > 0 else 0.0

    epsilon = compute_countercurrent_ntu_effectiveness(NTU, Cr)
    q_max = C_min * (params.T_hot_in_degC - params.T_cold_in_degC)
    q_actual = epsilon * q_max

    if q_actual < params.required_duty_W:
        return PhysicsCheck(
            name="TPL08_M5_Screen",
            passed=False,
            reason=f"Thermal duty {q_actual:.1f} W below required {params.required_duty_W:.1f} W (epsilon={epsilon:.3f})",
            metrics={"duty_W": q_actual, "required_duty_W": params.required_duty_W, "epsilon": epsilon, "NTU": NTU},
        )

    return PhysicsCheck(
        name="TPL08_M5_Screen",
        passed=True,
        reason="Screen thermal duty and length cap satisfied",
        metrics={"duty_W": q_actual, "epsilon": epsilon, "NTU": NTU, "Cr": Cr},
    )


def eval_tpl08(
    params: TPL08Params,
    length_cap_m: float = 1.0,
    mu_fluid: float = 1.0e-3,  # Pa.s (water default)
    rho_fluid: float = 1000.0,  # kg/m3
) -> PhysicsCheck:
    """M5-Eval: Coupled verification with axial conduction degradation and hydraulic pressure drop."""
    # 1. Check length
    if params.length_m > length_cap_m:
        return PhysicsCheck(
            name="TPL08_M5_Eval",
            passed=False,
            reason=f"Length {params.length_m:.3f} m exceeds cap {length_cap_m:.3f} m",
            metrics={"length_m": params.length_m},
        )

    C_hot = params.m_dot_hot_kg_s * params.cp_hot_J_kgK
    C_cold = params.m_dot_cold_kg_s * params.cp_cold_J_kgK
    C_min = min(C_hot, C_cold)
    C_max = max(C_hot, C_cold)
    Cr = C_min / C_max if C_max > 0 else 1.0

    UA = params.overall_U_W_m2K * params.heat_transfer_area_m2
    NTU = UA / C_min if C_min > 0 else 0.0
    epsilon_ideal = compute_countercurrent_ntu_effectiveness(NTU, Cr)

    # 2. Axial conduction degradation
    # lambda = (k_wall * A_wall) / (L * C_min)
    lambda_axial = (params.wall_conductivity_W_mK * params.wall_cross_section_m2) / (params.length_m * C_min)
    epsilon_degraded = compute_axial_conduction_degradation(epsilon_ideal, Cr, lambda_axial)

    q_max = C_min * (params.T_hot_in_degC - params.T_cold_in_degC)
    q_actual = epsilon_degraded * q_max

    if q_actual < params.required_duty_W:
        return PhysicsCheck(
            name="TPL08_M5_Eval",
            passed=False,
            reason=(
                f"Degraded duty {q_actual:.1f} W below required {params.required_duty_W:.1f} W "
                f"(ideal eps={epsilon_ideal:.3f} degraded to {epsilon_degraded:.3f} by axial cond lambda={lambda_axial:.4f})"
            ),
            metrics={"duty_W": q_actual, "epsilon_degraded": epsilon_degraded, "lambda_axial": lambda_axial},
        )

    # 3. Hydraulic pressure drop check
    # Estimate fluid velocity: m_dot / (rho * A_flow)
    # If hydraulic diameter and area given
    A_flow = (np.pi * (params.hydraulic_diameter_m ** 2) / 4.0) if params.channel_geometry == DuctCrossSectionEnum.CIRCULAR else (params.hydraulic_diameter_m ** 2)
    velocity = params.m_dot_cold_kg_s / (rho_fluid * A_flow) if A_flow > 0 else 0.1

    Re, f, delta_p = compute_duct_pressure_drop(
        L=params.length_m,
        D_h=params.hydraulic_diameter_m,
        rho=rho_fluid,
        mu=mu_fluid,
        velocity=velocity,
        cross_section=params.channel_geometry,
    )

    if delta_p > params.max_pressure_drop_Pa:
        return PhysicsCheck(
            name="TPL08_M5_Eval",
            passed=False,
            reason=f"Pressure drop {delta_p:.1f} Pa exceeds maximum allowance {params.max_pressure_drop_Pa:.1f} Pa (Re={Re:.1f})",
            metrics={"delta_p_Pa": delta_p, "max_delta_p_Pa": params.max_pressure_drop_Pa, "Re": Re, "f": f},
        )

    return PhysicsCheck(
        name="TPL08_M5_Eval",
        passed=True,
        reason="Coupled countercurrent effectiveness, axial conduction, and pressure drop satisfied",
        metrics={
            "duty_W": q_actual,
            "epsilon_ideal": epsilon_ideal,
            "epsilon_degraded": epsilon_degraded,
            "lambda_axial": lambda_axial,
            "delta_p_Pa": delta_p,
            "Re": Re,
        },
    )
