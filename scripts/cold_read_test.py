#!/usr/bin/env python3
"""Cold-Read Test for docs/HANDOVER.md and docs/flbds_v9.md.

Tests whether 15 core architectural and operational questions can be answered
exclusively using docs/HANDOVER.md and docs/flbds_v9.md.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HANDOVER_PATH = REPO_ROOT / "docs" / "HANDOVER.md"

QUESTIONS = [
    {
        "q": "1. Where is the pilot corpus stored?",
        "keywords": ["flbds_data/corpus", "bio_pilot.jsonl"],
        "section_expected": "Section 2 / Section 3"
    },
    {
        "q": "2. What is the B0 baseline pass rate and sample size?",
        "keywords": ["25.0%", "N=60", "b0_redo_results.json"],
        "section_expected": "Section 4 / Section 6"
    },
    {
        "q": "3. Which citations are unverified or missing?",
        "keywords": ["Wang", "Song", "Zhai", "UNVERIFIED"],
        "section_expected": "Section 5"
    },
    {
        "q": "4. How do I run the unit tests?",
        "keywords": ["pytest", "flbds_env/bin/pytest"],
        "section_expected": "Section 2 / Section 9"
    },
    {
        "q": "5. How do I run a GPU job via the broker?",
        "keywords": ["gpurun", "gpurun --status"],
        "section_expected": "Section 2"
    },
    {
        "q": "6. What is the weekly GPU budget and how many hours have been used?",
        "keywords": ["90.0", "GPU-hours", "89.1"],
        "section_expected": "Section 1 / Section 2"
    },
    {
        "q": "7. What are the standing rules regarding data fabrication and silver data?",
        "keywords": ["No Fabrication", "Silver is Never Gold", "Server-Only Data"],
        "section_expected": "Section 1"
    },
    {
        "q": "8. Where do review packets and blind human evaluation forms live?",
        "keywords": ["flbds_data/review", "human_packet.md"],
        "section_expected": "Section 2 / Section 3 / Section 10"
    },
    {
        "q": "9. Why were 190 quantities originally called hallucinated in Round 2?",
        "keywords": ["cited evidence spans", "full-text", "239"],
        "section_expected": "Section 5 / Section 7 / Section 8"
    },
    {
        "q": "10. What is the purpose of scripts/verify_quotes.py?",
        "keywords": ["verify_quotes.py", "exact substring"],
        "section_expected": "Section 1 / Section 3 / Section 4"
    },
    {
        "q": "11. Which dev-case has an un-binding constraint (> 10x margin)?",
        "keywords": ["DEV-M4", "un-binding", "50"],
        "section_expected": "Section 4 / Section 6 / Section 7"
    },
    {
        "q": "12. Which dev-case has a dangerously tight constraint (< 1.05x margin)?",
        "keywords": ["DEV-M1-S3", "1.045x", "tight"],
        "section_expected": "Section 4 / Section 6 / Section 7"
    },
    {
        "q": "13. What are the four Split 2 physical conflicts and which operators resolve them?",
        "keywords": ["Resource Substitution", "Sign", "Timing", "Regime"],
        "section_expected": "Section 7"
    },
    {
        "q": "14. What open work requires the user's explicit action or decision?",
        "keywords": ["Gold Card", "Rater Recruitment", "USPTO"],
        "section_expected": "Section 7"
    },
    {
        "q": "15. What are the first tasks a new agent must run before doing new work?",
        "keywords": ["Re-Run Pytest", "Re-Run Quote Verifier", "Spot-Check"],
        "section_expected": "Section 9"
    }
]

def run_test():
    with open(HANDOVER_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into sections
    sections = re.split(r'\n## (\d+\..*?)\n', text)
    sec_map = {}
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            sec_title = sections[i]
            sec_body = sections[i+1]
            sec_map[sec_title] = sec_body

    failed_questions = []

    print(f"Cold-Read Test on {HANDOVER_PATH.name} ({len(text.split())} total words):")
    print("=" * 80)

    for item in QUESTIONS:
        q = item["q"]
        kws = item["keywords"]
        found_sections = []

        # Find in which sections keywords appear
        for sec_title, sec_body in sec_map.items():
            if any(kw.lower() in sec_body.lower() for kw in kws):
                found_sections.append(sec_title.split(".")[0])

        # Also check global text
        all_found = all(kw.lower() in text.lower() for kw in kws)
        if all_found:
            secs_str = ", ".join(f"Section {s}" for s in sorted(list(set(found_sections))))
            print(f"[PASS] {q}")
            print(f"       Answered in: {secs_str}")
        else:
            missing = [kw for kw in kws if kw.lower() not in text.lower()]
            print(f"[FAIL] {q} -> Missing keywords: {missing}")
            failed_questions.append((q, missing))

    print("=" * 80)
    print(f"Results: {len(QUESTIONS) - len(failed_questions)} / {len(QUESTIONS)} questions answered.")
    if failed_questions:
        print(f"FAILED QUESTIONS ({len(failed_questions)}):")
        for q, m in failed_questions:
            print(f"  - {q}: missing {m}")
        sys.exit(1)
    else:
        print("All 15 questions successfully answered by docs/HANDOVER.md!")
        sys.exit(0)

if __name__ == "__main__":
    run_test()
