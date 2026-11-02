"""tests/test_conflict_detector.py
Unit tests for rule-based conflict detector (FLBDS v9 §4.4 and Audit Round 7 Prompt P5).
Tests all 12 dev cases:
- Split 1 cases MUST fire ZERO conflict flags.
- Prints which flags fire across all 12 dev cases.
- Tests that under proposed rewrites, Split 2 cases fire exactly their archetype conflict:
    M1-S2 -> T1 (Resource Absence)
    M2-S2 -> T3 (Temporal Phase Shift)
    M3-S2 -> T2 (Direction Inversion)
    M4-S2 -> T5 (Regime Re-scaling via characteristic_length comparison)
"""

import re
from pathlib import Path
import pytest

from flbds.schema.enums import DirectionEnum, ResourceEnum, TimeModeEnum
from flbds.schema.problem_card import ProblemCard

DEV_DIR = Path(__file__).resolve().parent.parent / "flbds" / "benchmark" / "dev"

SOURCE_CARDS = {
    "DEV-M1": {
        "card_id": "MC-BIO-DEV-M1",
        "name": "Elephant Mud-Wallowing Evaporative Storage",
        "consumable_inputs": ["liquid_water"],
        "target_direction": DirectionEnum.STORE_AND_RELEASE,
        "time_mode": TimeModeEnum.CYCLIC_DIURNAL,
        "regime_max_length_m": 0.05,
    },
    "DEV-M2": {
        "card_id": "MC-BIO-DEV-M2",
        "name": "Avian Appendicular Countercurrent Retia",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.TRANSPORT_DIRECTIONAL,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.10,
    },
    "DEV-M3": {
        "card_id": "MC-BIO-DEV-M3",
        "name": "Saharan Silver Ant Passive Radiative Rejection",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.DECREASE,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.02,
    },
    "DEV-M4": {
        "card_id": "MC-BIO-DEV-M4",
        "name": "Aphelocheirus Aestivalis Hydrophobic Plastron Gill",
        "consumable_inputs": [],
        "target_direction": DirectionEnum.TRANSPORT_DIRECTIONAL,
        "time_mode": TimeModeEnum.STEADY,
        "regime_max_length_m": 0.005,  # 5 mm biological gill
    },
}


def detect_conflicts(source_card: dict, prob: ProblemCard, proposed_char_length: float | None = None) -> list[str]:
    """Pure symbolic, rule-based conflict detector operating on ProblemCard enums and fields."""
    flags = []

    # 1. Operator T1: Resource Absence
    source_consumables = set(source_card.get("consumable_inputs", []))
    problem_absent = set(prob.environment.resources_absent)
    if source_consumables.intersection(problem_absent):
        flags.append("T1")

    # 2. Operator T2: Flow / Direction Inversion
    source_dir = source_card.get("target_direction")
    target_dir = prob.required_function.target_direction
    if (source_dir == DirectionEnum.DECREASE and target_dir == DirectionEnum.INCREASE) or \
       (source_dir == DirectionEnum.INCREASE and target_dir == DirectionEnum.DECREASE):
        flags.append("T2")

    # 3. Operator T3: Temporal Phase Shift
    source_time = source_card.get("time_mode")
    target_time = prob.time_pattern.time_mode
    if source_time in [TimeModeEnum.STEADY, TimeModeEnum.CONTINUOUS] and \
       target_time in [TimeModeEnum.CYCLIC_DIURNAL, TimeModeEnum.PULSED]:
        flags.append("T3")

    # 4. Operator T5: Regime Re-scaling
    # T5 compares the characteristic length with the source card's regime bounds
    source_max_L = source_card.get("regime_max_length_m", 0.005)
    target_L = proposed_char_length
    if target_L is None:
        target_L = getattr(prob.system, "characteristic_length_m", None)
    if target_L is None:
        for c in prob.constraints:
            if any(k in c.variable.lower() for k in ["characteristic_length", "device_length", "macro_scale", "envelope_length"]):
                m = re.search(r"(\d+(?:\.\d+)?)", c.bound)
                if m:
                    target_L = float(m.group(1))
                    break
    if target_L is not None and target_L > (5.0 * source_max_L):
        flags.append("T5")

    return flags


