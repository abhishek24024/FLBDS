"""TPL-06: Darcy-Forchheimer Porous Media Flow Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5:
- Screen: Darcy linear viscous pressure drop; pore Reynolds number Re_pore <= 10.
- Eval: Ergun equation (coupled viscous Blake-Kozeny plus inertial Forchheimer terms);
  pumping coefficient of performance (COP_pumping >= min_cop).
"""

from typing import Dict, Tuple
from flbds.schema.templates import TPL06Params
from flbds.schema.verification import PhysicsCheck


def compute_ergun_pressure_drop(
    L: float,
    eps: float,
    d_p: float,
    rho: float,
    mu: float,
    u_0: float,
) -> Tuple[float, float, float, float]:
    """Computes viscous, inertial, and total pressure drop via the classic Ergun equation.

    delta_P / L = 150 * (mu * (1 - eps)^2) / (eps^3 * d_p^2) * u_0
                + 1.75 * (rho * (1 - eps)) / (eps^3 * d_p) * u_0^2

    Returns:
        (delta_P_total, delta_P_viscous, delta_P_inertial, Re_pore)
    """
    if eps <= 0 or eps >= 1 or d_p <= 0 or L <= 0:
        return float("inf"), float("inf"), float("inf"), float("inf")

    term_visc = 150.0 * (mu * ((1.0 - eps) ** 2)) / ((eps ** 3) * (d_p ** 2)) * u_0
    term_inert = 1.75 * (rho * (1.0 - eps)) / ((eps ** 3) * d_p) * (u_0 ** 2)

    dp_visc = float(term_visc * L)
    dp_inert = float(term_inert * L)
    dp_total = dp_visc + dp_inert

    Re_pore = float((rho * u_0 * d_p) / (mu * (1.0 - eps))) if (mu * (1.0 - eps)) > 0 else 0.0

    return dp_total, dp_visc, dp_inert, Re_pore


def screen_tpl06(
    params: TPL06Params,
) -> PhysicsCheck:
    """M5-Screen: Darcy linear drop and pore Reynolds number <= 10."""
    dp_total, dp_visc, dp_inert, re_pore = compute_ergun_pressure_drop(
        L=params.bed_length_m,
        eps=params.bed_porosity,
        d_p=params.mean_pore_diameter_m,
        rho=params.fluid_density_kg_m3,
        mu=params.fluid_viscosity_Pa_s,
        u_0=params.superficial_velocity_m_s,
    )

    if re_pore > 10.0:
        return PhysicsCheck(
            template_name="TPL06_M5_Screen",
            passed=False,
            reason=f"Pore Reynolds number Re_p={re_pore:.2f} > 10.0 (inertial Forchheimer effects violate Darcy regime)",
            metrics={"Re_pore": re_pore, "dp_darcy_Pa": dp_visc},
        )

    if dp_visc > params.pressure_drop_cap_Pa:
        return PhysicsCheck(
            template_name="TPL06_M5_Screen",
            passed=False,
            reason=f"Darcy pressure drop {dp_visc:.1f} Pa exceeds cap {params.pressure_drop_cap_Pa:.1f} Pa",
            metrics={"dp_visc_Pa": dp_visc, "cap_Pa": params.pressure_drop_cap_Pa},
        )

    return PhysicsCheck(
        template_name="TPL06_M5_Screen",
        passed=True,
        reason=f"Screen Darcy flow satisfied (Re_p={re_pore:.2f}, dp={dp_visc:.1f} Pa)",
        metrics={"dp_visc_Pa": dp_visc, "Re_pore": re_pore},
    )


def eval_tpl06(
    params: TPL06Params,
    thermal_duty_W: float = 1000.0,
    bed_cross_section_m2: float = 0.04,  # 0.2m x 0.2m
) -> PhysicsCheck:
    """M5-Eval: Coupled Ergun pressure drop and thermal-to-pumping COP."""
    dp_total, dp_visc, dp_inert, re_pore = compute_ergun_pressure_drop(
        L=params.bed_length_m,
        eps=params.bed_porosity,
        d_p=params.mean_pore_diameter_m,
        rho=params.fluid_density_kg_m3,
        mu=params.fluid_viscosity_Pa_s,
        u_0=params.superficial_velocity_m_s,
    )

    # 1. Total Ergun drop within cap
    if dp_total > params.pressure_drop_cap_Pa:
        return PhysicsCheck(
            template_name="TPL06_M5_Eval",
            passed=False,
            reason=(
                f"Total Ergun pressure drop {dp_total:.1f} Pa (viscous: {dp_visc:.1f} Pa, "
                f"inertial: {dp_inert:.1f} Pa) exceeds cap {params.pressure_drop_cap_Pa:.1f} Pa"
            ),
            metrics={"dp_total_Pa": dp_total, "dp_visc_Pa": dp_visc, "dp_inert_Pa": dp_inert, "Re_p": re_pore},
        )

    # 2. Pumping power & COP check: W_pump = V_dot * delta_P
    v_dot = params.superficial_velocity_m_s * bed_cross_section_m2
    w_pumping = dp_total * v_dot
    pumping_cop = thermal_duty_W / w_pumping if w_pumping > 0 else float("inf")

    if pumping_cop < params.min_pumping_cop:
        return PhysicsCheck(
            template_name="TPL06_M5_Eval",
            passed=False,
            reason=f"Pumping COP {pumping_cop:.2f} below minimum {params.min_pumping_cop:.2f} (excess parasitic pumping power {w_pumping:.1f} W)",
            metrics={"COP": pumping_cop, "w_pumping_W": w_pumping, "thermal_duty_W": thermal_duty_W},
        )

    return PhysicsCheck(
        template_name="TPL06_M5_Eval",
        passed=True,
        reason=f"Coupled Ergun flow verified: dp={dp_total:.1f} Pa <= cap, pumping COP={pumping_cop:.1f} >= min",
        metrics={"dp_total_Pa": dp_total, "COP": pumping_cop, "Re_pore": re_pore, "w_pumping_W": w_pumping},
    )
