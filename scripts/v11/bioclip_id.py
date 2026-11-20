#!/usr/bin/env python3
"""BioCLIP 2 closed-list identification on the V11 organism photos (CPU). Candidates = the gold set's scientific names
plus distractor taxa (common look-alikes), text prompt 'a photo of <name>'. Reports top-1/top-5 vs the VLM's 64%."""
import json, sys
from pathlib import Path
import torch, open_clip
from PIL import Image

ROOT = Path(sys.argv[1])
M = "/home/abhishek24024/flbds_data/models/bioclip-2"
cases = json.loads((ROOT / "flbds/v11/data/organisms.json").read_text())["cases"]
DISTRACT = ["Rana temporaria", "Hyla arborea", "Danaus plexippus", "Papilio machaon", "Carcharodon carcharias", "Bombus terrestris",
            "Vespa crabro", "Formica rufa", "Camponotus pennsylvanicus", "Coccinella septempunctata", "Lucanus cervus", "Ardea alba",
            "Egretta garzetta", "Elephas maximus", "Iguana iguana", "Chamaeleo calyptratus", "Nymphaea alba", "Rosa canina",
            "Taraxacum officinale", "Pinus sylvestris", "Quercus robur", "Spheniscus demersus", "Mytilus galloprovincialis",
            "Tursiops truncatus", "Balaenoptera musculus", "Alcedo cristata", "Xanthium strumarium", "Sarracenia purpurea",
            "Drosera rotundifolia", "Lepisma saccharinum"]
names = [c["scientific"].split(" (")[0].split(" e.g.")[0] for c in cases] + DISTRACT
model, _, pre = open_clip.create_model_and_transforms("local-dir:" + M)
tok = open_clip.get_tokenizer("local-dir:" + M)
model.eval()
with torch.no_grad():
    t = model.encode_text(tok([f"a photo of {n}." for n in names])); t /= t.norm(dim=-1, keepdim=True)
res = {}
for i, c in enumerate(cases):
    p = ROOT / "flbds/v11/data/images" / f"{c['id']}.jpg"
    if not p.exists():
        continue
    with torch.no_grad():
        v = model.encode_image(pre(Image.open(p).convert("RGB")).unsqueeze(0)); v /= v.norm(dim=-1, keepdim=True)
    s = (v @ t.T).squeeze(0); top = s.topk(5).indices.tolist()
    res[c["id"]] = {"gold": names[i], "top5": [names[j] for j in top], "top1_ok": top[0] == i, "top5_ok": i in top}
n = len(res)
print(json.dumps(res, indent=0)[:1500])
print("top1", sum(r["top1_ok"] for r in res.values()), "/", n, " top5", sum(r["top5_ok"] for r in res.values()), "/", n, " candidates", len(names))
(ROOT / "bioclip_id_results.json").write_text(json.dumps({"n_candidates": len(names), "results": res}, indent=1))
