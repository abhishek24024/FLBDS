#!/usr/bin/env python3
"""scripts/run_critic_combined_eval.py
Evaluates:
1. Step (i): Document-level relevance on 133 silver cards and 24 seed-11 cards.
2. Step (ii): Quote-required critic for action and effect on 133 silver cards and 24 seed-11 cards.
3. Combined filter (Step i AND Step ii).
4. Cross-tabulation of Step i x Verdict (GOOD, MINOR, MAJOR) on 24 seed-11 cards.
5. Saves all results to flbds_data/audit6/critic_combined_results.json.
"""

import json
import re
import sys
import time
from pathlib import Path
import numpy as np

from vllm import LLM, SamplingParams

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
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


def main():
    out_dir = Path("/home/abhishek24024/flbds_data/audit6")
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

    # 2. Load 133 silver cards (from pilot or audit6)
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
        trust_remote_code=True
    )
    sp = SamplingParams(temperature=0.0, max_tokens=512)

    # -------------------------------------------------------------------------
    # PART 1: Step (i) Prompts (Relevance) for 133 Silver Cards
    # -------------------------------------------------------------------------
    step_i_prompts = []
    step_i_meta = []
    for sc in silver_cards:
        doc_id = sc["doc_id"]
        title = sc.get("title", "")
        rec = corpus.get(doc_id, {})
        full_text = rec.get("text", "") or sc.get("text", "")
        abstract = rec.get("abstract", "")
        sample_text = f"Title: {title}\nAbstract: {abstract}\nText: {full_text[:3500]}"

        prompt = (
            f"<|im_start|>system\nYou are a precise scientific reviewer assessing technical documents.\n"
            f"Your task: Determine whether the following document text describes a thermal, fluid, or porous transport mechanism.\n"
            f"Examples of in-scope mechanisms: thermal conduction, phase change heat storage, radiative cooling, convection, "
            f"capillary wicking, evaporation, porous media flow, diffusion.\n"
            f"If it describes such a mechanism, identify the mechanism and copy ONE exact sentence from the document text that demonstrates it.\n"
            f"Strict rule: The sentence MUST be copied verbatim as an exact substring from the document text.<|im_end|>\n"
            f"<|im_start|>user\n"
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
        step_i_meta.append({"doc_id": doc_id, "title": title, "full_text": full_text})

    print(f"Generating Step (i) relevance outputs for {len(step_i_prompts)} silver cards...")
    outs_i = llm.generate(step_i_prompts, sp)

    step_i_by_doc = {}
    for meta, out in zip(step_i_meta, outs_i):
        doc_id = meta["doc_id"]
        full_text = meta["full_text"]
        raw = out.outputs[0].text
        parsed = extract_json(raw)

        passed = False
        reason = "unknown"
        quoted = ""
        if parsed.get("describes_mechanism") is True:
            quoted = parsed.get("verbatim_sentence", "").strip()
            if quoted:
                if quoted in full_text:
                    passed = True
                    reason = "supported_and_exact_substring"
                else:
                    norm_q = " ".join(quoted.split())
                    norm_d = " ".join(full_text.split())
                    if norm_q.lower() in norm_d.lower():
                        passed = True
                        reason = "supported_and_whitespace_realigned"
                    else:
                        reason = "sentence_not_in_document_substring_failure"
            else:
                reason = "missing_verbatim_sentence"
        else:
            reason = "model_judged_not_relevant"

        step_i_by_doc[doc_id] = {
            "doc_id": doc_id,
            "title": meta["title"],
            "passed": passed,
            "reason": reason,
            "quoted_sentence": quoted
        }

    # -------------------------------------------------------------------------
    # PART 2: Step (ii) Prompts (Quote-Required Action/Effect) for 133 Silver Cards
    # -------------------------------------------------------------------------
    step_ii_prompts = []
    step_ii_meta = []
    for sc in silver_cards:
        doc_id = sc["doc_id"]
        title = sc.get("title", "")
        card = sc.get("card", {})
        action = card.get("action", {})
        effect = card.get("effect", {})
        evidence_spans = card.get("evidence", [])
        evidence_text = "\n".join(
            f"- \"{ev.get('text_span', '')}\"" if isinstance(ev, dict) else f"- \"{ev}\""
            for ev in evidence_spans
        )

        prompt = (
            f"<|im_start|>system\nYou are a rigorous scientific reviewer verifying physical causal claims.\n"
            f"Your task: evaluate whether the cited evidence strictly entails the asserted action and physical effect.\n"
            f"Strict rule: You MUST copy ONE supporting sentence verbatim from the cited evidence that directly supports the action and physical effect.\n"
            f"If the sentence is not an exact verbatim substring of the cited evidence, or if the evidence fails to support the claim, reject the card.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Document Title: {title}\n\n"
            f"Asserted Action: {json.dumps(action)}\n"
            f"Asserted Physical Effect: {json.dumps(effect)}\n\n"
            f"Cited Evidence Spans:\n{evidence_text}\n\n"
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
        step_ii_meta.append({"doc_id": doc_id, "evidence_text": evidence_text})

    print(f"Generating Step (ii) critic outputs for {len(step_ii_prompts)} silver cards...")
    outs_ii = llm.generate(step_ii_prompts, sp)

    step_ii_by_doc = {}
    for meta, out in zip(step_ii_meta, outs_ii):
        doc_id = meta["doc_id"]
        ev_text = meta["evidence_text"]
        raw = out.outputs[0].text
        parsed = extract_json(raw)

        accepted = False
        reason = "unknown"
        quoted = ""
        if parsed.get("supported") is True:
            quoted = parsed.get("supporting_sentence", "").strip()
            if quoted:
                if quoted in ev_text:
                    accepted = True
                    reason = "supported_and_exact_substring"
                else:
                    norm_q = " ".join(quoted.split())
                    norm_e = " ".join(ev_text.split())
                    if norm_q.lower() in norm_e.lower():
                        accepted = True
                        reason = "supported_and_whitespace_realigned"
                    else:
                        reason = "quote_not_substring_of_cited_evidence"
            else:
                reason = "missing_supporting_sentence"
        else:
            reason = parsed.get("reason", "evidence_does_not_support_action_effect")

        step_ii_by_doc[doc_id] = {
            "doc_id": doc_id,
            "accepted": accepted,
            "reason": reason,
            "quoted_sentence": quoted
        }

    # -------------------------------------------------------------------------
    # PART 3: Cross-Tabulation on 24 Seed-11 Cards
    # -------------------------------------------------------------------------
    s11_verdicts = {c["doc_id"]: c["verdict"] for c in s11_audits}
    crosstab_step_i = {
        "GOOD": {"passed": 0, "failed": 0, "doc_ids_failed": []},
        "MINOR": {"passed": 0, "failed": 0, "doc_ids_failed": []},
        "MAJOR": {"passed": 0, "failed": 0, "doc_ids_failed": []}
    }

    crosstab_combined = {
        "GOOD": {"passed": 0, "failed": 0, "doc_ids": []},
        "MINOR": {"passed": 0, "failed": 0, "doc_ids": []},
        "MAJOR": {"passed": 0, "failed": 0, "doc_ids": []}
    }

    for c in s11_audits:
        doc_id = c["doc_id"]
        verdict = c["verdict"]

        res_i = step_i_by_doc.get(doc_id, {"passed": False})
        res_ii = step_ii_by_doc.get(doc_id, {"accepted": False})

        if res_i["passed"]:
            crosstab_step_i[verdict]["passed"] += 1
        else:
            crosstab_step_i[verdict]["failed"] += 1
            crosstab_step_i[verdict]["doc_ids_failed"].append(doc_id)

        comb_pass = res_i["passed"] and res_ii["accepted"]
        if comb_pass:
            crosstab_combined[verdict]["passed"] += 1
        else:
            crosstab_combined[verdict]["failed"] += 1
        crosstab_combined[verdict]["doc_ids"].append({
            "doc_id": doc_id,
            "step_i": res_i["passed"],
            "step_ii": res_ii["accepted"],
            "combined": comb_pass
        })

    # Summary across all 133 silver cards
    silver_comb_passed = 0
    silver_comb_failed = 0
    silver_comb_records = []
    for sc in silver_cards:
        doc_id = sc["doc_id"]
        p_i = step_i_by_doc[doc_id]["passed"]
        p_ii = step_ii_by_doc[doc_id]["accepted"]
        c_pass = p_i and p_ii
        if c_pass:
            silver_comb_passed += 1
        else:
            silver_comb_failed += 1
        silver_comb_records.append({
            "doc_id": doc_id,
            "step_i_passed": p_i,
            "step_ii_accepted": p_ii,
            "combined_passed": c_pass
        })

    # Output artifact
    result_artifact = {
        "seed_11_cross_tab_step_i": crosstab_step_i,
        "seed_11_combined_results": crosstab_combined,
        "silver_133_summary": {
            "total_cards": len(silver_cards),
            "step_i_passed": sum(1 for sc in silver_cards if step_i_by_doc[sc["doc_id"]]["passed"]),
            "step_ii_accepted": sum(1 for sc in silver_cards if step_ii_by_doc[sc["doc_id"]]["accepted"]),
            "combined_passed": silver_comb_passed,
            "combined_pass_rate": round(silver_comb_passed / len(silver_cards), 4),
            "combined_wilson_ci_95": wilson_score_interval(silver_comb_passed, len(silver_cards)),
            "combined_failed": silver_comb_failed,
        },
        "silver_133_details": silver_comb_records,
        "step_i_details_by_doc": step_i_by_doc,
        "step_ii_details_by_doc": step_ii_by_doc
    }

    out_file = out_dir / "critic_combined_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result_artifact, f, indent=2)

    print(f"\nSaved combined critic results to {out_file}")

    print("\n--- STEP (i) RELEVANCE x VERDICT (Seed 11, N=24) ---")
    for v in ["GOOD", "MINOR", "MAJOR"]:
        p = crosstab_step_i[v]["passed"]
        f = crosstab_step_i[v]["failed"]
        print(f"  {v:<6}: Passed={p}, Failed={f} (Fail Rate: {f/(p+f)*100:.1f}%) | Failed doc IDs: {crosstab_step_i[v]['doc_ids_failed']}")

    print("\n--- COMBINED (Step i AND Step ii) x VERDICT (Seed 11, N=24) ---")
    for v in ["GOOD", "MINOR", "MAJOR"]:
        p = crosstab_combined[v]["passed"]
        f = crosstab_combined[v]["failed"]
        print(f"  {v:<6}: Combined Passed={p}, Combined Rejected={f} (Accept Rate: {p/(p+f)*100:.1f}%)")

    print(f"\n--- COMBINED ON ALL 133 SILVER CARDS ---")
    print(f"  Total Silver: {len(silver_cards)}")
    print(f"  Step (i) Passed: {result_artifact['silver_133_summary']['step_i_passed']}/133")
    print(f"  Step (ii) Accepted: {result_artifact['silver_133_summary']['step_ii_accepted']}/133")
    print(f"  Both Passed: {silver_comb_passed}/133 ({silver_comb_passed/133*100:.1f}%) [95% CI: {result_artifact['silver_133_summary']['combined_wilson_ci_95']}]")


if __name__ == "__main__":
    main()
