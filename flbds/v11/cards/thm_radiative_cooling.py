"""THM_RADIATIVE_COOLING: wraps V10 F_RAD (TPL_09) and adds the inner-leakage check."""

from __future__ import annotations

from flbds.physics.tpl09_radiative import solve_quartic_surface_temperature
from flbds.v10.families import FAMILIES, RADFamily

from ._v10wrap import convert, legacy_screen, params_from
from .base import ConstraintResult, PhysicsCard, le

_FAM = FAMILIES["F_RAD"]
assert isinstance(_FAM, RADFamily)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    legacy_ok, raw = legacy_screen(_FAM, d, e)
    cons = convert(raw)
    notes: list[str] = []
    derived: dict[str, float] = {}
    try:
        t_s, q_rad, q_conv, q_leak = solve_quartic_surface_temperature(
            q_solar=e["solar_irradiance_W_m2"], alpha_solar=d["solar_absorptivity"],
            epsilon_surf=d["surface_emissivity"], epsilon_sky=d["surface_emissivity"],
            T_sky_K=e["T_sky_degC"] + 273.15, T_amb_K=e["T_ambient_degC"] + 273.15,
            h_conv=e["h_conv_W_m2K"], k_substrate=d["substrate_k_W_mK"],
            d_substrate=d["substrate_thickness_m"], T_inner_K=e["T_inner_degC"] + 273.15)
        cons.append(le("inner_leakage_W_m2", q_leak, e["max_inner_leakage_W_m2"], "W/m2"))
        derived.update(surface_temp_degC=t_s - 273.15, q_rad_net_W_m2=q_rad, q_conv_W_m2=q_conv,
                       inner_leakage_W_m2=q_leak)
    except Exception as exc:  # noqa: BLE001 - root solver failure => validity violation
        notes.append(f"surface energy balance solver failed: {exc}")
    if e["T_sky_degC"] >= e["T_ambient_degC"]:
        notes.append("effective sky temperature not below ambient: no radiative sink")
    if not legacy_ok and all(c.status == "PASS" for c in cons):
        notes.append("legacy screen_tpl09 check failed")
    return cons, notes, derived


CARD = PhysicsCard(
    id="THM_RADIATIVE_COOLING",
    domain="thermal",
    title="Passive daytime radiative cooling roof skin",
    principle=(
        "Lumped net cooling P_net = eps sigma (T_amb^4 - T_sky^4) - alpha_s G >= required (TPL_09 screen). "
        "Surface equilibrium eps sigma (T_s^4 - T_sky^4) + h (T_s - T_amb) + (k/d)(T_s - T_in) = alpha_s G "
        "solved for T_s; inner leakage q = (k/d)(T_s - T_in) <= cap. Substrate thickness and areal mass <= caps."
    ),
    bio_exemplars=["Saharan silver ant (Cataglyphis bombycina) triangular hairs", "white beetle Cyphochilus scales",
                   "longicorn beetle Neocerambyx gigas hairs"],
    design_space=params_from(_FAM.design_space),
    env_space=params_from(_FAM.env_space, {"T_sky_degC": (-30.0, 30.0), "T_inner_degC": (10.0, 45.0)}),
    references=[
        "Raman A.P. et al. (2014) Passive radiative cooling below ambient air temperature under direct sunlight, Nature 515:540.",
        "Shi N.N. et al. (2015) Keeping cool: enhanced optical reflection and radiative heat dissipation in Saharan silver ants, Science 349:298.",
        "Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, ch. 12.",
        "flbds.physics.tpl09_radiative; flbds.v10.families.RADFamily.",
    ],
    _screen=_screen,
)
