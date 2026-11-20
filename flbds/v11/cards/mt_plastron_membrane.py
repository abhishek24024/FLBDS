"""MT_PLASTRON_MEMBRANE: wraps V10 F_MEM (TPL_10 plastron / hydrophobic porous gas membrane)."""

from __future__ import annotations

from flbds.v10.families import FAMILIES, MEMFamily

from ._v10wrap import convert, legacy_screen, params_from
from .base import ConstraintResult, PhysicsCard

_FAM = FAMILIES["F_MEM"]
assert isinstance(_FAM, MEMFamily)


def _screen(d: dict[str, float], e: dict[str, float]) -> tuple[list[ConstraintResult], list[str], dict[str, float]]:
    legacy_ok, raw = legacy_screen(_FAM, d, e)
    cons = convert(raw)
    df = _FAM._diff(_FAM.build_params(d, e))
    notes: list[str] = []
    if not legacy_ok and all(c.status == "PASS" for c in cons):
        notes.append("legacy screen_tpl10 check failed")
    return cons, notes, {"mass_fourier_number": df["fo"], "fickian_flux_mol_m2_s": df["j_screen"],
                         "coupled_flux_mol_m2_s": df["j_coupled"], "breakthrough_head_m": df["h_break"]}


CARD = PhysicsCard(
    id="MT_PLASTRON_MEMBRANE",
    domain="mass_transfer",
    title="Plastron-type hydrophobic porous gas-exchange membrane (O2, 25 degC)",
    principle=(
        "Gas flux through air-filled hydrophobic pores J = D_eff dC / L with Bosanquet D_eff = (eps/tau)/(1/D_m + 1/D_K), "
        "Knudsen D_K = (d/3) sqrt(8RT/(pi M)); Young-Laplace breakthrough head h = 4 gamma |cos theta| /(d rho g) "
        ">= hydrostatic head; pore diameter >= fouling minimum; mass Fourier number D_eff t/L^2 >= 1."
    ),
    bio_exemplars=["diving bell spider (Argyroneta aquatica) air bell", "Aphelocheirus aestivalis plastron",
                   "Salvinia molesta air-retaining hairs", "backswimmer Notonecta"],
    design_space=params_from(_FAM.design_space),
    env_space=params_from(_FAM.env_space),
    references=[
        "Thorpe W.H., Crisp D.J. (1947) Studies on plastron respiration, J. Exp. Biol. 24:227.",
        "Flynn M.R., Bush J.W.M. (2008) Underwater breathing: the mechanics of plastron respiration, J. Fluid Mech. 608:275.",
        "Cussler E.L. Diffusion: Mass Transfer in Fluid Systems (Bosanquet, Knudsen).",
        "flbds.physics.tpl10_diffusion; flbds.v10.families.MEMFamily.",
    ],
    _screen=_screen,
)
