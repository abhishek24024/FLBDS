#!/usr/bin/env python3
"""scripts/audit11_check_offsets.py
Audit Round 11 Item A1: Reconcile Character Offsets between Round 3 and Round 10.
Analyzes PMC8593863, US-PAT-E-0478, US-PAT-E-0427, and US-PAT-F-0220.
"""

import json
from pathlib import Path

def main():
    corpus_dir = Path("/home/abhishek24024/flbds_data/corpus")
    if not corpus_dir.exists():
        corpus_dir = Path("flbds_data/corpus")

    docs = {}
    for cname in ["bio_pilot.jsonl", "eng_pilot.jsonl"]:
        cpath = corpus_dir / cname
        if cpath.exists():
            with open(cpath) as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    did = d.get("doc_id") or d.get("id")
                    if did:
                        docs[did] = d

    targets = {
        "PMC8593863": {
            "quote": "liquid transport in fluidic channels produced by stencil printing on flexible substrates",
            "quote_len": 88,
            "r3_offsets": (2908, 2996),
            "r10_offsets": (2775, 2863),
        },
        "US-PAT-E-0478": {
            "quote": "The overlapping annulus insulation and joint insulation essentially provides continuous insulation along the tubular assembly, minimizing heat loss at the joint.",
            "quote_len": 161,
            "r3_offsets": (4993, 5154),
            "r10_offsets": (4195, 4356),
        },
        "US-PAT-E-0427": {
            "quote": "a floor assembly bounding a bottom portion of the interior chamber and providing a thermal insulating layer;",
            "quote_len": 108,
            "r3_offsets": (3135, 3243),
            "r10_offsets": (2322, 2430),
        },
        "US-PAT-F-0220": {
            "quote": "In aircraft, dozens of meters of piping are arranged to collect air at high temperatures (260 to 540\u00b0 C.) or under pressure (5 to 15 bar) from certain areas, such as at the engines, and to distribute that air to treatment systems that particularly make it possible to supply conditioned and/or pressurized air to specific spaces such as the cabin, in the passenger area, or provide hot air to the wings of the aircraft in order to defrost their leading edges.",
            "quote_len": 459,
            "r3_offsets": (1468, 1927),
            "r10_offsets": (902, 1361),
        }
    }

    print("=" * 80)
    print("AUDIT ROUND 11 - ITEM A1: OFFSET RECONCILIATION & CORPUS SLICES")
    print("=" * 80)

    for did, info in targets.items():
        d = docs[did]
        title = d.get("title", "")
        abstract = d.get("abstract", "")
        text = d.get("text", "")
        parts = [p for p in [title, abstract, text] if p]
        full_text = "\n".join(parts)

        q = info["quote"]
        r3_s, r3_e = info["r3_offsets"]
        r10_s, r10_e = info["r10_offsets"]

        prefix = "\n".join([p for p in [title, abstract] if p]) + ("\n" if parts else "")
        prefix_len = len(prefix)

        print(f"\n[CARD ID: {did}] (Expected Quote Length: {info['quote_len']} chars)")
        print(f"  Title: {title[:70]}...")
        print(f"  Title Length: {len(title)} | Abstract Length: {len(abstract)} | Prefix Length: {prefix_len}")
        print(f"  Offset Shift: R3 ({r3_s}:{r3_e}) - R10 ({r10_s}:{r10_e}) = {r3_s - r10_s} chars (== prefix length: {prefix_len == (r3_s - r10_s)})")
        print(f"  Target Quote: {repr(q[:60])}...")

        # 1. Evaluate against full_text (scripts/verify_quotes.py definition)
        slice_full_r3 = full_text[r3_s:r3_e]
        slice_full_r10 = full_text[r10_s:r10_e]
        print(f"  full_text[{r3_s}:{r3_e}] (R3)  == quote? {slice_full_r3 == q} (len: {len(slice_full_r3)})")
        if slice_full_r3 != q:
            print(f"    Mismatch content: {repr(slice_full_r3[:60])}")
        print(f"  full_text[{r10_s}:{r10_e}] (R10) == quote? {slice_full_r10 == q} (len: {len(slice_full_r10)})")
        if slice_full_r10 != q:
            print(f"    Mismatch content: {repr(slice_full_r10[:60])}")

        # 2. Evaluate against doc['text'] (body-only definition)
        slice_body_r3 = text[r3_s:r3_e]
        slice_body_r10 = text[r10_s:r10_e]
        print(f"  doc['text'][{r3_s}:{r3_e}] (R3)  == quote? {slice_body_r3 == q} (len: {len(slice_body_r3)})")
        if slice_body_r3 != q:
            print(f"    Mismatch content: {repr(slice_body_r3[:60])}")
        print(f"  doc['text'][{r10_s}:{r10_e}] (R10) == quote? {slice_body_r10 == q} (len: {len(slice_body_r10)})")
        if slice_body_r10 != q:
            print(f"    Mismatch content: {repr(slice_body_r10[:60])}")

    print("\n" + "=" * 80)
    print("SCRIPTS/VERIFY_QUOTES.PY IMPLEMENTATION CHECK")
    print("=" * 80)
    with open("scripts/verify_quotes.py") as f:
        v_lines = f.readlines()
    print("Lines 102-116 of scripts/verify_quotes.py:")
    for i in range(101, 116):
        print(f"  {i+1}: {v_lines[i]}", end="")

if __name__ == "__main__":
    main()
