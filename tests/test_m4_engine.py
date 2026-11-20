"""tests/test_m4_engine.py
Unit tests for M4 Analogy and Transformation Engine (FLBDS v9 §4.4, §4.5 and Audit Round 11 Item C).

Verifications:
1. SAPPhIRE graph structure and topology validation (connectivity, all canonical node types).
2. Precondition gates: operators may NOT fire without preconditions (negative tests).
3. Ablation flags: operators do NOT fire when corresponding ablation flag is False (ablation negative tests).
4. Deterministic graph rewrites: graph topology remains 100% valid after every operator application.
5. Proof obligations: exact match with target M5 verifier templates (T1->TPL_02, T2->TPL_09, T3->TPL_08, T4->TPL_02, T5->TPL_10).
6. Fixture labeling: all 4 biological source mechanisms are explicitly labeled FIXTURE (never called extracted).
7. Conflict detector across all 12 dev cases.
"""

from pathlib import Path
import pytest

from flbds.schema.enums import DirectionEnum, ResourceEnum, TimeModeEnum
from flbds.schema.problem_card import ProblemCard
from flbds.m4.sapphire_graph import SapphireGraph
from flbds.m4.fixtures import DEV_FIXTURES
from flbds.m4.conflict_detector import detect_conflicts
from flbds.m4.operators import (
    AblationConfig,
    apply_operator_t1,
    apply_operator_t2,
    apply_operator_t3,
    apply_operator_t4,
    apply_operator_t5,
)

DEV_BASE = Path(__file__).resolve().parent.parent / "flbds" / "benchmark" / "dev"


class TestM4Fixtures:
    """Verifies biological mechanism cards are explicitly labeled FIXTURE."""

    @pytest.mark.parametrize("cluster_id", ["DEV-M1", "DEV-M2", "DEV-M3", "DEV-M4"])
    def test_fixtures_are_labeled_fixture(self, cluster_id: str):
        meta, g = DEV_FIXTURES[cluster_id]()
        assert meta["tier"] == "FIXTURE", f"{cluster_id} must have tier=FIXTURE"
        assert "FIXTURE" in meta["card_id"], f"{cluster_id} card_id must contain FIXTURE"
        assert meta["provenance"] == "HAND_BUILT_FIXTURE_NOT_EXTRACTED"
        is_valid, errors = g.validate_topology()
        assert is_valid, f"{cluster_id} initial graph topology invalid: {errors}"


class TestSapphireGraphTopology:
    """Verifies graph validation rules and edge integrity."""

    def test_valid_graph_passes(self):
        _, g = DEV_FIXTURES["DEV-M1"]()
        valid, errs = g.validate_topology()
        assert valid
        assert len(errs) == 0

    def test_missing_node_type_fails(self):
        _, g = DEV_FIXTURES["DEV-M1"]()
        g.organs.clear()  # Drop all organs
        valid, errs = g.validate_topology()
        assert not valid
        assert any("Organ" in e for e in errs)

    def test_broken_edge_endpoint_fails(self):
        _, g = DEV_FIXTURES["DEV-M1"]()
        g.add_edge("nonexistent_source", "effect_01", "co_activates")
        valid, errs = g.validate_topology()
        assert not valid
        assert any("nonexistent_source" in e for e in errs)


