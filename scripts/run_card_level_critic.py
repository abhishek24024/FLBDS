#!/usr/bin/env python3
"""scripts/run_card_level_critic.py
Tests a CARD-LEVEL critic per Audit Round 7 Prompt P2:
Gives the model Title, Abstract, and First Claim / introductory text,
and asks whether the card's action and effect are the document's PRIMARY mechanism.
Rejects unless it copies a verbatim sentence that states it.
Evaluates on:
- 24 Seed-11 cards (cross-tabulated against human verdicts: GOOD, MINOR, MAJOR)
- 133 Silver Cards
Outputs accept rates, 95% Wilson intervals, and doc IDs of any rejected GOOD cards.
Saved to flbds_data/audit7/card_level_critic_results.json.
"""

import json
import math
import re
import sys
import time
from pathlib import Path
import numpy as np

from vllm import LLM, SamplingParams


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2.0 * n)) / denom
    half_width = (z * np.sqrt((p * (1.0 - p) + (z**2) / (4.0 * n)) / n)) / denom
    return (round(max(0.0, float(center - half_width)), 4), round(min(1.0, float(center + half_width)), 4))


def extract_json(text: str) -> dict:
    t = text.strip()
    match = re.search(r"\{.*\}", t, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


def extract_first_claim(text: str) -> str:
    """Extracts first claim or introductory text snippet."""
    patterns = [
        r"(?:what is claimed is|we claim|claims:?)\s*(?:1\.\s*)?([^\n]+(?:\n[^\n]+){1,10})",
        r"\b1\.\s+([A-Z][^\n]+(?:\n[^\n]+){1,8})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:1200]
    # Fallback to first 1200 chars of text after title
    return text[:1200].strip()


def main():
    out_dir = Path("/home/abhishek24024/flbds_data/audit7")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load corpus
    corpus = {}
    for cpath in [Path("/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl"), Path("/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl")]:
        if cpath.exists():
            with open(cpath) as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        corpus[d["doc_id"]] = d

    # 2. Load 133 silver cards
    silver_cards = []
    silver_path = Path("/home/abhishek24024/flbds_data/pilot/silver_cards.jsonl")
    with open(silver_path) as f:
        for line in f:
            if line.strip():
                silver_cards.append(json.loads(line))

    # 3. Load 24 seed-11 cards
    s11_path = Path("/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json")
    s11_data = json.loads(s11_path.read_text())
    s11_audits = s11_data["all_card_audits"]

    print(f"Loaded {len(silver_cards)} silver cards and {len(s11_audits)} seed-11 audits.")

    # Model init
    model_dir = "/home/abhishek24024/flbds_data/models/Qwen2.5-32B-Instruct-FP8"
    print(f"Loading 32B model: {model_dir}...")
    llm = LLM(
        model=model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.85,
        trust_remote_code=True,
    )
    sp = SamplingParams(temperature=0.0, max_tokens=512)

    # Combine unique cards to evaluate
    all_eval_items = []
    seen_ids = set()

    for item in s11_audits:
        doc_id = item["doc_id"]
        seen_ids.add(doc_id)
        c_fields = item.get("card_fields", {})
        all_eval_items.append({
            "doc_id": doc_id,
            "source": "seed11",
            "verdict": item.get("verdict"),
            "action": c_fields.get("action"),
            "effect": c_fields.get("effect"),
        })

    for sc in silver_cards:
        doc_id = sc["doc_id"]
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            c = sc.get("card", {})
            all_eval_items.append({
                "doc_id": doc_id,
                "source": "silver133",
                "verdict": None,
                "action": c.get("action"),
                "effect": c.get("effect"),
            })

    print(f"Total unique documents to evaluate: {len(all_eval_items)}")

    prompts = []
    meta_list = []

    for item in all_eval_items:
        doc_id = item["doc_id"]
        rec = corpus.get(doc_id, {})
        title = rec.get("title", "")
        abstract = rec.get("abstract", "")
        full_text = rec.get("text", "")
        first_claim = extract_first_claim(full_text)

        action_str = json.dumps(item["action"])
        effect_str = json.dumps(item["effect"])

        prompt = (
            f"<|im_start|>system\nYou are a rigorous scientific reviewer determining whether an extracted mechanism represents the primary physical function of a technical document.\n"
            f"Task: Evaluate whether the Asserted Action and Effect represent the PRIMARY transport/physical mechanism of the document.\n"
            f"Strict acceptance rules:\n"
            f"1. Accept ONLY if the asserted action and effect constitute the primary physical working principle of the document.\n"
            f"2. You MUST copy ONE exact sentence verbatim from the document text that explicitly states this action and effect as the core mechanism.\n"
            f"3. Reject if the mechanism is secondary, incidental, a control peripheral (e.g. electrical PID control), or not the main subject.\n"
            f"4. Reject if the supporting sentence is not an exact verbatim substring of the document text.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Document Title: {title}\n"
            f"Abstract: {abstract}\n"
            f"Primary Claim / Intro Excerpt:\n\"\"\"\n{first_claim}\n\"\"\"\n\n"
            f"Asserted Action: {action_str}\n"
            f"Asserted Effect: {effect_str}\n\n"
            f"Question: Are this action and effect the document's primary physical mechanism?\n"
            f"Respond strictly in JSON format:\n"
            f"{{\n"
            f'  "is_primary_mechanism": true | false,\n'
            f'  "verbatim_sentence": "<exact sentence copied verbatim from the document demonstrating this is the primary mechanism>",\n'
            f'  "reason": "<rigorous physical explanation of why this is or is not the primary mechanism>"\n'
            f"}}\n"
            f"If rejected, set is_primary_mechanism=false and verbatim_sentence=\"\".<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        prompts.append(prompt)
        meta_list.append({
            "doc_id": doc_id,
            "title": title,
            "full_text": full_text,
            "verdict": item["verdict"],
            "source": item["source"],
            "action": item["action"],
            "effect": item["effect"],
        })

    print(f"Generating Card-Level Critic assessments for {len(prompts)} items...")
    outs = llm.generate(prompts, sp)

    results_by_doc = {}

    for meta, out in zip(meta_list, outs):
        doc_id = meta["doc_id"]
        full_text = meta["full_text"]
        raw = out.outputs[0].text
        parsed = extract_json(raw)

        accepted = False
        reason = "unknown"
        quoted = ""

        if parsed.get("is_primary_mechanism") is True:
            quoted = parsed.get("verbatim_sentence", "").strip()
            if quoted:
                if quoted in full_text:
                    accepted = True
                    reason = "accepted_verbatim_primary_mechanism"
                else:
                    norm_q = " ".join(quoted.split())
                    norm_d = " ".join(full_text.split())
                    if norm_q.lower() in norm_d.lower():
                        accepted = True
                        reason = "accepted_whitespace_normalized"
                    else:
                        reason = "quoted_sentence_not_in_document"
            else:
                reason = "missing_verbatim_sentence"
        else:
            reason = parsed.get("reason", "rejected_not_primary_mechanism")

        results_by_doc[doc_id] = {
            "doc_id": doc_id,
            "title": meta["title"],
            "verdict": meta["verdict"],
            "source": meta["source"],
            "accepted": accepted,
            "reason": reason,
            "quoted_sentence": quoted,
            "action": meta["action"],
            "effect": meta["effect"],
        }

    # 1. Cross-tabulation on Seed-11 (N=24)
    s11_crosstab = {
        "GOOD": {"total": 0, "accepted": 0, "rejected": 0, "rejected_doc_ids": []},
        "MINOR": {"total": 0, "accepted": 0, "rejected": 0, "rejected_doc_ids": []},
        "MAJOR": {"total": 0, "accepted": 0, "rejected": 0, "rejected_doc_ids": []},
    }

    for audit in s11_audits:
        doc_id = audit["doc_id"]
        v = audit["verdict"]
        res = results_by_doc[doc_id]
        s11_crosstab[v]["total"] += 1
        if res["accepted"]:
            s11_crosstab[v]["accepted"] += 1
        else:
            s11_crosstab[v]["rejected"] += 1
            s11_crosstab[v]["rejected_doc_ids"].append(doc_id)

    for v in ["GOOD", "MINOR", "MAJOR"]:
        tot = s11_crosstab[v]["total"]
        acc = s11_crosstab[v]["accepted"]
        rate = round(acc / tot, 4) if tot > 0 else 0.0
        ci = wilson_score_interval(acc, tot)
        s11_crosstab[v]["accept_rate"] = rate
        s11_crosstab[v]["wilson_ci_95"] = ci

    # 2. Performance on 133 Silver Cards
    silver_acc = 0
    silver_rej = 0
    silver_details = []

    for sc in silver_cards:
        doc_id = sc["doc_id"]
        res = results_by_doc[doc_id]
        if res["accepted"]:
            silver_acc += 1
        else:
            silver_rej += 1
        silver_details.append({
            "doc_id": doc_id,
            "accepted": res["accepted"],
            "reason": res["reason"],
            "quoted": res["quoted_sentence"],
        })

    silver_summary = {
        "total": len(silver_cards),
        "accepted": silver_acc,
        "rejected": silver_rej,
        "accept_rate": round(silver_acc / len(silver_cards), 4),
        "wilson_ci_95": wilson_score_interval(silver_acc, len(silver_cards)),
    }

    final_payload = {
        "test_name": "Card-Level Primary Mechanism Critic Evaluation",
        "model": model_dir,
        "seed_11_crosstab": s11_crosstab,
        "good_cards_rejected": s11_crosstab["GOOD"]["rejected_doc_ids"],
        "silver_133_summary": silver_summary,
        "silver_details": silver_details,
        "results_by_doc": results_by_doc,
    }

    out_file = out_dir / "card_level_critic_results.json"
    out_file.write_text(json.dumps(final_payload, indent=2))
    print(f"\nSaved Card-Level Critic results to {out_file}")

    print("\n=== SEED 11 CROSS-TABULATION (N=24) ===")
    for v in ["GOOD", "MINOR", "MAJOR"]:
        d = s11_crosstab[v]
        print(f"  {v:<6}: Accepted {d['accepted']}/{d['total']} ({d['accept_rate']*100:.1f}%) [95% CI: {d['wilson_ci_95']}] | Rejected doc IDs: {d['rejected_doc_ids']}")

    print("\n=== SILVER 133 SUMMARY ===")
    print(f"  Accepted: {silver_summary['accepted']}/{silver_summary['total']} ({silver_summary['accept_rate']*100:.1f}%) [95% CI: {silver_summary['wilson_ci_95']}]")
    print(f"  GOOD Cards Rejected (False Rejections): {final_payload['good_cards_rejected']}")


if __name__ == "__main__":
    main()
