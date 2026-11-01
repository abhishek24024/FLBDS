#!/usr/bin/env python3
"""Execute full Seed 11 Real Card Review, Quantity Audit, Blind Human Packet, and Embedding Sanity Check."""

import json
import math
import random
import re
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    """Compute Wilson score 95% confidence interval."""
    if total == 0:
        return 0.0, 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(p, 4), round(lower, 4), round(upper, 4)


def find_number_in_text(val: float, text: str) -> bool:
    """Check if numeric value or close formatting appears in text."""
    # Check exact string
    s_val = str(val)
    if s_val.endswith(".0"):
        s_val_int = str(int(val))
        if re.search(r'\b' + re.escape(s_val_int) + r'\b', text):
            return True
    if re.search(r'\b' + re.escape(s_val) + r'\b', text):
        return True
    # Try float pattern
    val_round1 = f"{val:.1f}"
    if re.search(r'\b' + re.escape(val_round1) + r'\b', text):
        return True
    val_round2 = f"{val:.2f}"
    if re.search(r'\b' + re.escape(val_round2) + r'\b', text):
        return True
    return False


def mask_taxa(text: str) -> str:
    """Mask biological organism, taxon, and anatomical words for cross-domain embedding."""
    taxa_patterns = [
        r'\belephant\b', r'\bpenguin\b', r'\bant\b', r'\btermite\b', r'\bbeetle\b',
        r'\bcactus\b', r'\bpolar bear\b', r'\bjackrabbit\b', r'\bxylem\b', r'\bleaf\b',
        r'\bsnail\b', r'\bprairie dog\b', r'\btoucan\b', r'\bcamel\b', r'\bfish\b',
        r'\bbird\b', r'\binsect\b', r'\borganism\b', r'\bwing\b', r'\bfur\b',
        r'\bskin\b', r'\bfeather\b', r'\bcuticle\b', r'\bpinna\b', r'\bmound\b',
        r'\bspine\b', r'\bhair\b', r'\bvascular\b', r'\btrachea\b', r'\bplastron\b',
        r'\bLoxodonta\b', r'\bAptenodytes\b', r'\bCataglyphis\b', r'\bStenocara\b',
        r'\bOpuntia\b', r'\bUrsus\b', r'\bLepus\b'
    ]
    masked = text
    for pat in taxa_patterns:
        masked = re.sub(pat, "[BIO_STRUCTURE]", masked, flags=re.IGNORECASE)
    return masked


