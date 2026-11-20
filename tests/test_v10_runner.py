"""End-to-end runner tests with a fake LLM (no vLLM / torch needed)."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from flbds.v10.families import get_family
from flbds.v10.gen import Completion, GenParams, RequestOutput
from flbds.v10.optimizer_arm import optimise_from
from flbds.v10.runner import CONDITIONS, parse_response, run_condition, summarise

REPO = Path(__file__).resolve().parents[1]

INST_ENV_HX = {
    "required_duty_W": 800.0,
    "T_cold_in_degC": 15.0,
    "T_hot_in_degC": 45.0,
    "max_pressure_drop_Pa": 250.0,
    "length_cap_m": 1.0,
}
INST_ENV_MEM = {
    "required_flux_mol_m2_s": 0.006,
    "min_pore_diameter_m": 35e-9,
    "hydrostatic_head_m": 6.0,
    "delta_concentration_mol_m3": 5.0,
}


def _inst(iid: str, fam_name: str, env: dict[str, float]) -> dict[str, Any]:
    fam = get_family(fam_name)
    return {
        "instance_id": iid,
        "family": fam_name,
        "template_id": fam.template_id,
        "env": env,
        "system_name": fam.system_names[0],
        "problem_statement": fam.problem_statement(
            env, f"{fam.system_names[0]} [{iid}]"
        ),
    }


class FakeLLM:
    """Turn 0: seed-1 runs pick a wrong template, others give a poor (bounds-valid) design;
    the first response for MEM is garbage (exercises the free re-sample); repairs give a screen-optimal design."""

    def __init__(self, instances: list[dict[str, Any]]) -> None:
        self.by_tag = {f"[{i['instance_id']}]": i for i in instances}
        self.calls = 0
        self.garbage_done: set[str] = set()

    def _inst(self, text: str) -> dict[str, Any]:
        for tag, inst in self.by_tag.items():
            if tag in text:
                return inst
        raise AssertionError("instance tag not found in prompt")

    def generate(
        self, prompts: list[list[dict[str, str]]], params: list[GenParams]
    ) -> list[RequestOutput]:
        self.calls += 1
        assert len(prompts) == len(params)
        outs = []
        for msgs, gp in zip(prompts, params):
            assert isinstance(msgs, list) and msgs[-1]["role"] == "user"
            assert gp.max_tokens == 350
            user = msgs[-1]["content"]
            inst = self._inst(user)
            fam = get_family(inst["family"])
            first = "previous attempt" not in user
            key = inst["instance_id"]
            if first and inst["family"] == "F_MEM" and key not in self.garbage_done:
                self.garbage_done.add(key)
                text = "Sure! Here is my design: (no json)"
            elif first and "seed1" in user:
                text = json.dumps(
                    {"rationale": "x", "template_id": "TPL_01", "design": {}}
                )
            elif first:
                text = json.dumps(
                    {
                        "rationale": "x",
                        "template_id": inst["template_id"],
                        "design": {p.name: p.lo for p in fam.design_space},
                    }
                )
            else:
                design, _ = optimise_from(None, inst["env"], fam, seed=0)
                text = (
                    "```json\n"
                    + json.dumps(
                        {
                            "rationale": "fix",
                            "template_id": inst["template_id"],
                            "design": design,
                        }
                    )
                    + "\n```"
                )
            outs.append(
                RequestOutput([Completion(text, list(range(len(text) // 4 + 1)))])
            )
        return outs


@pytest.fixture()
def instances() -> list[dict[str, Any]]:
    return [
        _inst("T-HX-1", "F_HX", INST_ENV_HX),
        _inst("T-MEM-1", "F_MEM", INST_ENV_MEM),
    ]


@pytest.mark.parametrize(
    "cond", ["B0", "L3", "BoN8", "OPT", "OPTONLY", "V10", "L3_BIOMISMATCH", "A3x8"]
)
def test_runner_end_to_end(cond: str, instances) -> None:
    llm = FakeLLM(instances)
    records = run_condition(llm, instances, seeds=[1, 2], cond_name=cond)
    assert len(records) == len(instances) * 2
    for r in records:
        assert {
            "instance_id",
            "family",
            "seed",
            "condition",
            "screen_pass",
            "eval_pass",
            "tokens_generated",
        } <= set(r)
        for t in r.get("trajectories", []):
            for turn in t["turns"]:
                assert "acceptable" not in turn["prompt"].lower()
                assert inst_template_not_named(turn["prompt"], r)
    s = summarise(records, cond)
    assert s["n_runs"] == 4
    if cond == "B0":
        # poor lower-bound design on turn 0: screen must fail, so no B0 run passes
        assert not any(r["screen_pass"] for r in records)
        mem = [r for r in records if r["family"] == "F_MEM"]
        assert any(r["parse_failures"] >= 1 for r in mem)  # garbage then free re-sample
        assert all(r["final_status"] != "parse_failure" for r in mem)
    if cond in ("L3", "V10", "A3x8", "L3_BIOMISMATCH"):
        assert all(r["screen_pass"] for r in records)
        assert max(r["turns_used"] for r in records) >= 1
    if cond == "OPTONLY":
        assert llm.calls == 0
        assert all(r["screen_pass"] for r in records)
    if cond == "OPT":
        assert all("optimiser" in r for r in records)


def inst_template_not_named(prompt: str, rec: dict[str, Any]) -> bool:
    # The problem statement part (before the catalogue) must not name any template.
    head = prompt.split("Available physics templates")[0]
    return "TPL_" not in head


def test_batching_one_generate_per_turn(instances) -> None:
    llm = FakeLLM(instances)
    run_condition(llm, instances, seeds=[1, 2, 3], cond_name="BoN8")
    # BoN8: one batched call for the turn + one batched free re-sample for the MEM garbage output
    assert llm.calls == 2


def test_parse_response_strict_bounds() -> None:
    inst = _inst("X", "F_HX", INST_ENV_HX)
    fam = get_family("F_HX")
    good = {p.name: p.lo for p in fam.design_space}
    ok = parse_response(json.dumps({"template_id": "TPL_08", "design": good}), inst)
    assert ok["status"] == "ok"
    bad = dict(good, length_m=99.0)
    sf = parse_response(json.dumps({"template_id": "tpl-08", "design": bad}), inst)
    assert sf["status"] == "schema_failure" and "length_m" in sf["errors"][0]
    missing = dict(good)
    missing.pop("length_m")
    assert (
        parse_response(json.dumps({"template_id": "TPL_08", "design": missing}), inst)[
            "status"
        ]
        == "schema_failure"
    )
    assert (
        parse_response('{"template_id": "TPL_09", "design": {}}', inst)["status"]
        == "template_choice_error"
    )
    assert parse_response("not json", inst)["status"] == "parse_failure"


def test_conditions_registry() -> None:
    assert CONDITIONS["A24x1"].n_samples == 24 and CONDITIONS["A24x1"].max_repairs == 0
    assert CONDITIONS["A8x3"].n_samples == 8 and CONDITIONS["A8x3"].max_repairs == 2
    assert CONDITIONS["A3x8"].n_samples == 3 and CONDITIONS["A3x8"].max_repairs == 7
    assert CONDITIONS["V10"].n_samples == 8 and CONDITIONS["V10"].max_repairs == 3


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "run_v10", REPO / "scripts/run_v10.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_incremental_resume_and_dev_instances(tmp_path: Path) -> None:
    mod = _load_script()
    from flbds.v10.dev_instances import build_dev_instances

    dev = build_dev_instances()
    assert len(dev) == 12 and {d["family"] for d in dev} == {
        "F_PCM",
        "F_HX",
        "F_RAD",
        "F_MEM",
    }
    for d in dev:
        d["problem_statement"] += f"\n[{d['instance_id']}]"
    llm = FakeLLM(dev)
    args = mod.build_parser().parse_args(
        [
            "--instances",
            "dev",
            "--output-dir",
            str(tmp_path),
            "--conditions",
            "B0",
            "--max-instances",
            "4",
            "--chunk-instances",
            "2",
            "--seeds",
            "1",
            "2",
        ]
    )
    # the fake needs the instance tag in the prompt: patch dev builder used by the script
    import flbds.v10.dev_instances as di

    orig = di.build_dev_instances
    di.build_dev_instances = lambda: dev
    try:
        mod.run(args, llm=llm)
        lines = (tmp_path / "B0.jsonl").read_text().splitlines()
        assert len(lines) == 8
        n_calls = llm.calls
        mod.run(args, llm=llm)  # resume: nothing left to do
        assert llm.calls == n_calls
        assert len((tmp_path / "B0.jsonl").read_text().splitlines()) == 8
        summ = json.loads((tmp_path / "summary_all.json").read_text())
        assert summ["B0"]["n_runs"] == 8
    finally:
        di.build_dev_instances = orig
    assert isinstance(args, argparse.Namespace)


class WrongTemplateLLM(FakeLLM):
    def generate(self, prompts, params):
        self.calls += 1
        self.prompts = getattr(self, "prompts", []) + [m[-1]["content"] for m in prompts]
        t = json.dumps({"rationale": "x", "template_id": "TPL_03", "design": {}})
        return [RequestOutput([Completion(t, [1, 2, 3])]) for _ in prompts]


def test_template_choice_error_and_non_leaky_feedback(instances) -> None:
    from flbds.v10.prompts import TEMPLATE_ERROR_FEEDBACK

    llm = WrongTemplateLLM(instances)
    recs = run_condition(llm, instances, seeds=[1], cond_name="L3")
    assert all(r["failure_type"] == "template_choice_error" and not r["eval_pass"] for r in recs)
    fb = [p for p in llm.prompts if "previous attempt" in p]
    assert fb and all(TEMPLATE_ERROR_FEEDBACK in p for p in fb)
    for p, inst in zip(fb, instances * 10):
        tail = p.split("Your previous attempt")[1]
        assert "TPL_08" not in tail and "TPL_10" not in tail  # true template never revealed
