#!/usr/bin/env python3
"""Extract quoted passages, specific errors, and verbatim cards for all 17 non-GOOD cards."""

import json
from pathlib import Path

def main():
    path = Path("/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json")
    with open(path) as f:
        data = json.load(f)

    audits = data["all_card_audits"]

    minor_cards = [c for c in audits if c["verdict"] == "MINOR"]
    major_cards = [c for c in audits if c["verdict"] == "MAJOR"]
    good_cards = [c for c in audits if c["verdict"] == "GOOD"]

    print(f"Total Audited: {len(audits)}")
    print(f"GOOD: {len(good_cards)}")
    print(f"MINOR: {len(minor_cards)}")
    print(f"MAJOR: {len(major_cards)}")

    print("\n" + "="*80)
    print("ALL 10 MINOR CARDS: SPECIFIC ERRORS AND QUOTED PASSAGES")
    print("="*80)
    for i, c in enumerate(minor_cards):
        print(f"\n--- [MINOR {i+1}/10] Doc ID: {c['doc_id']} ({c['domain'].upper()}) ---")
        print(f"Title: {c['title']}")
        print(f"Specific Error(s): {', '.join(c['issues'])}")
        print(f"Extracted Fields:")
        print(f"  Subject: {c['card_fields']['subject']}")
        print(f"  Action: {c['card_fields']['action']}")
        print(f"  Effect: {c['card_fields']['effect']}")
        print(f"Quoted Source Passage:")
        quote = c.get("quoted_source_passage_for_flaw") or (c['card_fields']['evidence_spans'][0] if c['card_fields']['evidence_spans'] else "No quote available")
        print(f"  \"{quote.strip()}\"")

    print("\n" + "="*80)
    print("ALL 7 MAJOR CARDS: SPECIFIC ERRORS, VERBATIM CARDS, AND EVIDENCE SPANS")
    print("="*80)
    for i, c in enumerate(major_cards):
        print(f"\n--- [MAJOR {i+1}/7] Doc ID: {c['doc_id']} ({c['domain'].upper()}) ---")
        print(f"Title: {c['title']}")
        print(f"Specific Fatal Flaw(s): {', '.join(c['issues'])}")
        print(f"Verbatim Card Object:")
        print(json.dumps(c["card_fields"], indent=2))
        print(f"Quoted Source Passage:")
        quote = c.get("quoted_source_passage_for_flaw") or (c['card_fields']['evidence_spans'][0] if c['card_fields']['evidence_spans'] else "No quote available")
        print(f"  \"{quote.strip()}\"")

if __name__ == "__main__":
    main()
