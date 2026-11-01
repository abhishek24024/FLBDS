#!/usr/bin/env python3
"""Rebuild 20-card blind review packet from stage_6_output_clean.jsonl."""

import json
import random
from pathlib import Path

def main():
    in_path = Path("/home/abhishek24024/flbds_data/pilot/stage_6_output_clean.jsonl")
    with open(in_path) as f:
        records = [json.loads(line) for line in f]

    bio = [r for r in records if r.get("domain") == "bio" or "PMC" in r.get("doc_id", "")]
    eng = [r for r in records if r not in bio]

    bio.sort(key=lambda x: x["doc_id"])
    eng.sort(key=lambda x: x["doc_id"])

    random.seed(11)
    sampled_bio = random.sample(bio, 10)
    sampled_eng = random.sample(eng, 10)

    packet_items = sampled_bio + sampled_eng
    random.seed(11)
    random.shuffle(packet_items)

    packet_path = Path("/home/abhishek24024/flbds_data/review/human_packet.md")
    with open(packet_path, "w") as f_pkt:
        f_pkt.write("# FLBDS Blind Quality Review Packet (Audit Round 2)\n\n")
        f_pkt.write("This review packet contains 20 blinded candidate Mechanism Cards (10 biological literature, 10 engineering patents) sampled from Stage 5/6 output with strictly span-grounded quantities.\n")
        f_pkt.write("For each item: read the source text excerpt, evaluate the extracted card fields, and complete the blank checklist.\n\n---\n\n")

        for idx, item in enumerate(packet_items):
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
            subj = card.get("subject", {}).get("name") if isinstance(card.get("subject"), dict) else card.get("subject")
            f_pkt.write(f"- **Subject**: {subj}\n")
            action_dict = card.get("action", {})
            act_verb = action_dict.get("verb") if isinstance(action_dict, dict) else action_dict
            act_obj = action_dict.get("object") if isinstance(action_dict, dict) else ""
            f_pkt.write(f"- **Action Verb**: {act_verb}\n")
            f_pkt.write(f"- **Action Object**: {act_obj}\n")
            phenom = card.get("phenomenon", {}).get("description") if isinstance(card.get("phenomenon"), dict) else card.get("phenomenon")
            f_pkt.write(f"- **Phenomenon**: {phenom}\n")
            eff = card.get("effect", {}).get("canonical_name") if isinstance(card.get("effect"), dict) else card.get("effect")
            f_pkt.write(f"- **Effect**: {eff}\n")
            f_pkt.write(f"- **Consumable Inputs**: {card.get('inputs', [])}\n")
            
            f_pkt.write("- **Extracted Quantities (Strictly Span-Grounded)**:\n")
            quantities = card.get("quantities") or []
            if quantities:
                for q in quantities:
                    f_pkt.write(f"  * {q.get('name')}: {q.get('value')} {q.get('unit')} (regime: {q.get('regime_of_validity')})\n")
            else:
                f_pkt.write("  * None extracted (or purged as not inside span)\n")

            f_pkt.write("- **Cited Evidence Spans**:\n")
            evidence = card.get("evidence") or []
            if evidence:
                for ev in evidence:
                    span_text = ev.get('text_span', '')
                    f_pkt.write(f"  * \"{span_text}\"\n")
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

    print(f"Rebuilt human packet -> {packet_path} with {len(packet_items)} cards.")

if __name__ == "__main__":
    main()
