"""TPL-07: Extended Surface Fin Convection Verifier.

Implements M5-Screen and M5-Eval per FLBDS v9 §5:
- Screen: Straight rectangular fin efficiency eta_f = tanh(m * L_c) / (m * L_c);
  Biot number Bi = h * (t_f / 2) / k < 0.1 (1D conduction assumption); envelope height cap.
- Eval: Boundary-layer choking check (fin spacing S >= 2 * delta_th) or Elenbaas channel correlation;
  coupled degraded thermal duty meets required heat rejection.
"""

from typing import Dict, Tuple
import numpy as np

from flbds.schema.templates import TPL07Params
from flbds.schema.verification import PhysicsCheck


def compute_constructal_spacing_m(fin_length_m: float, air_velocity_m_s: float = 2.0) -> float:
    """Computes Bejan constructal optimal/minimum fin spacing S_opt ~ 2 * delta_th."""
    nu_air = 1.5e-5
    Pr = 0.71
    delta_th = 5.0 * np.sqrt((nu_air * fin_length_m) / max(0.1, air_velocity_m_s)) / (Pr ** (1.0 / 3.0))
    return float(2.0 * delta_th)


def compute_fin_efficiency(h: float, k: float, t_f: float, L_f: float) -> Tuple[float, float, float]:
    """Computes fin parameter m, corrected length L_c, and efficiency eta_f for rectangular profile.

    m = sqrt(2 * h / (k * t_f))
    L_c = L_f + t_f / 2
    eta_f = tanh(m * L_c) / (m * L_c)
    """
    if k <= 0 or t_f <= 0 or L_f <= 0 or h <= 0:
        return 0.0, 0.0, 0.0

    m = np.sqrt(2.0 * h / (k * t_f))
    L_c = L_f + (t_f / 2.0)
    mLc = m * L_c
    eta_f = float(np.tanh(mLc) / mLc) if mLc > 0 else 1.0
    Bi = float((h * (t_f / 2.0)) / k)

    return float(m), float(eta_f), Bi


def screen_tpl07(
    params: TPL07Params,
    envelope_height_cap_m: float = 0.10,
) -> PhysicsCheck:
    """M5-Screen: Fin efficiency, Biot number < 0.1, envelope height cap."""
    if params.fin_length_m > envelope_height_cap_m:
        return PhysicsCheck(
            template_name="TPL07_M5_Screen",
            passed=False,
            reason=f"Fin length {params.fin_length_m*1e3:.1f} mm exceeds envelope cap {envelope_height_cap_m*1e3:.1f} mm",
            metrics={"fin_length_m": params.fin_length_m, "cap_m": envelope_height_cap_m},
        )

    m, eta_f, Bi = compute_fin_efficiency(
        h=params.h_conv_W_m2K,
        k=params.fin_conductivity_W_mK,
        t_f=params.fin_thickness_m,
        L_f=params.fin_length_m,
    )

    if Bi >= 0.1:
        return PhysicsCheck(
            template_name="TPL07_M5_Screen",
            passed=False,
            reason=f"Biot number Bi={Bi:.4f} >= 0.1 (violates 1D lumped-fin conduction assumption)",
            metrics={"Bi": Bi, "eta_f": eta_f},
        )

    return PhysicsCheck(
        template_name="TPL07_M5_Screen",
        passed=True,
        reason=f"Screen fin efficiency verified (eta_f={eta_f:.3f}, Bi={Bi:.4f})",
        metrics={"eta_f": eta_f, "Bi": Bi, "m_inv_m": m},
    )


def eval_tpl07(
    params: TPL07Params,
    base_excess_temp_K: float = 30.0,
    required_duty_W: float = 150.0,
    fin_width_m: float = 0.10,
    num_fins: int = 15,
    air_velocity_m_s: float = 2.0,
    envelope_height_cap_m: float = 0.10,
) -> PhysicsCheck:
    """M5-Eval: Coupled boundary-layer choking check and heat rejection duty."""
    # 1. Screen checks
    screen_res = screen_tpl07(params, envelope_height_cap_m=envelope_height_cap_m)
    if not screen_res.passed:
        return PhysicsCheck(
            template_name="TPL07_M5_Eval",
            passed=False,
            reason=f"Screen check failed: {screen_res.reason}",
            metrics=screen_res.metrics,
        )

    # 2. Boundary layer choking check (spacing >= 2 * delta_thermal)
    # Laminar boundary layer thickness along fin tip: delta_th ~ 5 * sqrt(nu * L / u) / Pr^(1/3)
    nu_air = 1.5e-5  # m2/s
    Pr = 0.71
    delta_th = 5.0 * np.sqrt((nu_air * params.fin_length_m) / max(0.1, air_velocity_m_s)) / (Pr ** (1.0 / 3.0))

    if params.fin_spacing_m < (2.0 * delta_th):
        return PhysicsCheck(
            template_name="TPL07_M5_Eval",
            passed=False,
            reason=(
                f"Fin spacing {params.fin_spacing_m*1e3:.2f} mm below 2*delta_th ({2*delta_th*1e3:.2f} mm) "
                f"(boundary layers merge, severely choking convective airflow)"
            ),
            metrics={"fin_spacing_mm": params.fin_spacing_m * 1e3, "2_delta_th_mm": 2 * delta_th * 1e3},
        )

    # 3. Heat dissipation duty
    m, eta_f, Bi = compute_fin_efficiency(
        h=params.h_conv_W_m2K,
        k=params.fin_conductivity_W_mK,
        t_f=params.fin_thickness_m,
        L_f=params.fin_length_m,
    )
    # Fin surface area: 2 * L_f * width per fin
    A_fin = 2.0 * params.fin_length_m * fin_width_m
    q_per_fin = eta_f * params.h_conv_W_m2K * A_fin * base_excess_temp_K
    q_total = num_fins * q_per_fin

    if q_total < required_duty_W:
        return PhysicsCheck(
            template_name="TPL07_M5_Eval",
            passed=False,
            reason=f"Total fin heat dissipation {q_total:.1f} W below required {required_duty_W:.1f} W",
            metrics={"q_total_W": q_total, "required_W": required_duty_W, "q_per_fin": q_per_fin},
        )

    return PhysicsCheck(
        template_name="TPL07_M5_Eval",
        passed=True,
        reason=f"Coupled fin convection verified: q={q_total:.1f} W >= required, spacing clear of boundary-layer choking",
        metrics={"q_total_W": q_total, "eta_f": eta_f, "spacing_clearance_mm": (params.fin_spacing_m - 2 * delta_th) * 1e3},
    )