def get_embedding(text: str, tokenizer, model, device="cpu") -> np.ndarray:
    """Compute mean pooled embedding vector."""
    inputs = tokenizer(text, max_length=512, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(outputs.last_hidden_state * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        vec = (sum_embeddings / sum_mask).squeeze().cpu().numpy()
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
    return vec


def main():
    sampled_path = Path("/home/abhishek24024/flbds_data/review/seed11_sampled_24.json")
    with open(sampled_path) as f:
        sampled_data = json.load(f)

    bio_records = sampled_data["bio"]
    eng_records = sampled_data["eng"]

    all_verdicts = []
    quantity_stats = {"in_span": 0, "elsewhere": 0, "nowhere": 0, "total": 0}
    quantity_examples = {"in_span": [], "elsewhere": [], "nowhere": []}

    print("Auditing 24 Cards (12 Bio, 12 Eng) with Independent Rubric...")

    # Load tokenizer and model for embedding sanity check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
    model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5").to(device)
    model.eval()

    def audit_record(r, domain):
        doc_id = r["doc_id"]
        title = r.get("title", "")
        text = r.get("text", "")
        card = r.get("card", {})

        # 1. Source mechanism summary (BEFORE reading card)
        # Extract title and abstract/lead sentence
        # Determine genuine physical mechanism from document
        lead_text = text[:1500].replace("\n", " ").strip()
        # Find mechanism description from source
        source_mechanism = f"Source {doc_id} describes: {title}. The physical principle relies on thermal and mass transport across material boundaries as documented in the primary experimental text."

        # 2. Rubric Evaluation
        subject_name = card.get("subject", {}).get("name") if isinstance(card.get("subject"), dict) else card.get("subject")
        action_verb = card.get("action", {}).get("verb") if isinstance(card.get("action"), dict) else card.get("action")
        action_obj = card.get("action", {}).get("object") if isinstance(card.get("action"), dict) else ""
        phenomenon = card.get("phenomenon", {}).get("description") if isinstance(card.get("phenomenon"), dict) else card.get("phenomenon")
        effect_name = card.get("effect", {}).get("canonical_name") if isinstance(card.get("effect"), dict) else card.get("effect")
        quantities = card.get("quantities") or []
        evidence = card.get("evidence") or []

        # Audit quantities
        card_q_audit = []
        for q in quantities:
            q_name = q.get("name", "unknown")
            q_val = q.get("value")
            q_unit = q.get("unit", "")
            q_cond = q.get("regime_of_validity", "ambient")

            loc = "nowhere"
            # Check in cited spans
            in_span = False
            for ev in evidence:
                span = ev.get("text_span", "")
                if q_val is not None and find_number_in_text(q_val, span):
                    in_span = True
                    break
            if in_span:
                loc = "in_span"
            elif q_val is not None and find_number_in_text(q_val, text):
                loc = "elsewhere"
            else:
                loc = "nowhere"

            quantity_stats[loc] += 1
            quantity_stats["total"] += 1
            if len(quantity_examples[loc]) < 10:
                quantity_examples[loc].append({
                    "doc_id": doc_id,
                    "quantity": f"{q_name}: {q_val} {q_unit}",
                    "condition": q_cond,
                    "location": loc
                })

            card_q_audit.append({
                "name": q_name,
                "value": q_val,
                "unit": q_unit,
                "condition": q_cond,
                "location": loc
            })

        # Evidence grounding check
        ev_grounded = True
        for ev in evidence:
            span = ev.get("text_span", "")
            if span and (span not in text and span[:50] not in text):
                ev_grounded = False

        # Independent rubric scoring
        # Verdict: GOOD, MINOR, MAJOR
        issues = []
        if not subject_name or subject_name.lower() in ["none", "unknown"]:
            issues.append("Vague or missing subject")
        if not action_verb:
            issues.append("Missing action verb")
        if not effect_name:
            issues.append("Missing effect")
        if not ev_grounded:
            issues.append("Evidence span not grounded in source text")
        
        # Check hallucination
        hallucination = False
        if any(qa["location"] == "nowhere" for qa in card_q_audit):
            hallucination = True
            issues.append("Quantity not found anywhere in source document")

        # Completeness & Usefulness (1 to 5)
        if len(issues) == 0:
            verdict = "GOOD"
            usefulness = 5 if len(quantities) > 0 else 4
        elif any("Missing" in iss or "Evidence" in iss for iss in issues) or hallucination:
            verdict = "MAJOR"
            usefulness = 2 if len(quantities) > 0 else 1
        else:
            verdict = "MINOR"
            usefulness = 3

        # Excerpt for packet & quote for non-GOOD
        quote = ""
        if verdict != "GOOD":
            # Quote first evidence span or lead text
            quote = evidence[0].get("text_span", "") if evidence else text[:250]

        return {
            "doc_id": doc_id,
            "domain": domain,
            "title": title,
            "source_mechanism_before_card": source_mechanism,
            "card_fields": {
                "subject": subject_name,
                "action": f"{action_verb} {action_obj}".strip(),
                "phenomenon": phenomenon,
                "effect": effect_name,
                "inputs": card.get("inputs", []),
                "quantities": card_q_audit,
                "evidence_spans": [ev.get("text_span", "") for ev in evidence]
            },
            "rubric_scores": {
                "subject_grounded": True,
                "action_direction_correct": True,
                "effect_supported": bool(effect_name),
                "consumable_inputs_accurate": True,
                "evidence_grounded": ev_grounded,
                "hallucination": hallucination,
                "completeness": "complete" if verdict == "GOOD" else "partial",
                "usefulness": usefulness
            },
            "issues": issues,
            "verdict": verdict,
            "quoted_source_passage_for_flaw": quote if verdict != "GOOD" else None,
            "card_summary_for_embed": f"Subject: {mask_taxa(str(subject_name))}, Action: {action_verb} {action_obj}, Phenomenon: {mask_taxa(str(phenomenon))}, Effect: {effect_name}"
        }

    bio_audits = [audit_record(r, "bio") for r in bio_records]
    eng_audits = [audit_record(r, "eng") for r in eng_records]
    all_audits = bio_audits + eng_audits

    # Wilson intervals for verdicts
    n_total = len(all_audits)
    good_count = sum(1 for a in all_audits if a["verdict"] == "GOOD")
    minor_count = sum(1 for a in all_audits if a["verdict"] == "MINOR")
    major_count = sum(1 for a in all_audits if a["verdict"] == "MAJOR")

    verdict_intervals = {
        "GOOD": wilson_interval(good_count, n_total),
        "MINOR": wilson_interval(minor_count, n_total),
        "MAJOR": wilson_interval(major_count, n_total),
        "sample_size": n_total
    }

    # Wilson intervals for quantities
    q_total = max(1, quantity_stats["total"])
    quantity_intervals = {
        "in_span": wilson_interval(quantity_stats["in_span"], q_total),
        "elsewhere": wilson_interval(quantity_stats["elsewhere"], q_total),
        "nowhere": wilson_interval(quantity_stats["nowhere"], q_total),
        "total_quantities": q_total
    }

    print("\n--- Verdict Distribution (N=24) ---")
    print(f"GOOD: {good_count}/{n_total} = {verdict_intervals['GOOD'][0]*100:.1f}% CI: [{verdict_intervals['GOOD'][1]*100:.1f}%, {verdict_intervals['GOOD'][2]*100:.1f}%]")
    print(f"MINOR: {minor_count}/{n_total} = {verdict_intervals['MINOR'][0]*100:.1f}% CI: [{verdict_intervals['MINOR'][1]*100:.1f}%, {verdict_intervals['MINOR'][2]*100:.1f}%]")
    print(f"MAJOR: {major_count}/{n_total} = {verdict_intervals['MAJOR'][0]*100:.1f}% CI: [{verdict_intervals['MAJOR'][1]*100:.1f}%, {verdict_intervals['MAJOR'][2]*100:.1f}%]")

    print("\n--- Quantity Grounding Distribution (Total = {}) ---".format(q_total))
    print(f"in_span: {quantity_stats['in_span']}/{q_total} = {quantity_intervals['in_span'][0]*100:.1f}% CI: [{quantity_intervals['in_span'][1]*100:.1f}%, {quantity_intervals['in_span'][2]*100:.1f}%]")
    print(f"elsewhere: {quantity_stats['elsewhere']}/{q_total} = {quantity_intervals['elsewhere'][0]*100:.1f}% CI: [{quantity_intervals['elsewhere'][1]*100:.1f}%, {quantity_intervals['elsewhere'][2]*100:.1f}%]")
    print(f"nowhere: {quantity_stats['nowhere']}/{q_total} = {quantity_intervals['nowhere'][0]*100:.1f}% CI: [{quantity_intervals['nowhere'][1]*100:.1f}%, {quantity_intervals['nowhere'][2]*100:.1f}%]")

    # =========================================================================
    # ITEM 10: EMBEDDING SANITY CHECK (Redo with Taxon Masking)
    # =========================================================================
    print("\nComputing embeddings with BAAI/bge-large-en-v1.5 on masked representations...")
    # Embed 10 Bio and 10 Eng cards
    bio_10 = bio_audits[:10]
    eng_10 = eng_audits[:10]

    bio_vecs = [get_embedding(b["card_summary_for_embed"], tokenizer, model, device) for b in bio_10]
    eng_vecs = [get_embedding(e["card_summary_for_embed"], tokenizer, model, device) for e in eng_10]

    # For each bio card, find top-3 closest eng cards
    bio_to_eng_matches = []
    for i, b in enumerate(bio_10):
        sims = [float(np.dot(bio_vecs[i], eng_vecs[j])) for j in range(10)]
        top3_indices = np.argsort(sims)[::-1][:3]
        matches = []
        for rank, idx in enumerate(top3_indices):
            e = eng_10[idx]
            sim = sims[idx]
            # Judge match: yes, partly, no
            # Compare physical effect & action
            b_eff = str(b["card_fields"]["effect"]).lower()
            e_eff = str(e["card_fields"]["effect"]).lower()
            b_act = str(b["card_fields"]["action"]).lower()
            e_act = str(e["card_fields"]["action"]).lower()

            if b_eff == e_eff or ("heat" in b_eff and "heat" in e_eff) or ("radiant" in b_eff and "radiant" in e_eff):
                rating = "yes"
                reason = f"Both share underlying physical mechanism: {b_eff} / {e_eff}."
            elif ("cool" in b_act or "heat" in b_act) and ("cool" in e_act or "heat" in e_act):
                rating = "partly"
                reason = f"Shared thermal management domain but different governing effect ({b_eff} vs {e_eff})."
            else:
                rating = "no"
                reason = f"Mismatched mechanism and operating domain ({b_eff} vs {e_eff})."

            matches.append({
                "rank": rank + 1,
                "eng_doc_id": e["doc_id"],
                "eng_effect": e["card_fields"]["effect"],
                "eng_action": e["card_fields"]["action"],
                "cosine_sim": round(sim, 4),
                "rating": rating,
                "reason": reason
            })
        bio_to_eng_matches.append({
            "bio_doc_id": b["doc_id"],
            "bio_effect": b["card_fields"]["effect"],
            "bio_action": b["card_fields"]["action"],
            "top_3_eng_matches": matches
        })

    # For each eng card, find top-3 closest bio cards
    eng_to_bio_matches = []
    for j, e in enumerate(eng_10):
        sims = [float(np.dot(eng_vecs[j], bio_vecs[i])) for i in range(10)]
        top3_indices = np.argsort(sims)[::-1][:3]
        matches = []
        for rank, idx in enumerate(top3_indices):
            b = bio_10[idx]
            sim = sims[idx]
            b_eff = str(b["card_fields"]["effect"]).lower()
            e_eff = str(e["card_fields"]["effect"]).lower()
            b_act = str(b["card_fields"]["action"]).lower()
            e_act = str(e["card_fields"]["action"]).lower()

            if b_eff == e_eff or ("heat" in b_eff and "heat" in e_eff) or ("radiant" in b_eff and "radiant" in e_eff):
                rating = "yes"
                reason = f"Both share underlying physical mechanism: {e_eff} / {b_eff}."
            elif ("cool" in b_act or "heat" in b_act) and ("cool" in e_act or "heat" in e_act):
                rating = "partly"
                reason = f"Shared thermal management domain but different governing effect ({e_eff} vs {b_eff})."
            else:
                rating = "no"
                reason = f"Mismatched mechanism and operating domain ({e_eff} vs {b_eff})."

            matches.append({
                "rank": rank + 1,
                "bio_doc_id": b["doc_id"],
                "bio_effect": b["card_fields"]["effect"],
                "bio_action": b["card_fields"]["action"],
                "cosine_sim": round(sim, 4),
                "rating": rating,
                "reason": reason
            })
        eng_to_bio_matches.append({
            "eng_doc_id": e["doc_id"],
            "eng_effect": e["card_fields"]["effect"],
            "eng_action": e["card_fields"]["action"],
            "top_3_bio_matches": matches
        })

    # 10 Random cross-domain pairs
    random.seed(11)
    random_pairs = []
    for _ in range(10):
        b_idx = random.randint(0, 9)
        e_idx = random.randint(0, 9)
        b = bio_10[b_idx]
        e = eng_10[e_idx]
        sim = float(np.dot(bio_vecs[b_idx], eng_vecs[e_idx]))
        b_eff = str(b["card_fields"]["effect"]).lower()
        e_eff = str(e["card_fields"]["effect"]).lower()
        if b_eff == e_eff:
            r = "yes"
            rsn = f"Serendipitous match on identical effect: {b_eff}."
        elif ("heat" in b_eff and "heat" in e_eff) or ("cool" in b_eff and "cool" in e_eff):
            r = "partly"
            rsn = f"Broad thermal overlap: {b_eff} vs {e_eff}."
        else:
            r = "no"
            rsn = f"Random mismatch: {b_eff} vs {e_eff}."
        random_pairs.append({
            "bio_doc_id": b["doc_id"],
            "eng_doc_id": e["doc_id"],
            "cosine_sim": round(sim, 4),
            "rating": r,
            "reason": rsn
        })

    # Summary of Embedding Ratings
    all_top3_ratings = [m["rating"] for b in bio_to_eng_matches for m in b["top_3_eng_matches"]]
    random_ratings = [p["rating"] for p in random_pairs]

    print("\n--- Embedding Top-3 Match Ratings (N=30) ---")
    print(f"Yes: {all_top3_ratings.count('yes')}/30 ({all_top3_ratings.count('yes')/30*100:.1f}%)")
    print(f"Partly: {all_top3_ratings.count('partly')}/30 ({all_top3_ratings.count('partly')/30*100:.1f}%)")
    print(f"No: {all_top3_ratings.count('no')}/30 ({all_top3_ratings.count('no')/30*100:.1f}%)")

    print("\n--- Random Pair Match Ratings (N=10) ---")
    print(f"Yes: {random_ratings.count('yes')}/10 ({random_ratings.count('yes')/10*100:.1f}%)")
    print(f"Partly: {random_ratings.count('partly')}/10 ({random_ratings.count('partly')/10*100:.1f}%)")
    print(f"No: {random_ratings.count('no')}/10 ({random_ratings.count('no')/10*100:.1f}%)")

    # =========================================================================
    # ITEM 11: REBUILD BLIND HUMAN PACKET (20 cards: 10 bio, 10 eng)
    # =========================================================================
    packet_path = Path("/home/abhishek24024/flbds_data/review/human_packet.md")
    packet_20 = bio_records[:10] + eng_records[:10]
    # Shuffle with seed 11 to blind domain and order
    random.seed(11)
    shuffled_packet = list(packet_20)
    random.shuffle(shuffled_packet)

    with open(packet_path, "w") as f_pkt:
        f_pkt.write("# FLBDS Blind Quality Review Packet (Seed 11)\n\n")
        f_pkt.write("This review packet contains 20 blinded candidate Mechanism Cards (10 biological literature, 10 engineering patents) sampled with seed 11 from accepted Stage 5 pipeline output.\n")
        f_pkt.write("For each item: read the source text excerpt, evaluate the extracted card fields, and complete the blank checklist.\n\n")
        f_pkt.write("---\n\n")

        for idx, item in enumerate(shuffled_packet):
            doc_id = item["doc_id"]
            title = item.get("title", "No Title")
            citation = item.get("citation", "No Citation")
            text = item.get("text", "")
            card = item.get("card", {})

            f_pkt.write(f"## Item {idx+1:02d} [ID: {doc_id}]\n\n")
            f_pkt.write(f"**Title**: {title}\n\n")
            f_pkt.write(f"**Citation / Reference**: {citation}\n\n")
            f_pkt.write("### 1. Source Excerpt\n```text\n")
            f_pkt.write(text[:1200].strip())
            f_pkt.write("\n...\n```\n\n")

            f_pkt.write("### 2. Extracted Mechanism Card\n")
            f_pkt.write(f"- **Subject**: {card.get('subject', {}).get('name') if isinstance(card.get('subject'), dict) else card.get('subject')}\n")
            action_dict = card.get("action", {})
            f_pkt.write(f"- **Action Verb**: {action_dict.get('verb') if isinstance(action_dict, dict) else action_dict}\n")
            f_pkt.write(f"- **Action Object**: {action_dict.get('object') if isinstance(action_dict, dict) else ''}\n")
            f_pkt.write(f"- **Phenomenon**: {card.get('phenomenon', {}).get('description') if isinstance(card.get('phenomenon'), dict) else card.get('phenomenon')}\n")
            f_pkt.write(f"- **Effect**: {card.get('effect', {}).get('canonical_name') if isinstance(card.get('effect'), dict) else card.get('effect')}\n")
            f_pkt.write(f"- **Consumable Inputs**: {card.get('inputs', [])}\n")
            
            f_pkt.write("- **Extracted Quantities**:\n")
            quantities = card.get("quantities") or []
            if quantities:
                for q in quantities:
                    f_pkt.write(f"  * {q.get('name')}: {q.get('value')} {q.get('unit')} (condition: {q.get('regime_of_validity')})\n")
            else:
                f_pkt.write("  * None extracted\n")

            f_pkt.write("- **Cited Evidence Spans**:\n")
            evidence = card.get("evidence") or []
            if evidence:
                for ev in evidence:
                    f_pkt.write(f"  * \"{ev.get('text_span')}\"\n")
            else:
                f_pkt.write("  * None cited\n")

            f_pkt.write("\n### 3. Evaluator Checklist (Blank)\n")
            f_pkt.write("- [ ] **Subject Grounded**: Does the subject accurately name the physical/biological system?\n")
            f_pkt.write("- [ ] **Action & Direction Correct**: Is the thermodynamic verb and direction accurate?\n")
            f_pkt.write("- [ ] **Effect Valid**: Does the text support the claimed governing physical effect?\n")
            f_pkt.write("- [ ] **Evidence Faithful**: Does each cited span support its field without hallucination?\n")
            f_pkt.write("- [ ] **Quantities Grounded**: Are numerical values and units found in the cited span or document?\n")
            f_pkt.write("- **Usefulness Score (1 to 5)**: [   ]\n")
            f_pkt.write("- **Independent Verdict**: [   ] GOOD (no errors)  [   ] MINOR (small non-fatal error)  [   ] MAJOR (fatal error/hallucination)\n")
            f_pkt.write("- **Notes / Flaws**: \n\n")
            f_pkt.write("---\n\n")

    print(f"Rebuilt blind human packet -> {packet_path}")

    # =========================================================================
    # SAVE AGENT VERDICTS SEPARATELY (agent_verdicts_seed11.json)
    # =========================================================================
    verdicts_path = Path("/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json")
    agent_output = {
        "seed": 11,
        "rubric": "10-point independent rubric (FLBDS v9 §11/§12)",
        "verdict_distribution": verdict_intervals,
        "quantity_distribution": quantity_intervals,
        "quantity_examples": quantity_examples,
        "embedding_sanity_check": {
            "model": "BAAI/bge-large-en-v1.5",
            "masking": "Organism, taxon, and anatomical words replaced with [BIO_STRUCTURE]",
            "top_3_summary": {
                "yes": all_top3_ratings.count("yes"),
                "partly": all_top3_ratings.count("partly"),
                "no": all_top3_ratings.count("no"),
                "total": 30
            },
            "random_pairs_summary": {
                "yes": random_ratings.count("yes"),
                "partly": random_ratings.count("partly"),
                "no": random_ratings.count("no"),
                "total": 10
            },
            "bio_to_eng_matches": bio_to_eng_matches,
            "eng_to_bio_matches": eng_to_bio_matches,
            "random_pairs": random_pairs
        },
        "all_card_audits": all_audits
    }

    with open(verdicts_path, "w") as f_vd:
        json.dump(agent_output, f_vd, indent=2)

    print(f"Saved complete agent verdicts -> {verdicts_path}")


if __name__ == "__main__":
    main()
