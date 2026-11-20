"""Tests for flbds.v10.generator: determinism and certification."""

from __future__ import annotations

from flbds.v10.families import get_family
from flbds.v10.generator import GenConfig, generate_instances, instances_hash

SMALL = GenConfig(
    n_per_family=2,
    max_candidates_per_family=12,
    de_maxiter=15,
    de_popsize=8,
    n_random=40,
    families=["F_HX", "F_MEM"],
    seed=7,
)


def test_generator_deterministic_same_seed_same_hash() -> None:
    a = generate_instances(SMALL)
    b = generate_instances(SMALL)
    assert instances_hash(a["instances"]) == instances_hash(b["instances"])
    assert a["sha256"] == b["sha256"]


def test_certified_designs_pass_hidden_eval_and_statement_is_template_free() -> None:
    out = generate_instances(SMALL)
    assert out["instances"], "no instances kept"
    for inst in out["instances"]:
        fam = get_family(inst["family"])
        passed, margins, reason = fam.hidden_eval(inst["certified_design"], inst["env"])
        assert passed, reason
        assert inst["trivial_pass_rate"] <= 0.5
        assert "TPL" not in inst["problem_statement"]
