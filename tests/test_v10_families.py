"""Tests for flbds.v10.families: parameter construction, screen, hidden eval."""

from __future__ import annotations

import json

import numpy as np
import pytest

from flbds.v10.families import FAMILIES, get_family

FAMILY_NAMES = ["F_PCM", "F_HX", "F_RAD", "F_MEM"]


def test_four_families_registered() -> None:
    assert sorted(FAMILIES) == sorted(FAMILY_NAMES)


@pytest.mark.parametrize("fname", FAMILY_NAMES)
def test_build_params_sets_every_field_explicitly(fname: str) -> None:
    fam = get_family(fname)
    rng = np.random.default_rng(0)
    env = fam.sample_env(rng)
    design = fam.random_design(rng)
    params = fam.build_params(design, env)
    missing = set(type(params).model_fields) - set(params.model_fields_set)
    assert not missing, f"fields left to schema defaults: {missing}"


@pytest.mark.parametrize("fname", FAMILY_NAMES)
def test_env_overrides_model_output(fname: str) -> None:
    fam = get_family(fname)
    rng = np.random.default_rng(1)
    env = fam.sample_env(rng)
    design = fam.random_design(rng)
    # A malicious/confused model tries to set environment fields in its design dict.
    poisoned = dict(design)
    for k in env:
        poisoned[k] = 12345.678
    params = fam.build_params(poisoned, env)
    dumped = params.model_dump()
    for k, v in env.items():
        if k in dumped and isinstance(v, (int, float)):
            assert dumped[k] == pytest.approx(v), k


@pytest.mark.parametrize("fname", FAMILY_NAMES)
def test_screen_output_has_no_template_leak(fname: str) -> None:
    fam = get_family(fname)
    rng = np.random.default_rng(2)
    env = fam.sample_env(rng)
    for _ in range(20):
        design = fam.random_design(rng)
        passed, constraints, reason = fam.screen(design, env)
        text = json.dumps(constraints) + reason
        assert "TPL_" not in text
        assert "acceptable" not in text.lower()
        for c in constraints:
            assert set(c) >= {
                "name",
                "achieved",
                "limit",
                "margin_normalised",
                "status",
            }


@pytest.mark.parametrize("fname", FAMILY_NAMES)
def test_screen_verdict_matches_margins(fname: str) -> None:
    """Screen pass (verdict from the existing screen functions) iff all margins >= 0."""
    fam = get_family(fname)
    rng = np.random.default_rng(3)
    n_pass = 0
    for i in range(300):
        env = fam.sample_env(rng)
        design = fam.random_design(rng)
        passed, constraints, _ = fam.screen(design, env)
        all_ok = all(c["margin_normalised"] >= 0 for c in constraints)
        assert passed == all_ok, (i, constraints)
        n_pass += passed
    assert n_pass >= 0


@pytest.mark.parametrize("fname", ["F_HX", "F_RAD", "F_MEM"])
def test_hidden_eval_verdict_matches_margins(fname: str) -> None:
    fam = get_family(fname)
    rng = np.random.default_rng(4)
    for _ in range(200):
        env = fam.sample_env(rng)
        design = fam.random_design(rng)
        passed, margins, _ = fam.hidden_eval(design, env)
        if margins:
            assert passed == (min(margins.values()) >= 0), margins


def test_pcm_hidden_eval_known_design() -> None:
    fam = get_family("F_PCM")
    env = {
        "required_energy_J_m2": 4.0e6,
        "heat_flux_W_m2": 150.0,
        "charge_hours": 8.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 45.0,
        "superheat_limit_K": 10.0,
    }
    design = {
        "thickness_m": 0.03,
        "k_eff_W_mK": 1.0,
        "matrix_volume_fraction": 0.0,
        "matrix_density_kg_m3": 2700.0,
        "matrix_specific_heat_J_kgK": 900.0,
        "pcm_density_kg_m3": 1450.0,
        "pcm_latent_heat_J_kg": 190000.0,
        "pcm_specific_heat_J_kgK": 2000.0,
    }
    passed, margins, reason = fam.hidden_eval(design, env)
    assert passed, reason
    assert margins["surface_superheat_K"] > 0


def test_pcm_unstable_solver_regime_is_rejected() -> None:
    """eval_tpl02's explicit solver is unstable for Fo_eff > 135 (N floor 10 + 30000-step clamp)."""
    fam = get_family("F_PCM")
    env = {
        "required_energy_J_m2": 3.0e6,
        "heat_flux_W_m2": 120.0,
        "charge_hours": 8.0,
        "thickness_max_m": 0.05,
        "mass_cap_kg_m2": 60.0,
        "superheat_limit_K": 10.0,
    }
    design = {
        "thickness_m": 0.023,
        "k_eff_W_mK": 14.6,
        "matrix_volume_fraction": 0.28,
        "matrix_density_kg_m3": 3420.0,
        "matrix_specific_heat_J_kgK": 850.0,
        "pcm_density_kg_m3": 1222.0,
        "pcm_latent_heat_J_kg": 194000.0,
        "pcm_specific_heat_J_kgK": 2657.0,
    }
    passed, margins, reason = fam.hidden_eval(design, env)
    assert not passed
    assert margins["eval_model_validity_fourier_number"] < 0
    s_passed, cons, _ = fam.screen(design, env)
    assert not s_passed
    assert any(c["name"] == "eval_model_validity_fourier_number" and c["status"] == "MISS" for c in cons)


def test_pcm_hidden_eval_never_passes_non_finite() -> None:
    import math

    fam = get_family("F_PCM")
    rng = np.random.default_rng(11)
    for _ in range(60):
        env = fam.sample_env(rng)
        d = fam.random_design(rng)
        d["thickness_m"] = env["thickness_max_m"] * 0.9  # reach the solver
        passed, margins, _ = fam.hidden_eval(d, env)
        if passed:
            assert all(math.isfinite(v) for v in margins.values())
