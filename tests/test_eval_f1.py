"""Unit tests for scripts/eval_f1.py on synthetic card inputs."""

import pytest
from scripts.eval_f1 import token_f1, quantity_match, evaluate_quantities, evaluate_card_pair, evaluate_corpus


def test_token_f1_exact():
    p, r, f1 = token_f1("latent heat of vaporization", "latent heat of vaporization")
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0


def test_token_f1_partial():
    p, r, f1 = token_f1("evaporation cooling", "evaporative cooling process")
    # "cooling" is shared (1 token). Pred has 2 tokens -> p=0.5. Gold has 3 tokens -> r=1/3.
    assert p == 0.5
    assert abs(r - (1/3)) < 1e-4
    expected_f1 = 2 * (0.5 * (1/3)) / (0.5 + (1/3))
    assert abs(f1 - expected_f1) < 1e-4


def test_token_f1_disjoint():
    p, r, f1 = token_f1("fourier conduction", "darcy fluid flow")
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_quantity_match_unit_conversion():
    # 2500 J / g equals 2500000 J / kg within 10%
    pred = {"name": "latent_heat", "value": 2500.0, "unit": "kJ / kg"}
    gold = {"name": "latent_heat", "value": 2.5e6, "unit": "J / kg"}
    assert quantity_match(pred, gold, val_tol=0.01) is True


def test_quantity_match_mismatched_dimension():
    # Temperature vs Length cannot be converted
    pred = {"name": "temp", "value": 300.0, "unit": "kelvin"}
    gold = {"name": "temp", "value": 300.0, "unit": "meter"}
    assert quantity_match(pred, gold) is False


def test_synthetic_card_pair_evaluation():
    synthetic_card_a = {
        "card_id": "SYNTH-01",
        "action": {"verb": "dissipate", "object": "heat"},
        "state_change": {"state_variable": "temperature", "from_value": "40 C", "to_value": "30 C"},
        "phenomenon": {"description": "sweat evaporation from moist skin"},
        "effect": {"canonical_name": "latent_heat_of_vaporization"},
        "quantities": [
            {"name": "heat_flux", "value": 150.0, "unit": "W / m^2"}
        ],
    }

    # Identical card -> macro_f1 = 1.0
    res_perfect = evaluate_card_pair(synthetic_card_a, synthetic_card_a)
    assert res_perfect["effect_exact_match"] == 1.0
    assert res_perfect["effect_f1"] == 1.0
    assert res_perfect["macro_f1"] == 1.0

    # Perturbed card -> partial F1
    synthetic_card_b = {
        "card_id": "SYNTH-01",
        "action": {"verb": "insulate", "object": "temperature"},
        "state_change": {"state_variable": "heat_flux", "from_value": "", "to_value": ""},
        "phenomenon": {"description": "aerogel boundary layer"},
        "effect": {"canonical_name": "fourier_thermal_conduction"},
        "quantities": [],
    }
    res_partial = evaluate_card_pair(synthetic_card_a, synthetic_card_b)
    assert res_partial["effect_exact_match"] == 0.0
    assert res_partial["macro_f1"] < 0.5


def test_synthetic_corpus_evaluation():
    gold = [{"card_id": "C1", "effect": {"canonical_name": "darcy_flow"}}]
    pred = [{"card_id": "C1", "effect": {"canonical_name": "darcy_flow"}}]
    eval_res = evaluate_corpus(pred, gold)
    assert eval_res["evaluated_pairs"] == 1
    assert eval_res["mean_effect_exact_match"] == 1.0
