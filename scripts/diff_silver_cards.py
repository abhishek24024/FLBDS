#!/usr/bin/env python3
"""Diff silver cards between pilot and audit6 sets, correctly navigating the nested 'card' structure."""

import json
import sys
from pathlib import Path

def load_cards(path):
    cards = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            did = rec.get("doc_id") or rec.get("card_id")
            # Bug fix: Access nested 'card' dict, not top-level root
            card = rec.get("card", rec)
            cards[did] = card
    return cards

def main():
    pilot_path = Path("/home/abhishek24024/flbds_data/pilot/silver_cards.jsonl")
    audit6_path = Path("/home/abhishek24024/flbds_data/audit6/silver_cards.jsonl")

    pilot = load_cards(pilot_path)
    audit6 = load_cards(audit6_path)

    subject_diffs = []
    for did in sorted(pilot.keys()):
        if did in audit6:
            p_subj = pilot[did].get("subject")
            a_subj = audit6[did].get("subject")
            if p_subj != a_subj:
                subject_diffs.append((did, p_subj, a_subj))

    print(f"Total cards with subject differences: {len(subject_diffs)} / {len(pilot)}")
    print("\nSample 3 cards whose subject changed from null to a name:")
    for did, p_s, a_s in subject_diffs[:3]:
        print("----------------------------------------------------------------------")
        print(f"Document ID: {did}")
        print(f"  Pilot Subject:  {p_s}")
        print(f"  Audit6 Subject: {a_s}")

if __name__ == "__main__":
    main()
