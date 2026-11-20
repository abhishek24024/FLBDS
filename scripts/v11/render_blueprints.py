#!/usr/bin/env python3
"""Render concept-sketch images for selected blueprints with Qwen-Image (diffusers). Illustrative only:
the authoritative design is the blueprint JSON (dimensions, materials, physics check)."""

import argparse
import json
from pathlib import Path

import torch
from diffusers import QwenImagePipeline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model", default="/home/abhishek24024/flbds_data/models/Qwen-Image"
    )
    ap.add_argument("--dir", default="/home/abhishek24024/flbds_data/v11/e1e2")
    ap.add_argument(
        "--cases",
        nargs="+",
        default=["B01", "B02", "B03", "B04", "B07", "B09", "B06", "B11"],
    )
    ap.add_argument("--steps", type=int, default=40)
    a = ap.parse_args()
    d = Path(a.dir)
    (d / "renders").mkdir(exist_ok=True)
    bps = [json.loads(l) for l in open(d / "e2_blueprints.jsonl")]
    pick = {}
    for b in bps:  # first parsed IMG-arm BIO blueprint per case
        if (
            b["variant"] == "BIO"
            and b["arm"] == "IMG"
            and b["parsed"]
            and b["case"] in a.cases
            and b["case"] not in pick
        ):
            pick[b["case"]] = b
    pipe = QwenImagePipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16).to(
        "cuda"
    )
    meta = {}
    for cid, b in pick.items():
        p = b["parsed"]
        dims = "; ".join(
            f"{g.get('part')} {g.get('dimension')} {g.get('value')} {g.get('unit')}"
            for g in (p.get("geometry") or [])[:5]
        )
        prompt = (
            f"Clean engineering concept sketch, blueprint style, white background, thin dark-blue linework, "
            f"isometric view with one cut-away detail and short English labels. Device: {p.get('title')}. "
            f"{p.get('render_prompt', '')} Key parts: {dims}."
        )
        img = pipe(
            prompt=prompt,
            negative_prompt="photo, blurry, clutter, watermark",
            width=1328,
            height=928,
            num_inference_steps=a.steps,
            true_cfg_scale=4.0,
            generator=torch.Generator("cuda").manual_seed(42),
        ).images[0]
        img.save(d / "renders" / f"{cid}.png")
        meta[cid] = {"title": p.get("title"), "prompt": prompt}
        print("rendered", cid, flush=True)
    (d / "renders" / "render_meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
