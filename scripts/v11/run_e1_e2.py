#!/usr/bin/env python3
"""V11 pilot, generation stage (Qwen3-VL-32B-Instruct-FP8, vLLM).

For each organism in flbds/v11/data/organisms.json that has a photo, and each input arm
  IMG       photo only (no name, no caption)
  NAME      common + scientific name only (no photo)
  IMG+NAME  photo + name
and each seed, the model returns ONE JSON object:
  perception  (organism guess, visible structures with scale, functions, mechanisms with physical-effect tag)
  applications (top-5 engineering applications, each with problem, bio->engineering mapping, why it should work physically)
Then, for the top application of each run (Mode B), a blueprint call returns a design blueprint JSON
(geometry with dimensions, materials, manufacturing steps, quick physics check, limitations, render prompt) and a
control arm NOBIO designs for the SAME application statement with no biology.
Outputs JSONL to --out.
"""

import argparse
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAGS = "thermal | fluids | structures | adhesion | wetting | optics | mass_transfer | other"

PERCEIVE = f"""You are a biologist and a bio-inspired design engineer.
{{subject}}
Task: analyse the organism for BIO-INSPIRED ENGINEERING DESIGN. Return ONLY one JSON object:
{{{{
 "organism": {{{{"common": "...", "scientific": "...", "confidence": 0-1}}}},
 "structures": [{{{{"name": "...", "description": "...", "scale_m_estimate": number or null, "visible_in_image": true/false}}}}],
 "functions": ["biological functions these structures serve"],
 "mechanisms": [{{{{"principle": "the physical/chemical principle", "physical_effect_tag": "{TAGS}", "evidence": "what supports this"}}}}],
 "applications": [  // exactly 5, best first
   {{{{"application": "engineering application", "problem": "the engineering problem it solves", "mapping": "biological feature -> engineered feature", "why_it_works": "physical reasoning incl. scale/regime", "physical_effect_tag": "{TAGS}"}}}}
 ]
}}}}"""

BLUEPRINT = """You are a senior design engineer. Produce an implementable concept blueprint (not a full drawing) for:
APPLICATION: {app}
ENGINEERING PROBLEM: {problem}
{bio}
Return ONLY one JSON object:
{{
 "title": "...",
 "summary": "3-4 sentences",
 "bio_to_engineering_mapping": [{{"biological_feature": "...", "engineering_feature": "...", "scale_change": "..."}}],
 "geometry": [{{"part": "...", "dimension": "...", "value": number, "unit": "SI unit"}}],
 "materials": [{{"part": "...", "material": "...", "reason": "..."}}],
 "manufacturing_steps": ["..."],
 "quick_physics_check": [{{"quantity": "...", "equation": "...", "estimate": number, "unit": "...", "requirement": "..."}}],
 "expected_performance": "...",
 "limitations_and_risks": ["..."],
 "render_prompt": "one-sentence prompt for a clean technical concept sketch of the device"
}}"""

NOBIO = "Design the most innovative effective solution you can. No biological source is given; use conventional or novel engineering ideas as you see fit."


def data_url(p: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def parse_json(t: str):
    t = re.sub(r"```(json)?", "", t)
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b <= a:
        return None
    s = t[a : b + 1]
    s = re.sub(r"//[^\n]*", "", s)
    try:
        return json.loads(s)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default="/home/abhishek24024/flbds_data/models/Qwen3-VL-32B-Instruct-FP8",
    )
    ap.add_argument("--images", default=str(ROOT / "flbds/v11/data/images"))
    ap.add_argument("--out", default="/home/abhishek24024/flbds_data/v11/e1e2")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--temperature", type=float, default=0.7)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from vllm import LLM, SamplingParams

    cases = json.loads((ROOT / "flbds/v11/data/organisms.json").read_text())["cases"]
    imgdir = Path(a.images)
    cases = [c for c in cases if (imgdir / f"{c['id']}.jpg").exists()]
    print("cases with images:", len(cases), flush=True)
    llm = LLM(
        model=a.model,
        max_model_len=16384,
        gpu_memory_utilization=0.88,
        limit_mm_per_prompt={"image": 1},
        trust_remote_code=True,
    )

    convs, meta = [], []
    for c in cases:
        name = f"Organism: {c['common']} ({c['scientific']})."
        for arm in ("IMG", "NAME", "IMG+NAME"):
            subj = {
                "IMG": "Here is a photograph of an organism (no name given).",
                "NAME": name + " (No image is available; rely on your knowledge.)",
                "IMG+NAME": name + " Here is a photograph of it.",
            }[arm]
            content = [{"type": "text", "text": PERCEIVE.format(subject=subj)}]
            if arm != "NAME":
                content.insert(
                    0,
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url(imgdir / f"{c['id']}.jpg")},
                    },
                )
            for s in a.seeds:
                convs.append([{"role": "user", "content": content}])
                meta.append({"case": c["id"], "arm": arm, "seed": s})
    sps = [
        SamplingParams(
            temperature=a.temperature,
            top_p=0.9,
            max_tokens=2000,
            seed=m["seed"] * 1000 + i,
        )
        for i, m in enumerate(meta)
    ]
    outs = llm.chat(convs, sps)
    rows = []
    for m, o in zip(meta, outs):
        t = o.outputs[0].text
        rows.append(
            {
                **m,
                "raw": t,
                "parsed": parse_json(t),
                "tokens": len(o.outputs[0].token_ids),
            }
        )
    with open(out / "e1_perception.jsonl", "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(
        "perception done; parsed",
        sum(r["parsed"] is not None for r in rows),
        "/",
        len(rows),
        flush=True,
    )

    # ---- Mode B blueprint for top application, plus NOBIO control on the same application
    bconvs, bmeta = [], []
    cmap = {c["id"]: c for c in cases}
    for r in rows:
        p = r["parsed"]
        if not p or not p.get("applications"):
            continue
        app = p["applications"][0]
        org = p.get("organism", {})
        bio = (
            f"BIOLOGICAL SOURCE: {org.get('common')} ({org.get('scientific')}). Mechanisms: "
            + "; ".join(x.get("principle", "") for x in p.get("mechanisms", [])[:3])
            + f". Mapping: {app.get('mapping')}. Base the design on this biological mechanism."
        )
        for variant, biotext in (("BIO", bio), ("NOBIO", NOBIO)):
            if variant == "NOBIO" and r["seed"] != a.seeds[0]:
                continue  # one control per (case, arm)
            prompt = BLUEPRINT.format(
                app=app.get("application"), problem=app.get("problem"), bio=biotext
            )
            bconvs.append(
                [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            )
            bmeta.append(
                {
                    "case": r["case"],
                    "arm": r["arm"],
                    "seed": r["seed"],
                    "variant": variant,
                    "application": app,
                }
            )
    bsps = [
        SamplingParams(
            temperature=a.temperature, top_p=0.9, max_tokens=2500, seed=7000 + i
        )
        for i in range(len(bmeta))
    ]
    bouts = llm.chat(bconvs, bsps)
    with open(out / "e2_blueprints.jsonl", "w") as f:
        for m, o in zip(bmeta, bouts):
            t = o.outputs[0].text
            f.write(json.dumps({**m, "raw": t, "parsed": parse_json(t)}) + "\n")
    print("blueprints done:", len(bmeta), flush=True)


if __name__ == "__main__":
    main()
