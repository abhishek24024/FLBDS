"""THM_PCM_STORAGE: wraps V10 F_PCM (TPL_02 phase-change thermal buffer)."""

from __future__ import annotations

from flbds.v10.families import FAMILIES, PCM_SOLVER_FO_MAX, PCMFamily

from ._v10wrap import convert, legacy_screen, params_from
from .base import ConstraintResult, PhysicsCard

_FAM = FAMILIES["F_PCM"]
assert isinstance(_FAM, PCMFamily)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    legacy_ok, raw = legacy_screen(_FAM, d, e)
    fo = next(c["achieved"] for c in raw if c["name"] == "effective_fourier_number")
    cons = convert(raw, drop=("eval_model_validity_fourier_number",))
    notes: list[str] = []
    if not (fo <= PCM_SOLVER_FO_MAX):
        notes.append(f"Fourier number Fo={fo:.3g} > {PCM_SOLVER_FO_MAX:.0f}: outside TPL_02 enthalpy-model validity")
    if not legacy_ok and all(c.status == "PASS" for c in cons):
        notes.append("legacy screen_tpl02 lumped check failed")
    p = _FAM.build_params(d, e)
    cf = _FAM._closed_forms(p)
    return cons, notes, {"fourier_number": fo, "melt_front_depth_m": cf["x_melt"],
                         "latent_capacity_J_m2": cf["latent_capacity"], "areal_mass_kg_m2": cf["mass"]}


CARD = PhysicsCard(
    id="THM_PCM_STORAGE",
    domain="thermal",
    title="Phase-change thermal buffer layer (latent heat storage, melt point 28 degC)",
    principle=(
        "A layer of thickness d of PCM (+ optional conductive matrix) absorbs a constant flux q for t hours. "
        "Latent capacity rho_eff*L_eff*d >= required energy q*t; melt-front depth x = q t/(rho L); closed-form "
        "surface superheat dT = q x / k_eff (quasi-steady Stefan/Neumann limit) <= limit; areal mass rho_eff*d <= cap. "
        "Validity: effective Fourier number Fo = alpha t / d^2 in [0.8, 135] (lumped and solver-validity window)."
    ),
    bio_exemplars=[
        "honeybee nest thermoregulation (wax/honey thermal mass; analogy is thermal buffering, not true PCM)",
        "termite mound thermal mass (sensible, not latent; weak analogy)",
        "camel diurnal heat storage in body mass (sensible heat buffering)",
    ],
    design_space=params_from(_FAM.design_space),
    env_space=params_from(_FAM.env_space, {"required_energy_J_m2": (3.0e5, 1.0e7)}),
    references=[
        "Mehling H., Cabeza L.F. (2008) Heat and Cold Storage with PCM, Springer.",
        "Alexiades V., Solomon A.D. (1993) Mathematical Modeling of Melting and Freezing Processes.",
        "flbds.physics.tpl02_pcm (screen_tpl02, compute_composite_properties); flbds.v10.families.PCMFamily.",
    ],
    _screen=_screen,
)
