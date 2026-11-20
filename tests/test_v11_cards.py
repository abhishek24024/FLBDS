"""Tests for V11 physics cards, problem library and certification output."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from flbds.v11.cards import CARDS, DesignSchemaError, EnvSchemaError
from flbds.v11.cards.fld_riblet_drag import drag_reduction_pct
from flbds.v11.cards.opt_bragg_structural_color import peak_reflectance, peak_wavelength
from flbds.v11.problems import PROBLEMS, PROBLEMS_BY_ID

FEAS = json.loads(
    (Path(__file__).parents[1] / "flbds/v11/problem_feasibility.json").read_text()
)
CERTIFIED = [
    (row["problem_id"], r["card_id"], r["best_design"])
    for row in FEAS["problems"]
    for r in row["results"]
    if r["feasible"]
]
DOMAINS = {
    "thermal",
    "fluids",
    "structures",
    "adhesion",
    "wetting",
    "optics",
    "mass_transfer",
}


def _env(pid: str) -> dict[str, float]:
    return PROBLEMS_BY_ID[pid].env


def _first(card_id: str) -> tuple[str, dict[str, float]]:
    pid, _, d = next(x for x in CERTIFIED if x[1] == card_id)
    return pid, dict(d)


def test_registry_contract() -> None:
    assert len(CARDS) == 11
    for cid, c in CARDS.items():
        assert c.id == cid and c.domain in DOMAINS
        assert c.references and c.bio_exemplars and c.design_space and c.env_space
        for p in c.design_space:
            assert p.lo < p.hi, (cid, p.name)


def test_problem_library_shape() -> None:
    assert 20 <= len(PROBLEMS) <= 32
    for dom in DOMAINS:
        assert sum(p.domain == dom for p in PROBLEMS) >= 2, dom
    assert sum(len(p.plausible_cards) >= 2 for p in PROBLEMS) >= 6
    for p in PROBLEMS:
        for cid in p.plausible_cards:
            missing = {q.name for q in CARDS[cid].env_space} - set(p.env)
            assert not missing, (p.id, cid, missing)


def test_every_problem_has_a_feasible_card() -> None:
    assert all(row["feasible_cards"] for row in FEAS["problems"])


@pytest.mark.parametrize(
    ("pid", "cid", "design"), CERTIFIED, ids=[f"{a}-{b}" for a, b, _ in CERTIFIED]
)
def test_certified_design_passes(pid: str, cid: str, design: dict[str, float]) -> None:
    res = CARDS[cid].screen(design, _env(pid))
    assert (
        res.passed
        and res.regime_ok
        and all(c.status == "PASS" for c in res.constraints)
    )


@pytest.mark.parametrize("cid", sorted(CARDS))
def test_missing_or_out_of_bounds_design_raises(cid: str) -> None:
    card = CARDS[cid]
    pid, d = _first(cid)
    first = card.design_space[0]
    with pytest.raises(DesignSchemaError):
        card.screen({k: v for k, v in d.items() if k != first.name}, _env(pid))
    with pytest.raises(DesignSchemaError):
        card.screen({**d, first.name: first.hi * 10 + 1.0}, _env(pid))
    env = dict(_env(pid))
    env.pop(card.env_space[0].name)
    with pytest.raises(EnvSchemaError):
        card.screen(d, env)


@pytest.mark.parametrize("cid", sorted(CARDS))
def test_some_bounds_corner_fails(cid: str) -> None:
    card = CARDS[cid]
    pid, _ = _first(cid)
    lo = {p.name: p.lo for p in card.design_space}
    hi = {p.name: p.hi for p in card.design_space}
    assert not (card.screen(lo, _env(pid)).passed and card.screen(hi, _env(pid)).passed)


def test_honeycomb_stiffness_rises_with_face_thickness() -> None:
    card = CARDS["STR_SANDWICH_HONEYCOMB"]
    pid, d = _first(card.id)
    ks = [
        card.screen({**d, "face_thickness_m": t}, _env(pid)).derived["stiffness_N_m"]
        for t in (2e-4, 5e-4, 1e-3)
    ]
    assert ks[0] < ks[1] < ks[2]


def test_honeycomb_thin_core_fails_stiffness() -> None:
    card = CARDS["STR_SANDWICH_HONEYCOMB"]
    pid, d = _first(card.id)
    res = card.screen(
        {**d, "core_thickness_m": 2e-3, "face_thickness_m": 1e-4}, _env(pid)
    )
    assert not res.passed
    assert (
        next(c for c in res.constraints if c.name == "bending_stiffness_N_m").status
        == "MISS"
    )


def test_lattice_stretch_stiffer_than_bending() -> None:
    card = CARDS["STR_LATTICE_TRUSS"]
    pid, d = _first(card.id)
    s = card.screen({**d, "nodal_connectivity": 12.0}, _env(pid)).derived[
        "core_shear_modulus_Pa"
    ]
    b = card.screen({**d, "nodal_connectivity": 8.0}, _env(pid)).derived[
        "core_shear_modulus_Pa"
    ]
    assert s > b


def test_riblet_peak_near_s_plus_15_and_increase_beyond_30() -> None:
    sp = [x * 0.5 for x in range(2, 80)]
    best = max(sp, key=lambda s: drag_reduction_pct(s, 0.5))
    assert 13.0 <= best <= 17.0
    assert 7.0 <= drag_reduction_pct(best, 0.5) <= 10.0
    assert drag_reduction_pct(30.0, 0.5) < 0.0
    assert drag_reduction_pct(1.0, 0.5) < drag_reduction_pct(8.0, 0.5)


def test_riblet_regime_flag_laminar() -> None:
    card = CARDS["FLD_RIBLET_DRAG"]
    pid, d = _first(card.id)
    env = {**_env(pid), "flow_velocity_m_s": 1.0, "reference_length_m": 0.1}
    res = card.screen(d, env)
    assert not res.regime_ok and not res.passed


def test_bragg_peak_shifts_with_thickness_and_reflectance_with_pairs() -> None:
    assert peak_wavelength(2.4, 60e-9, 1.46, 90e-9) < peak_wavelength(
        2.4, 70e-9, 1.46, 90e-9
    )
    assert peak_wavelength(1.5, 100e-9, 1.0, 150e-9) == pytest.approx(600e-9)
    r = [peak_reflectance(2.4, 1.46, n, 1.0, 1.5) for n in (1, 3, 6)]
    assert r[0] < r[1] < r[2] < 1.0


def test_bragg_regime_flag_non_quarter_wave() -> None:
    card = CARDS["OPT_BRAGG_STRUCTURAL_COLOR"]
    pid, d = _first(card.id)
    res = card.screen(
        {
            **d,
            "thickness_layer1_m": 3 * d["thickness_layer1_m"]
            if d["thickness_layer1_m"] < 1.6e-7
            else 2e-8,
        },
        _env(pid),
    )
    assert not res.regime_ok


def test_adhesion_contact_splitting_scaling() -> None:
    card = CARDS["ADH_FIBRILLAR"]
    pid, d = _first(card.id)
    a = d["fibril_radius_m"]
    big = card.screen({**d, "fibril_radius_m": min(2 * a, 5e-5)}, _env(pid)).derived
    small = card.screen(d, _env(pid)).derived
    assert small["contact_splitting_pressure_Pa"] > big["contact_splitting_pressure_Pa"]


def test_adhesion_aspect_ratio_regime() -> None:
    card = CARDS["ADH_FIBRILLAR"]
    pid, d = _first(card.id)
    res = card.screen(
        {**d, "fibril_length_m": min(2e-3, 100 * d["fibril_radius_m"])}, _env(pid)
    )
    assert not res.regime_ok


def test_superhydrophobic_cassie_limits_and_hydrophilic_flag() -> None:
    card = CARDS["WET_SUPERHYDROPHOBIC"]
    pid, d = _first(card.id)
    sparse = card.screen(
        {**d, "pillar_pitch_m": min(5e-4, 1.5 * d["pillar_pitch_m"])}, _env(pid)
    )
    dense = card.screen(d, _env(pid))
    ang = lambda r: next(
        c.achieved for c in r.constraints if c.name == "cassie_apparent_angle_deg"
    )
    assert ang(sparse) > ang(dense)
    res = card.screen({**d, "intrinsic_contact_angle_deg": 80.0}, _env(pid))
    assert not res.regime_ok and not res.passed


def test_fog_yield_scales_with_area_and_smaller_fibres_deposit_better() -> None:
    card = CARDS["MT_FOG_HARVEST_MESH"]
    pid, d = _first(card.id)
    e = _env(pid)
    y1 = card.screen({**d, "mesh_area_m2": 10.0}, e).constraints[0].achieved
    y2 = card.screen({**d, "mesh_area_m2": 20.0}, e).constraints[0].achieved
    assert y2 == pytest.approx(2 * y1)
    fine = card.screen({**d, "fibre_radius_m": 1e-4}, e).derived["eta_deposition"]
    coarse = card.screen({**d, "fibre_radius_m": 1e-3}, e).derived["eta_deposition"]
    assert fine > coarse


def test_radiative_checks_both_net_cooling_and_leakage() -> None:
    card = CARDS["THM_RADIATIVE_COOLING"]
    pid, d = _first(card.id)
    names = {c.name for c in card.screen(d, _env(pid)).constraints}
    assert {"lumped_net_radiative_cooling_W_m2", "inner_leakage_W_m2"} <= names
    hot = card.screen({**d, "solar_absorptivity": 0.9}, _env(pid))
    assert not hot.passed


def test_pcm_fourier_validity_rule() -> None:
    card = CARDS["THM_PCM_STORAGE"]
    pid, d = _first(card.id)
    res = card.screen({**d, "thickness_m": 0.003, "k_eff_W_mK": 15.0}, _env(pid))
    assert res.derived["fourier_number"] > 135.0
    assert not res.regime_ok and not res.passed
    assert math.isfinite(res.min_margin)
