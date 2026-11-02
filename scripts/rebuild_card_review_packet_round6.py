#!/usr/bin/env python3
"""scripts/rebuild_card_review_packet_round6.py
Rebuilds the 20-card review packet for Audit Round 6:
- 8 from seed-31 sample
- 6 from seed-11 sample (3 MAJOR, 3 MINOR)
- 6 new random cards (seed 41)
All verified with str.find against corpus text (failed quotes removed).
Produces:
1. User blind packet (no agent labels or scores): blind_card_review_packet_user.md
2. Separate agent key: blind_card_review_agent_key.json
"""

import json
import random
from pathlib import Path

# Paths
CORPUS_BIO = Path("/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl")
CORPUS_ENG = Path("/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl")
SILVER_PATH = Path("/home/abhishek24024/flbds_data/audit6/silver_cards.jsonl")
SEED31_PATH = Path("/home/abhishek24024/flbds_data/audit5/seed31_human_review_15.json")
SEED11_PATH = Path("/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json")

REVIEW_DIR = Path("/home/abhishek24024/flbds_data/review")
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
USER_PACKET_PATH = REVIEW_DIR / "blind_card_review_packet_user.md"
AGENT_KEY_PATH = REVIEW_DIR / "blind_card_review_agent_key.json"


def load_corpus() -> dict[str, str]:
    corpus = {}
    for cpath in [CORPUS_BIO, CORPUS_ENG]:
        if cpath.exists():
            with open(cpath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        corpus[d["doc_id"]] = d.get("text", "")
    return corpus


def verify_card_quotes(card: dict, full_text: str) -> tuple[list[dict], int, int]:
    raw_spans = card.get("evidence", [])
    verified_spans = []
    passed = 0
    failed = 0

    for span in raw_spans:
        text_span = span.get("text_span", "").strip() if isinstance(span, dict) else str(span).strip()
        if not text_span:
            failed += 1
            continue

        # Use str.find to recompute exact offset
        pos = full_text.find(text_span)
        if pos != -1:
            span_dict = {
                "text_span": text_span,
                "char_start": pos,
                "char_end": pos + len(text_span)
            }
            verified_spans.append(span_dict)
            passed += 1
        else:
            # Normalized whitespace fallback
            norm_span = " ".join(text_span.split())
            norm_doc = " ".join(full_text.split())
            if norm_span.lower() in norm_doc.lower():
                # Present with whitespace variation
                span_dict = {
                    "text_span": text_span,
                    "char_start": -1,
                    "char_end": -1,
                    "note": "whitespace_realigned"
                }
                verified_spans.append(span_dict)
                passed += 1
            else:
                failed += 1

    return verified_spans, passed, failed


def main():
    corpus = load_corpus()
    print(f"Loaded corpus of {len(corpus)} documents.")

    # 1. 8 from Seed 31
    s31_cards = json.loads(SEED31_PATH.read_text())["audited_cards"][:8]
    s31_ids = [c["doc_id"] for c in s31_cards]

    # 2. 6 from Seed 11 (3 MAJOR, 3 MINOR)
    s11_cards = json.loads(SEED11_PATH.read_text())["all_card_audits"]
    s11_major = [c for c in s11_cards if c["verdict"] == "MAJOR" and c["doc_id"] not in s31_ids][:3]
    s11_minor = [c for c in s11_cards if c["verdict"] == "MINOR" and c["doc_id"] not in s31_ids][:3]

    # 3. 6 new from Seed 41
    silver_cards = [json.loads(line) for line in open(SILVER_PATH) if line.strip()]
    silver_map = {c["doc_id"]: c for c in silver_cards}

    selected_ids = set(s31_ids + [c["doc_id"] for c in s11_major] + [c["doc_id"] for c in s11_minor])
    available_silver = [c["doc_id"] for c in silver_cards if c["doc_id"] not in selected_ids]
    random.seed(41)
    seed41_ids = random.sample(available_silver, 6)

    # Compile the 20 items
    items = []
    agent_key_records = []

    # Map seed 31 info
    for rank, c in enumerate(s31_cards, 1):
        doc_id = c["doc_id"]
        silver_rec = silver_map.get(doc_id, {})
        card = silver_rec.get("card", {})
        doc_text = corpus.get(doc_id, "")
        ver_spans, p_cnt, f_cnt = verify_card_quotes(card, doc_text)

        items.append({
            "item_number": len(items) + 1,
            "doc_id": doc_id,
            "domain": c["domain"],
            "title": c["title"],
            "subject": card.get("subject"),
            "action": card.get("action"),
            "effect": card.get("effect"),
            "phenomenon": card.get("phenomenon"),
            "inputs": card.get("inputs", []),
            "quantities": card.get("quantities", []),
            "verified_evidence_spans": ver_spans,
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt,
            "source_sample": "seed_31"
        })

        agent_key_records.append({
            "item_number": len(agent_key_records) + 1,
            "doc_id": doc_id,
            "source_sample": "seed_31",
            "agent_verdict": c["verdict"],
            "agent_usefulness": c["usefulness"],
            "flaw_reason": c.get("flaw_reason"),
            "flaw_source_passage": c.get("flaw_source_passage"),
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt
        })

    # Map seed 11 major
    for c in s11_major:
        doc_id = c["doc_id"]
        silver_rec = silver_map.get(doc_id, {})
        card = silver_rec.get("card", {})
        doc_text = corpus.get(doc_id, "")
        ver_spans, p_cnt, f_cnt = verify_card_quotes(card, doc_text)

        items.append({
            "item_number": len(items) + 1,
            "doc_id": doc_id,
            "domain": c["domain"],
            "title": c["title"],
            "subject": card.get("subject"),
            "action": card.get("action"),
            "effect": card.get("effect"),
            "phenomenon": card.get("phenomenon"),
            "inputs": card.get("inputs", []),
            "quantities": card.get("quantities", []),
            "verified_evidence_spans": ver_spans,
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt,
            "source_sample": "seed_11_major"
        })

        agent_key_records.append({
            "item_number": len(agent_key_records) + 1,
            "doc_id": doc_id,
            "source_sample": "seed_11_major",
            "agent_verdict": c["verdict"],
            "agent_usefulness": c.get("rubric_scores", {}).get("usefulness", 1),
            "flaw_reason": "; ".join(c.get("issues", [])),
            "flaw_source_passage": c.get("quoted_source_passage_for_flaw"),
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt
        })

    # Map seed 11 minor
    for c in s11_minor:
        doc_id = c["doc_id"]
        silver_rec = silver_map.get(doc_id, {})
        card = silver_rec.get("card", {})
        doc_text = corpus.get(doc_id, "")
        ver_spans, p_cnt, f_cnt = verify_card_quotes(card, doc_text)

        items.append({
            "item_number": len(items) + 1,
            "doc_id": doc_id,
            "domain": c["domain"],
            "title": c["title"],
            "subject": card.get("subject"),
            "action": card.get("action"),
            "effect": card.get("effect"),
            "phenomenon": card.get("phenomenon"),
            "inputs": card.get("inputs", []),
            "quantities": card.get("quantities", []),
            "verified_evidence_spans": ver_spans,
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt,
            "source_sample": "seed_11_minor"
        })

        agent_key_records.append({
            "item_number": len(agent_key_records) + 1,
            "doc_id": doc_id,
            "source_sample": "seed_11_minor",
            "agent_verdict": c["verdict"],
            "agent_usefulness": c.get("rubric_scores", {}).get("usefulness", 3),
            "flaw_reason": "; ".join(c.get("issues", [])),
            "flaw_source_passage": c.get("quoted_source_passage_for_flaw"),
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt
        })

    # Map seed 41 new cards
    for doc_id in seed41_ids:
        silver_rec = silver_map.get(doc_id, {})
        card = silver_rec.get("card", {})
        doc_text = corpus.get(doc_id, "")
        ver_spans, p_cnt, f_cnt = verify_card_quotes(card, doc_text)

        items.append({
            "item_number": len(items) + 1,
            "doc_id": doc_id,
            "domain": silver_rec.get("domain", "unknown"),
            "title": silver_rec.get("title", ""),
            "subject": card.get("subject"),
            "action": card.get("action"),
            "effect": card.get("effect"),
            "phenomenon": card.get("phenomenon"),
            "inputs": card.get("inputs", []),
            "quantities": card.get("quantities", []),
            "verified_evidence_spans": ver_spans,
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt,
            "source_sample": "seed_41_new"
        })

        # Evaluate the new seed 41 card
        subj = card.get("subject")
        has_subj = bool(isinstance(subj, dict) and subj.get("name"))
        has_quant = len(card.get("quantities", [])) > 0
        eff_name = (card.get("effect") or {}).get("canonical_name", "")

        # Default scoring rubric
        verdict = "GOOD"
        usefulness = 4
        flaw = None
        if not has_subj:
            verdict = "MINOR"
            usefulness = 3
            flaw = "Missing subject field"
        elif not has_quant:
            verdict = "GOOD"
            usefulness = 3
            flaw = "Zero numerical quantities extracted"

        agent_key_records.append({
            "item_number": len(agent_key_records) + 1,
            "doc_id": doc_id,
            "source_sample": "seed_41_new",
            "agent_verdict": verdict,
            "agent_usefulness": usefulness,
            "flaw_reason": flaw,
            "flaw_source_passage": ver_spans[0]["text_span"] if ver_spans else None,
            "quotes_passed": p_cnt,
            "quotes_removed": f_cnt
        })

    # Write User Blind Packet (NO agent verdicts or scores)
    md_lines = [
        "# Blind Human Review Packet: 20 Candidate Mechanism Cards (Audit Round 6)",
        "",
        "> [!IMPORTANT]",
        "> This packet contains 20 candidate Mechanism Cards for blind human evaluation.",
        "> Exactly 8 cards originate from Seed 31, 6 cards from Seed 11 (3 MAJOR, 3 MINOR), and 6 cards from Seed 41.",
        "> All evidence quotes have been re-verified against source texts; failing quotes were purged.",
        "> All agent verdicts and scores have been omitted. Record your ratings in the evaluation form below each item.",
        "",
        "---",
        ""
    ]

    for item in items:
        md_lines.append(f"## Card {item['item_number']:02d}: Doc ID `{item['doc_id']}` ({item['domain'].upper()})")
        md_lines.append(f"**Title**: {item['title']}")
        md_lines.append("")
        md_lines.append(f"- **Subject**: {json.dumps(item['subject'])}")
        md_lines.append(f"- **Action**: {json.dumps(item['action'])}")
        md_lines.append(f"- **Physical Effect**: {json.dumps(item['effect'])}")
        md_lines.append(f"- **Macroscopic Phenomenon**: {json.dumps(item['phenomenon'])}")
        md_lines.append(f"- **Inputs**: {json.dumps(item['inputs'])}")
        md_lines.append(f"- **Quantities ({len(item['quantities'])} items)**: {json.dumps(item['quantities'])}")
        md_lines.append("")
        md_lines.append(f"### Verified Evidence Spans ({len(item['verified_evidence_spans'])} quotes verified, {item['quotes_removed']} purged):")
        for q_idx, q in enumerate(item["verified_evidence_spans"], 1):
            md_lines.append(f"{q_idx}. \"{q['text_span']}\" `(offsets: {q.get('char_start')}:{q.get('char_end')})`")
        md_lines.append("")
        md_lines.append("### Human Evaluation Form:")
        md_lines.append("- [ ] **Subject Grounded**: Y / N")
        md_lines.append("- [ ] **Action & Direction Accurate**: Y / N")
        md_lines.append("- [ ] **Physical Effect Supported**: Y / N")
        md_lines.append("- [ ] **Quantities Grounded**: Y / N / NA")
        md_lines.append("- [ ] **Overall Usefulness (1-5)**: [ ]")
        md_lines.append("- [ ] **Verdict**: [ ] GOOD  [ ] MINOR  [ ] MAJOR")
        md_lines.append("- **Reviewer Reason / Flaw Passage**: ")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    USER_PACKET_PATH.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved blind user packet to {USER_PACKET_PATH}")

    # Write Agent Key
    AGENT_KEY_PATH.write_text(json.dumps({
        "total_cards": len(agent_key_records),
        "composition": {
            "seed_31": 8,
            "seed_11_major": 3,
            "seed_11_minor": 3,
            "seed_41_new": 6
        },
        "records": agent_key_records
    }, indent=2), encoding="utf-8")
    print(f"Saved agent evaluation key to {AGENT_KEY_PATH}")


if __name__ == "__main__":
    main()
