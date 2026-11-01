#!/usr/bin/env python3
"""Phase C: Critic Tests on Verified Cards (FLBDS Audit Round 5).

Implements and evaluates:
(i) Document-level relevance step:
    "Does this document describe a thermal, fluid or porous transport mechanism?
     Copy one sentence from it that shows this."
    Accept ONLY if the sentence is a verbatim substring of doc_text.

(ii) Quote-required critic for action and effect:
    Return a supporting sentence copied verbatim from the cited evidence;
    reject if it is not a substring of the cited evidence.

Evaluated on:
- 24 cards from Seed 11 sample: 7 GOOD, 10 MINOR, 7 MAJOR.
  (Goal: MAJOR cards must be rejected; report confusion matrix and doc IDs).
- 133 silver cards from pilot corpus (silver_cards.jsonl):
  Report how many fail step (i), and show 10 verbatim examples with source titles.
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ["PATH"] = "/home/abhishek24024/flbds_env/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, "/home/abhishek24024/flbds")

from vllm import LLM, SamplingParams
from pydantic import BaseModel, Field


def load_corpus(data_dir: Path):
    corpus = {}
    for fn in ["bio_pilot.jsonl", "eng_pilot.jsonl"]:
        fp = data_dir / "corpus" / fn
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        doc_id = d.get("doc_id") or d.get("id") or d.get("pmcid") or d.get("patent_id")
                        corpus[doc_id] = d
    return corpus


def extract_json(text: str) -> dict | None:
    text = text.strip()
    import re
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None


def main():
    data_dir = Path("/home/abhishek24024/flbds_data")
    out_dir = data_dir / "audit5"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading corpus records...")
    corpus = load_corpus(data_dir)
    print(f"Loaded {len(corpus)} corpus documents.")

    # 1. Load Seed 11 24 cards
    with open(data_dir / "review" / "agent_verdicts_seed11.json", "r") as f:
        s11_data = json.load(f)
    s11_audits = s11_data.get("all_card_audits", [])
    print(f"Loaded {len(s11_audits)} Seed 11 card audits.")

    # 2. Load 133 silver cards
    silver_cards = []
    with open(data_dir / "pilot" / "silver_cards.jsonl", "r") as f:
        for line in f:
            if line.strip():
                silver_cards.append(json.loads(line))
    print(f"Loaded {len(silver_cards)} silver cards.")

    # Initialize vLLM with Qwen2.5-7B-Instruct
    model_dir = "/home/abhishek24024/flbds_data/models/Qwen2.5-7B-Instruct"
    print(f"Initializing vLLM with {model_dir}...")
    t0 = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.85,
        trust_remote_code=True
    )
    print(f"Model loaded in {time.perf_counter() - t0:.2f} s.")

    sp = SamplingParams(temperature=0.0, max_tokens=512)

    # -------------------------------------------------------------
    # Step (i): Document-Level Relevance on 133 Silver Cards
    # -------------------------------------------------------------
    print("\n--- Running Step (i): Document-Level Relevance on 133 Silver Cards ---")
    step_i_prompts = []
    step_i_metadata = []

    for sc in silver_cards:
        doc_id = sc.get("doc_id")
        title = sc.get("title", "")
        rec = corpus.get(doc_id, {})
        full_text = rec.get("text", "") or sc.get("text", "")
        # Use title + abstract + first 3000 chars of body
        abstract = rec.get("abstract", "")
        sample_text = f"Title: {title}\nAbstract: {abstract}\nText: {full_text[:3500]}"

        prompt = (
            f"<|im_start|>system\nYou are an expert physical reviewer for thermal, fluid, and porous transport systems.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Does this document describe a thermal, fluid or porous transport mechanism? "
            f"Copy one sentence from it that shows this.\n\n"
            f"Document Title: {title}\n"
            f"Document Text:\n\"\"\"\n{sample_text}\n\"\"\"\n\n"
            f"Respond strictly in JSON format:\n"
            f"{{\n"
            f'  "describes_mechanism": true | false,\n'
            f'  "verbatim_sentence": "<exact sentence copied verbatim from the document text showing thermal, fluid, or porous transport>",\n'
            f'  "mechanism_type": "thermal" | "fluid" | "porous" | "none"\n'
            f"}}\n"
            f"If it does not describe such a mechanism, set describes_mechanism=false and verbatim_sentence=\"\".<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        step_i_prompts.append(prompt)
        step_i_metadata.append({
            "doc_id": doc_id,
            "title": title,
            "full_text": full_text
        })

    outs_i = llm.generate(step_i_prompts, sp)

    step_i_results = []
    step_i_fails = []
    step_i_passes = []

    for meta, out in zip(step_i_metadata, outs_i):
        doc_id = meta["doc_id"]
        title = meta["title"]
        full_text = meta["full_text"]
        raw = out.outputs[0].text
        parsed = extract_json(raw)

        passed = False
        reason = "unknown"
        quoted_sentence = ""

        if not parsed:
            reason = "invalid_json_output"
        elif not parsed.get("describes_mechanism", False):
            reason = "model_judged_not_relevant"
        else:
            quoted_sentence = parsed.get("verbatim_sentence", "").strip()
            if not quoted_sentence:
                reason = "empty_verbatim_sentence"
            elif quoted_sentence in full_text:
                passed = True
                reason = "exact_verbatim_substring_matched"
            else:
                # Check normalized whitespace
                norm_q = " ".join(quoted_sentence.split())
                norm_t = " ".join(full_text.split())
                if norm_q in norm_t:
                    passed = True
                    reason = "whitespace_normalized_substring_matched"
                else:
                    reason = "sentence_not_in_document_substring_failure"

        res_entry = {
            "doc_id": doc_id,
            "title": title,
            "passed": passed,
            "reason": reason,
            "quoted_sentence": quoted_sentence,
            "raw_response": raw
        }
        step_i_results.append(res_entry)
        if passed:
            step_i_passes.append(res_entry)
        else:
            step_i_fails.append(res_entry)

    print(f"Step (i) Evaluation on 133 Silver Cards:")
    print(f"  Passed: {len(step_i_passes)} / 133 ({len(step_i_passes)/133*100:.1f}%)")
    print(f"  Failed: {len(step_i_fails)} / 133 ({len(step_i_fails)/133*100:.1f}%)")

    # -------------------------------------------------------------
    # Step (ii): Quote-Required Critic on 24 Seed 11 Cards
    # -------------------------------------------------------------
    print("\n--- Running Step (i) & (ii) on 24 Seed 11 Cards ---")
    step_ii_prompts = []
    step_ii_meta = []

    # Map cards from silver_cards or stage 4
    cards_map = {sc["doc_id"]: sc for sc in silver_cards}

    for a in s11_audits:
        doc_id = a.get("doc_id")
        verdict = a.get("verdict")
        domain = a.get("domain")
        title = a.get("title", "")
        sc = cards_map.get(doc_id, {})
        card = sc.get("card", {})
        evidence_spans = card.get("evidence", [])
        evidence_text = "\n".join(f"- \"{ev.get('text_span', '')}\"" for ev in evidence_spans)
        rec = corpus.get(doc_id, {})
        full_text = rec.get("text", "")

        action = card.get("action", {})
        effect = card.get("effect", {})
        subject = card.get("subject", {})

        prompt = (
            f"<|im_start|>system\nYou are a strict physics verifier assessing whether cited evidence supports a claimed causal mechanism.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Review this Mechanism Card's claimed Action and Physical Effect against its Cited Evidence Spans.\n"
            f"Claimed Subject: {subject}\n"
            f"Claimed Action: {action}\n"
            f"Claimed Physical Effect: {effect}\n\n"
            f"Cited Evidence Spans:\n\"\"\"\n{evidence_text}\n\"\"\"\n\n"
            f"Question: Does the cited evidence support this action and physical effect? Return a supporting sentence copied verbatim from the cited evidence; reject if it is not a substring of the cited evidence.\n\n"
            f"Respond strictly in JSON format:\n"
            f"{{\n"
            f'  "supported": true | false,\n'
            f'  "supporting_sentence": "<exact supporting sentence copied verbatim from the cited evidence>",\n'
            f'  "reason": "<explanation of physical entailment or why evidence fails to support the action/effect>"\n'
            f"}}\n"
            f"If the evidence does not support the action and effect, set supported=false and supporting_sentence=\"\".<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        step_ii_prompts.append(prompt)
        step_ii_meta.append({
            "doc_id": doc_id,
            "verdict": verdict,
            "domain": domain,
            "title": title,
            "evidence_text": evidence_text,
            "full_text": full_text
        })

    outs_ii = llm.generate(step_ii_prompts, sp)

    step_ii_results = []
    confusion = {
        "GOOD": {"accepted": 0, "rejected": 0, "doc_ids": []},
        "MINOR": {"accepted": 0, "rejected": 0, "doc_ids": []},
        "MAJOR": {"accepted": 0, "rejected": 0, "doc_ids": []}
    }

    for meta, out in zip(step_ii_meta, outs_ii):
        doc_id = meta["doc_id"]
        verdict = meta["verdict"]
        ev_text = meta["evidence_text"]
        raw = out.outputs[0].text
        parsed = extract_json(raw)

        accepted = False
        rejection_reason = "unknown"
        quoted_sentence = ""

        if not parsed:
            rejection_reason = "invalid_json"
        elif not parsed.get("supported", False):
            rejection_reason = parsed.get("reason", "model_rejected_unsupported")
        else:
            quoted_sentence = parsed.get("supporting_sentence", "").strip()
            if not quoted_sentence:
                rejection_reason = "empty_supporting_sentence"
            elif quoted_sentence in ev_text:
                accepted = True
                rejection_reason = "supported_and_exact_substring"
            else:
                norm_q = " ".join(quoted_sentence.split())
                norm_ev = " ".join(ev_text.split())
                if norm_q in norm_ev:
                    accepted = True
                    rejection_reason = "supported_and_whitespace_normalized_substring"
                else:
                    rejection_reason = "quote_not_substring_of_cited_evidence"

        status_str = "ACCEPTED" if accepted else "REJECTED"
        if accepted:
            confusion[verdict]["accepted"] += 1
        else:
            confusion[verdict]["rejected"] += 1
        confusion[verdict]["doc_ids"].append({"doc_id": doc_id, "status": status_str, "reason": rejection_reason})

        step_ii_results.append({
            "doc_id": doc_id,
            "verdict": verdict,
            "domain": meta["domain"],
            "title": meta["title"],
            "critic_decision": status_str,
            "reason": rejection_reason,
            "quoted_sentence": quoted_sentence
        })

    print("\nConfusion Matrix on 24 Seed 11 Cards (Critic Step ii):")
    print("=" * 65)
    print(f"{'Human Verdict':<15} | {'Critic Accept':<15} | {'Critic Reject':<15} | {'Accept Rate':<10}")
    print("-" * 65)
    for v in ["GOOD", "MINOR", "MAJOR"]:
        acc = confusion[v]["accepted"]
        rej = confusion[v]["rejected"]
        tot = acc + rej
        rate = f"{acc/tot*100:.1f}%" if tot > 0 else "N/A"
        print(f"{v:<15} | {acc:<15} | {rej:<15} | {rate:<10}")
    print("=" * 65)

    # Save artifacts
    critic_output = {
        "step_i_summary": {
            "total_silver_cards": len(silver_cards),
            "step_i_passed": len(step_i_passes),
            "step_i_failed": len(step_i_fails),
            "pass_rate": len(step_i_passes) / len(silver_cards),
            "failed_samples_10": step_i_fails[:10]
        },
        "step_ii_confusion_matrix": confusion,
        "step_ii_card_results": step_ii_results
    }

    out_path = out_dir / "critic_test_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(critic_output, f, indent=2)

    print(f"\nSaved critic test results to {out_path}")


if __name__ == "__main__":
    main()