def test_detector_on_all_12_dev_cases():
    """Runs rule-based detector on all 12 dev cases and prints which flags fire.
    Confirms Split 1 cases fire NONE.
    """
    cases = [
        "DEV-M1-S1", "DEV-M1-S2", "DEV-M1-S3",
        "DEV-M2-S1", "DEV-M2-S2", "DEV-M2-S3",
        "DEV-M3-S1", "DEV-M3-S2", "DEV-M3-S3",
        "DEV-M4-S1", "DEV-M4-S2", "DEV-M4-S3",
    ]

    print("\n--- Conflict Flags on Current 12 Dev Cases ---")
    results = {}
    for cid in cases:
        cluster = cid[:6]
        source = SOURCE_CARDS[cluster]
        with open(DEV_DIR / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        flags = detect_conflicts(source, prob)
        results[cid] = flags
        print(f"  {cid}: flags = {flags}")

    # Enforce P5 mandate: Split 1 cases must fire none
    for cid in ["DEV-M1-S1", "DEV-M2-S1", "DEV-M3-S1", "DEV-M4-S1"]:
        assert results[cid] == [], f"Split 1 case {cid} fired unexpected flags: {results[cid]}"


def test_split2_proposed_rewrites_fire_intended_single_operators():
    """Under proposed rewrites, each Split 2 case fires exactly its single intended archetype operator."""
    # DEV-M1-S2: Resource Absence -> T1
    with open(DEV_DIR / "DEV-M1-S2" / "problem_card.json") as f:
        prob_m1 = ProblemCard.model_validate_json(f.read())
    flags_m1 = detect_conflicts(SOURCE_CARDS["DEV-M1"], prob_m1)
    assert flags_m1 == ["T1"], f"DEV-M1-S2 expected ['T1'], got {flags_m1}"

    # DEV-M2-S2: Timing Conflict -> T3 (time_mode: CYCLIC_DIURNAL)
    with open(DEV_DIR / "DEV-M2-S2" / "problem_card.json") as f:
        prob_m2 = ProblemCard.model_validate_json(f.read())
    prob_m2.time_pattern.time_mode = TimeModeEnum.CYCLIC_DIURNAL
    flags_m2 = detect_conflicts(SOURCE_CARDS["DEV-M2"], prob_m2)
    assert flags_m2 == ["T3"], f"DEV-M2-S2 expected ['T3'], got {flags_m2}"

    # DEV-M3-S2: Direction Inversion -> T2 (target_direction: INCREASE)
    with open(DEV_DIR / "DEV-M3-S2" / "problem_card.json") as f:
        prob_m3 = ProblemCard.model_validate_json(f.read())
    prob_m3.required_function.target_direction = DirectionEnum.INCREASE
    flags_m3 = detect_conflicts(SOURCE_CARDS["DEV-M3"], prob_m3)
    assert flags_m3 == ["T2"], f"DEV-M3-S2 expected ['T2'], got {flags_m3}"

    # DEV-M4-S2: Regime Re-scaling -> T5 (characteristic_length_m = 1.0 m vs biological gill 0.005 m)
    with open(DEV_DIR / "DEV-M4-S2" / "problem_card.json") as f:
        prob_m4 = ProblemCard.model_validate_json(f.read())
    prob_m4.target_system.characteristic_length_m = 1.0
    flags_m4 = detect_conflicts(SOURCE_CARDS["DEV-M4"], prob_m4)
    assert flags_m4 == ["T5"], f"DEV-M4-S2 expected ['T5'], got {flags_m4}"


def test_conflict_detector_negative_tests():
    """Negative tests for rule-based conflict detector:
    1. If you strip the conflict from a Split-2 case, detector returns 0 flags.
    2. If you add the conflict to a Split-1 case, detector returns the matching flag.
    """
    # 1. Strip conflict from Split-2 cases -> 0 flags
    # M1-S2: Strip T1 (Resource Absence) by removing liquid_water from resources_absent
    with open(DEV_DIR / "DEV-M1-S2" / "problem_card.json") as f:
        prob_m1 = ProblemCard.model_validate_json(f.read())
    prob_m1.environment.resources_absent = [
        r for r in prob_m1.environment.resources_absent
        if str(r) != "liquid_water" and getattr(r, "value", str(r)) != "liquid_water"
    ]
    flags_m1_stripped = detect_conflicts(SOURCE_CARDS["DEV-M1"], prob_m1)
    assert flags_m1_stripped == [], f"Stripped DEV-M1-S2 expected [], got {flags_m1_stripped}"

    # M2-S2: Strip T3 (Timing Conflict) by setting time_mode to STEADY
    with open(DEV_DIR / "DEV-M2-S2" / "problem_card.json") as f:
        prob_m2 = ProblemCard.model_validate_json(f.read())
    prob_m2.time_pattern.time_mode = TimeModeEnum.STEADY
    flags_m2_stripped = detect_conflicts(SOURCE_CARDS["DEV-M2"], prob_m2)
    assert flags_m2_stripped == [], f"Stripped DEV-M2-S2 expected [], got {flags_m2_stripped}"

    # M3-S2: Strip T2 (Direction Inversion) by setting target_direction to DECREASE
    with open(DEV_DIR / "DEV-M3-S2" / "problem_card.json") as f:
        prob_m3 = ProblemCard.model_validate_json(f.read())
    prob_m3.required_function.target_direction = DirectionEnum.DECREASE
    flags_m3_stripped = detect_conflicts(SOURCE_CARDS["DEV-M3"], prob_m3)
    assert flags_m3_stripped == [], f"Stripped DEV-M3-S2 expected [], got {flags_m3_stripped}"

    # M4-S2: Strip T5 (Regime Re-scaling) by setting characteristic_length_m <= 5*source_max_L
    with open(DEV_DIR / "DEV-M4-S2" / "problem_card.json") as f:
        prob_m4 = ProblemCard.model_validate_json(f.read())
    prob_m4.target_system.characteristic_length_m = 0.005  # within biological gill regime
    flags_m4_stripped = detect_conflicts(SOURCE_CARDS["DEV-M4"], prob_m4)
    assert flags_m4_stripped == [], f"Stripped DEV-M4-S2 expected [], got {flags_m4_stripped}"

    # 2. Add conflict to Split-1 cases -> matching flag
    # M1-S1: Add T1 (Resource Absence)
    with open(DEV_DIR / "DEV-M1-S1" / "problem_card.json") as f:
        prob_m1_s1 = ProblemCard.model_validate_json(f.read())
    prob_m1_s1.environment.resources_absent.append("liquid_water")
    flags_m1_added = detect_conflicts(SOURCE_CARDS["DEV-M1"], prob_m1_s1)
    assert flags_m1_added == ["T1"], f"Added conflict to DEV-M1-S1 expected ['T1'], got {flags_m1_added}"

    # M2-S1: Add T3 (Timing Conflict)
    with open(DEV_DIR / "DEV-M2-S1" / "problem_card.json") as f:
        prob_m2_s1 = ProblemCard.model_validate_json(f.read())
    prob_m2_s1.time_pattern.time_mode = TimeModeEnum.CYCLIC_DIURNAL
    flags_m2_added = detect_conflicts(SOURCE_CARDS["DEV-M2"], prob_m2_s1)
    assert flags_m2_added == ["T3"], f"Added conflict to DEV-M2-S1 expected ['T3'], got {flags_m2_added}"

    # M3-S1: Add T2 (Direction Inversion)
    with open(DEV_DIR / "DEV-M3-S1" / "problem_card.json") as f:
        prob_m3_s1 = ProblemCard.model_validate_json(f.read())
    prob_m3_s1.required_function.target_direction = DirectionEnum.INCREASE
    flags_m3_added = detect_conflicts(SOURCE_CARDS["DEV-M3"], prob_m3_s1)
    assert flags_m3_added == ["T2"], f"Added conflict to DEV-M3-S1 expected ['T2'], got {flags_m3_added}"

    # M4-S1: Add T5 (Regime Re-scaling)
    with open(DEV_DIR / "DEV-M4-S1" / "problem_card.json") as f:
        prob_m4_s1 = ProblemCard.model_validate_json(f.read())
    prob_m4_s1.target_system.characteristic_length_m = 1.0  # Macro-scale (1.0m >> 5*0.005m)
    flags_m4_added = detect_conflicts(SOURCE_CARDS["DEV-M4"], prob_m4_s1)
    assert flags_m4_added == ["T5"], f"Added conflict to DEV-M4-S1 expected ['T5'], got {flags_m4_added}"

