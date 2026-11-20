#!/usr/bin/env python3
"""V11 pilot E3 — end-to-end Mode B with physics checks (Qwen3-VL-32B-FP8, text-only calls).

Arms per organism (case) x seed:
  IMG    : starts from the IMG-arm perception (photo only) of the same case/seed
  NAME   : starts from the NAME-arm perception (name only)
  NOBIO  : control — same problem the IMG run chose, no biology; free choice of physics card
Each run: choose (problem, physics card) + design -> physics-card screen -> up to R repair turns with per-constraint
margins -> final screen verdict. Metrics: screen pass, regime ok, chosen card == organism's gold card,
chosen card plausible for chosen problem.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT))
from flbds.v11.cards import CARDS
from flbds.v11.problems import PROBLEMS

PROB = {p.id: p for p in PROBLEMS}


def catalogue():
    lines = []
    for c in CARDS.values():
        f = ", ".join(f"{p.name} [{p.lo:.3g}..{p.hi:.3g}]" for p in c.design_space)
        lines.append(f"- {c.id} ({c.domain}): {c.title}. Design fields: {f}")
    return "\n".join(lines)


def problems_text():
    return "\n".join(
        f"- {p.id} [{p.domain}] {p.title}: {p.statement}" for p in PROBLEMS
    )


def problem_full(p):
    env = "; ".join(f"{k} = {v:.4g}" for k, v in p.env.items())
    return f"{p.id} — {p.title}. {p.statement}\nOperating conditions and requirements: {env}"


FMT = (
    'Return ONLY one JSON object: {"problem_id": "P-...", "card_id": "<physics card id>", '
    '"bio_mapping": [{"biological_feature": "...", "engineering_feature": "...", "scale_change": "..."}], '
    '"rationale": "2 sentences", "design": {<every design field of the chosen card as a number within bounds>}}'
)


def choose_prompt(perception, arm):
    if arm == "NOBIO":
        return None
    return (
        f"You are a bio-inspired design engineer. A biological analysis of an organism:\n{json.dumps(perception)[:5000]}\n\n"
        f"Engineering problems you may choose from (choose the ONE where this organism's mechanism gives the best working, innovative solution):\n{problems_text()}\n\n"
        f"Physics models available to realise and check the design (choose the one that expresses the biological mechanism):\n{catalogue()}\n\n"
        f"The design MUST be based on the organism's mechanism. {FMT}"
    )


def nobio_prompt(pid):
    p = PROB[pid]
    return (
        f"You are a design engineer. Engineering problem:\n{problem_full(p)}\n\n"
        f"Physics models available to realise and check the design:\n{catalogue()}\n\n"
        f"Design the best working solution. {FMT.replace('P-...', pid)}"
    )


def repair_prompt(prev, table, pid):
    return (
        f"Your previous design for problem {problem_full(PROB[pid])}\n"
        f"was: {json.dumps(prev)[:3000]}\nPhysics check result:\n{table}\n"
        "Fix the failures (you may change parameters or switch to a better-suited physics card, keeping the same problem "
        f"and the same biological inspiration if any). {FMT.replace('P-...', pid)}"
    )


def pj(t):
    t = re.sub(r"```(json)?", "", t)
    a, b = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[a : b + 1])
    except Exception:
        return None


def check(d):
    """-> (passed, regime_ok, min_margin, table_text, status)"""
    if not d or d.get("problem_id") not in PROB or d.get("card_id") not in CARDS:
        return False, False, -10, "Unknown problem_id or card_id.", "bad_ids"
    p, c = PROB[d["problem_id"]], CARDS[d["card_id"]]
    try:
        r = c.screen(d.get("design") or {}, p.env)
    except Exception as e:  # schema / env errors
        msg = str(e)[:300]
        if "Env" in type(e).__name__ or "env" in msg.lower():
            return (
                False,
                False,
                -10,
                (
                    "This physics model cannot be evaluated for this problem's conditions "
                    "(the mechanism does not match the problem). Choose a better-suited card."
                ),
                "card_problem_mismatch",
            )
        return False, False, -10, f"Design invalid: {msg}", "schema_error"
    rows = "\n".join(
        f"| {x.name} | {x.achieved:.4g} {x.unit} | {x.sense} {x.limit:.4g} | margin {x.margin:+.3f} | {x.status} |"
        for x in r.constraints
    )
    if r.regime_notes:
        rows += "\nRegime/validity: " + "; ".join(r.regime_notes)
    return r.passed, r.regime_ok, r.min_margin, rows, ("pass" if r.passed else "fail")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default="/home/abhishek24024/flbds_data/models/Qwen3-VL-32B-Instruct-FP8",
    )
    ap.add_argument("--dir", default="/home/abhishek24024/flbds_data/v11/e1e2")
    ap.add_argument("--repairs", type=int, default=4)
    a = ap.parse_args()
    d = Path(a.dir)
    from vllm import LLM, SamplingParams

    gold = {
        c["id"]: c
        for c in json.loads((ROOT / "flbds/v11/data/organisms.json").read_text())[
            "cases"
        ]
    }
    per = {
        (r["case"], r["arm"], r["seed"]): r
        for r in map(json.loads, open(d / "e1_perception.jsonl"))
    }
    llm = LLM(
        model=a.model,
        max_model_len=16384,
        gpu_memory_utilization=0.88,
        limit_mm_per_prompt={"image": 0},
    )

    def gen(prompts, seed0):
        sps = [
            SamplingParams(temperature=0.7, top_p=0.9, max_tokens=1500, seed=seed0 + i)
            for i in range(len(prompts))
        ]
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], sps)
        return [pj(o.outputs[0].text) for o in outs]

    def loop(trajs, seed0):
        """trajs: list of dict with 'design' (parsed) and 'pid'; runs repairs in batches."""
        for t in trajs:
            t["history"] = []
            res = check(t["design"])
            t["history"].append({"design": t["design"], "check": res[:3] + (res[4],)})
            t["res"] = res
        for k in range(a.repairs):
            todo = [t for t in trajs if not t["res"][0] and t.get("pid") in PROB]
            if not todo:
                break
            outs = gen(
                [repair_prompt(t["design"], t["res"][3], t["pid"]) for t in todo],
                seed0 + 100 * (k + 1),
            )
            for t, o in zip(todo, outs):
                if o is not None:
                    o["problem_id"] = t[
                        "pid"
                    ]  # problem is fixed after the first choice
                    t["design"] = o
                res = check(t["design"])
                t["history"].append(
                    {"design": t["design"], "check": res[:3] + (res[4],)}
                )
                t["res"] = res

    rows = []
    for arm in ("IMG", "NAME"):
        keys = [k for k in per if k[1] == arm and per[k]["parsed"]]
        firsts = gen(
            [choose_prompt(per[k]["parsed"], arm) for k in keys],
            11000 if arm == "IMG" else 12000,
        )
        trajs = [
            {
                "case": k[0],
                "arm": arm,
                "seed": k[2],
                "design": f,
                "pid": (f or {}).get("problem_id"),
            }
            for k, f in zip(keys, firsts)
        ]
        loop(trajs, 13000 if arm == "IMG" else 14000)
        rows += trajs
    # NOBIO control on the problem the IMG run chose
    img = [t for t in rows if t["arm"] == "IMG" and t["pid"] in PROB]
    nf = gen([nobio_prompt(t["pid"]) for t in img], 15000)
    ctl = [
        {
            "case": t["case"],
            "arm": "NOBIO",
            "seed": t["seed"],
            "design": f,
            "pid": t["pid"],
        }
        for t, f in zip(img, nf)
    ]
    for c in ctl:
        if c["design"] is not None:
            c["design"]["problem_id"] = c["pid"]
    loop(ctl, 16000)
    rows += ctl
    with open(d / "e3_modeb.jsonl", "w") as f:
        for t in rows:
            first = t["history"][0]["design"] or {}
            final = t["design"] or {}
            gcard = gold[t["case"]].get("card")
            f.write(
                json.dumps(
                    {
                        "case": t["case"],
                        "arm": t["arm"],
                        "seed": t["seed"],
                        "problem_id": t["pid"],
                        "first_card": first.get("card_id"),
                        "final_card": final.get("card_id"),
                        "gold_card": gcard,
                        "first_card_is_gold": first.get("card_id") == gcard
                        if gcard
                        else None,
                        "card_plausible_for_problem": (
                            final.get("card_id") in PROB[t["pid"]].plausible_cards
                        )
                        if t["pid"] in PROB
                        else False,
                        "passed": bool(t["res"][0]),
                        "regime_ok": bool(t["res"][1]),
                        "min_margin": t["res"][2],
                        "status": t["res"][4],
                        "turns": len(t["history"]) - 1,
                        "final_design": final,
                        "history": t["history"],
                    }
                )
                + "\n"
            )
    print("E3 done", len(rows), flush=True)


if __name__ == "__main__":
    main()