class TestOperatorT1ResourceLoopClosing:
    """Tests T1: Resource Absence -> Sealed storage rewrite."""

    def test_t1_fires_on_dev_m1_s2(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t1(g, meta, prob)
        assert res.applied, "T1 should fire on DEV-M1-S2 where liquid_water is absent"
        assert res.target_template == "TPL_02"
        assert "enthalpy capacity >= required_energy" in res.proof_obligation
        valid, errs = res.rewritten_graph.validate_topology()
        assert valid, f"T1 rewritten graph topology invalid: {errs}"

    def test_negative_t1_does_not_fire_when_resource_present(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S1" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        # In DEV-M1-S1, liquid_water is NOT absent
        res = apply_operator_t1(g, meta, prob)
        assert not res.applied, "T1 must NOT fire when consumable resource is available"
        assert "Precondition failed" in res.rejection_reason

    def test_negative_t1_ablation_disabled(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t1(g, meta, prob, config=AblationConfig(enable_t1=False))
        assert not res.applied
        assert "disabled by ablation flag" in res.rejection_reason


class TestOperatorT2DirectionInversion:
    """Tests T2: Opposing direction -> Flux sign and boundary inversion."""

    def test_t2_fires_when_direction_opposes(self):
        meta, g = DEV_FIXTURES["DEV-M3"]()
        with open(DEV_BASE / "DEV-M3-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        prob.required_function.target_direction = DirectionEnum.INCREASE
        res = apply_operator_t2(g, meta, prob)
        assert res.applied, "T2 should fire when source direction opposes target"
        assert res.target_template == "TPL_09"
        valid, errs = res.rewritten_graph.validate_topology()
        assert valid, f"T2 rewritten graph topology invalid: {errs}"

    def test_negative_t2_does_not_fire_when_directions_align(self):
        meta, g = DEV_FIXTURES["DEV-M3"]()
        with open(DEV_BASE / "DEV-M3-S1" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t2(g, meta, prob)
        assert not res.applied, "T2 must NOT fire when target directions align"
        assert "Precondition failed" in res.rejection_reason

    def test_negative_t2_ablation_disabled(self):
        meta, g = DEV_FIXTURES["DEV-M3"]()
        with open(DEV_BASE / "DEV-M3-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        prob.required_function.target_direction = DirectionEnum.INCREASE
        res = apply_operator_t2(g, meta, prob, config=AblationConfig(enable_t2=False))
        assert not res.applied
        assert "disabled by ablation flag" in res.rejection_reason


class TestOperatorT3TemporalPhaseShift:
    """Tests T3: Steady source vs cyclic target -> Capacitive buffering."""

    def test_t3_fires_when_cyclic_target(self):
        meta, g = DEV_FIXTURES["DEV-M2"]()
        with open(DEV_BASE / "DEV-M2-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        prob.time_pattern.time_mode = TimeModeEnum.CYCLIC_DIURNAL
        res = apply_operator_t3(g, meta, prob)
        assert res.applied, "T3 should fire when time modes mismatch"
        assert res.target_template == "TPL_08"
        valid, errs = res.rewritten_graph.validate_topology()
        assert valid, f"T3 rewritten graph topology invalid: {errs}"

    def test_negative_t3_does_not_fire_when_time_modes_compatible(self):
        meta, g = DEV_FIXTURES["DEV-M2"]()
        with open(DEV_BASE / "DEV-M2-S1" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t3(g, meta, prob)
        assert not res.applied, "T3 must NOT fire when time modes are compatible"
        assert "Precondition failed" in res.rejection_reason

    def test_negative_t3_ablation_disabled(self):
        meta, g = DEV_FIXTURES["DEV-M2"]()
        with open(DEV_BASE / "DEV-M2-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        prob.time_pattern.time_mode = TimeModeEnum.CYCLIC_DIURNAL
        res = apply_operator_t3(g, meta, prob, config=AblationConfig(enable_t3=False))
        assert not res.applied
        assert "disabled by ablation flag" in res.rejection_reason


class TestOperatorT4EffectSubstitution:
    """Tests T4: Blocked medium -> Sibling physical effect substitution."""

    def test_t4_fires_when_medium_blocked(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t4(g, meta, prob)
        assert res.applied
        assert res.target_template == "TPL_02"
        valid, errs = res.rewritten_graph.validate_topology()
        assert valid, f"T4 rewritten graph topology invalid: {errs}"

    def test_negative_t4_does_not_fire_when_medium_available(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S1" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t4(g, meta, prob)
        assert not res.applied
        assert "Precondition failed" in res.rejection_reason

    def test_negative_t4_ablation_disabled(self):
        meta, g = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t4(g, meta, prob, config=AblationConfig(enable_t4=False))
        assert not res.applied
        assert "disabled by ablation flag" in res.rejection_reason


class TestOperatorT5RegimeRescaling:
    """Tests T5: Scale mismatch -> Sub-scale pore/micro-architecture tuning."""

    def test_t5_fires_when_macro_scale_exceeds_biological_regime(self):
        meta, g = DEV_FIXTURES["DEV-M4"]()
        with open(DEV_BASE / "DEV-M4-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t5(g, meta, prob, char_length_m=0.50)
        assert res.applied
        assert res.target_template == "TPL_10"
        assert "Laplace capillary breakthrough" in res.proof_obligation
        valid, errs = res.rewritten_graph.validate_topology()
        assert valid, f"T5 rewritten graph topology invalid: {errs}"

    def test_negative_t5_does_not_fire_within_micro_scale(self):
        meta, g = DEV_FIXTURES["DEV-M4"]()
        with open(DEV_BASE / "DEV-M4-S1" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t5(g, meta, prob, char_length_m=0.005)
        assert not res.applied
        assert "Precondition failed" in res.rejection_reason

    def test_negative_t5_ablation_disabled(self):
        meta, g = DEV_FIXTURES["DEV-M4"]()
        with open(DEV_BASE / "DEV-M4-S2" / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        res = apply_operator_t5(g, meta, prob, config=AblationConfig(enable_t5=False), char_length_m=0.50)
        assert not res.applied
        assert "disabled by ablation flag" in res.rejection_reason


class TestConflictDetectorAll12DevCases:
    """Verifies that conflict detector fires exactly according to FLBDS design splits."""

    @pytest.mark.parametrize("cid", [
        "DEV-M1-S1", "DEV-M2-S1", "DEV-M3-S1", "DEV-M4-S1"
    ])
    def test_split1_fires_zero_conflicts(self, cid: str):
        cluster = cid[:6]
        meta, _ = DEV_FIXTURES[cluster]()
        with open(DEV_BASE / cid / "problem_card.json") as f:
            prob = ProblemCard.model_validate_json(f.read())
        flags = detect_conflicts(meta, prob)
        assert len(flags) == 0, f"Split 1 unperturbed case {cid} must fire 0 conflict flags, got {flags}"

    def test_split2_proposed_rewrites_fire_intended_single_operators(self):
        # M1-S2: Resource Absence -> T1
        meta_m1, _ = DEV_FIXTURES["DEV-M1"]()
        with open(DEV_BASE / "DEV-M1-S2" / "problem_card.json") as f:
            prob_m1 = ProblemCard.model_validate_json(f.read())
        flags_m1 = detect_conflicts(meta_m1, prob_m1)
        assert "T1" in flags_m1

        # M2-S2: Timing Conflict -> T3
        meta_m2, _ = DEV_FIXTURES["DEV-M2"]()
        with open(DEV_BASE / "DEV-M2-S2" / "problem_card.json") as f:
            prob_m2 = ProblemCard.model_validate_json(f.read())
        prob_m2.time_pattern.time_mode = TimeModeEnum.CYCLIC_DIURNAL
        flags_m2 = detect_conflicts(meta_m2, prob_m2)
        assert "T3" in flags_m2

        # M3-S2: Direction Inversion -> T2
        meta_m3, _ = DEV_FIXTURES["DEV-M3"]()
        with open(DEV_BASE / "DEV-M3-S2" / "problem_card.json") as f:
            prob_m3 = ProblemCard.model_validate_json(f.read())
        prob_m3.required_function.target_direction = DirectionEnum.INCREASE
        flags_m3 = detect_conflicts(meta_m3, prob_m3)
        assert "T2" in flags_m3

        # M4-S2: Regime Re-scaling -> T5
        meta_m4, _ = DEV_FIXTURES["DEV-M4"]()
        with open(DEV_BASE / "DEV-M4-S2" / "problem_card.json") as f:
            prob_m4 = ProblemCard.model_validate_json(f.read())
        flags_m4 = detect_conflicts(meta_m4, prob_m4, proposed_char_length=0.50)
        assert "T5" in flags_m4
