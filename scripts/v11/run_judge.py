#!/usr/bin/env python3
"""V11 pilot, judging stage (Qwen2.5-72B-Instruct-FP8 — a different model family/size than the generator).

J1 perception/rediscovery: per perception run, compare against the gold case (organism, structure, mechanism,
   canonical application) -> organism_correct, mechanism_score (0-2), rediscovery_rank (1-5, 0 = absent),
   hallucination (0/1), specificity (1-5).
J2 blueprint pairwise: BIO blueprint vs NOBIO blueprint for the same application, judged blind in BOTH orders
   (position-bias control) on novelty, physical soundness, implementability, overall; plus bio_faithfulness (1-5)
   for the BIO blueprint alone.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

J1 = """You are grading an AI system's analysis of an organism for bio-inspired design against a reference.
REFERENCE (ground truth): organism = {common} ({scientific}); key structure = {structure}; mechanism = {mechanism};
canonical engineering application = {application}.
SYSTEM OUTPUT:
{output}
Grade strictly. Return ONLY JSON:
{{"organism_correct": 0 or 1 (1 if the identified organism matches the reference at genus level or by common name),
 "mechanism_score": 0, 1 or 2 (2 = the reference mechanism is stated correctly, 1 = partially/vaguely, 0 = missing or wrong),
 "rediscovery_rank": 0-5 (position 1-5 of the first proposed application that is essentially the canonical application; 0 if none),
 "hallucination": 0 or 1 (1 if the output asserts a clearly false biological fact about this organism),
 "specificity": 1-5 (how concrete and design-usable the structures/mechanisms are: scales, geometry, principles),
 "note": "one sentence"}}"""

J2 = """You are an expert engineering design reviewer. Two concept blueprints address the same engineering application.
APPLICATION: {app}
--- DESIGN A ---
{a}
--- DESIGN B ---
{b}
Judge on: novelty (non-obvious relative to standard practice), physical soundness (would it actually work; are numbers
and equations plausible), implementability (clear enough to build from the description). Return ONLY JSON:
{{"novelty": "A" or "B" or "tie", "soundness": "A" or "B" or "tie", "implementability": "A" or "B" or "tie",
 "overall": "A" or "B" or "tie", "reason": "one sentence"}}"""

J3 = """Rate how faithfully this engineering blueprint uses its stated biological source.
5 = the core working principle is the biological mechanism, correctly transferred with attention to scale/regime;
3 = biological idea present but partly superficial; 1 = biology is decoration only.
BLUEPRINT:
{bp}
Return ONLY JSON: {{"bio_faithfulness": 1-5, "reason": "one sentence"}}"""


def pj(t):
    t = re.sub(r"```(json)?", "", t)
    a, b = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[a : b + 1])
    except Exception:
        return None


def brief(p):
    if not p:
        return "(unparseable)"
    keep = {
        k: p.get(k)
        for k in (
            "title",
            "summary",
            "bio_to_engineering_mapping",
            "geometry",
            "materials",
            "manufacturing_steps",
            "quick_physics_check",
            "expected_performance",
            "limitations_and_risks",
        )
    }
    return json.dumps(keep, indent=0)[:6000]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default="/home/abhishek24024/flbds_data/models/Qwen2.5-72B-Instruct-FP8",
    )
    ap.add_argument("--dir", default="/home/abhishek24024/flbds_data/v11/e1e2")
    a = ap.parse_args()
    d = Path(a.dir)
    from vllm import LLM, SamplingParams

    gold = {
        c["id"]: c
        for c in json.loads((ROOT / "flbds/v11/data/organisms.json").read_text())[
            "cases"
        ]
    }
    per = [json.loads(l) for l in open(d / "e1_perception.jsonl")]
    bps = [json.loads(l) for l in open(d / "e2_blueprints.jsonl")]
    llm = LLM(model=a.model, max_model_len=12288, gpu_memory_utilization=0.9)
    sp = SamplingParams(temperature=0.0, max_tokens=400)

    def chat(prompts):
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], sp)
        return [pj(o.outputs[0].text) for o in outs]

    # J1
    p1 = []
    for r in per:
        g = gold[r["case"]]
        o = json.dumps(
            {
                k: (r["parsed"] or {}).get(k)
                for k in ("organism", "structures", "mechanisms", "applications")
            }
        )[:7000]
        p1.append(
            J1.format(
                output=o,
                **{
                    k: g[k]
                    for k in (
                        "common",
                        "scientific",
                        "structure",
                        "mechanism",
                        "application",
                    )
                },
            )
        )
    for r, j in zip(per, chat(p1)):
        r["judge"] = j
    with open(d / "j1_perception_judged.jsonl", "w") as f:
        for r in per:
            f.write(
                json.dumps(
                    {k: r[k] for k in ("case", "arm", "seed", "judge", "tokens")}
                )
                + "\n"
            )

    # J2 pairwise (both orders) + J3 faithfulness
    nob = {(b["case"], b["arm"]): b for b in bps if b["variant"] == "NOBIO"}
    pairs = [
        (b, nob[(b["case"], b["arm"])])
        for b in bps
        if b["variant"] == "BIO" and (b["case"], b["arm"]) in nob
    ]
    p2, p3 = [], []
    for bio, ctl in pairs:
        app = bio["application"].get("application")
        p2.append(
            J2.format(app=app, a=brief(bio["parsed"]), b=brief(ctl["parsed"]))
        )  # BIO = A
        p2.append(
            J2.format(app=app, a=brief(ctl["parsed"]), b=brief(bio["parsed"]))
        )  # BIO = B
        p3.append(J3.format(bp=brief(bio["parsed"])))
    r2, r3 = chat(p2), chat(p3)
    with open(d / "j2_pairwise_judged.jsonl", "w") as f:
        for i, (bio, ctl) in enumerate(pairs):
            f.write(
                json.dumps(
                    {
                        "case": bio["case"],
                        "arm": bio["arm"],
                        "seed": bio["seed"],
                        "bio_as_A": r2[2 * i],
                        "bio_as_B": r2[2 * i + 1],
                        "faith": r3[i],
                    }
                )
                + "\n"
            )
    print("judging done", len(per), len(pairs), flush=True)


if __name__ == "__main__":
    main()
