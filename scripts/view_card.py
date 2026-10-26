#!/usr/bin/env python3
"""Step 6: Side-by-side terminal viewer for documents and extracted Mechanism Cards."""

import argparse
import json
import shutil
import textwrap
from pathlib import Path


def render_box(title: str, lines: list[str], width: int) -> list[str]:
    header = f"┌─ {title} " + "─" * max(0, width - len(title) - 4) + "┐"
    footer = "└" + "─" * (width - 2) + "┘"
    boxed = [header]
    for line in lines:
        wrapped = textwrap.wrap(line, width - 4) if line else [""]
        for w in wrapped:
            boxed.append(f"│ {w:<{width - 4}} │")
    boxed.append(footer)
    return boxed


def main():
    parser = argparse.ArgumentParser(description="Side-by-side viewer for documents and Mechanism Cards.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/silver_cards.jsonl")
    parser.add_argument("--index", type=int, default=0, help="0-based index of card to view")
    parser.add_argument("--doc-id", help="Specific Doc ID to view")
    parser.add_argument("--width", type=int, default=60, help="Width of each column")
    args = parser.parse_args()

    cards = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    if not cards:
        print(f"No cards found in {args.input}")
        return

    selected = None
    if args.doc_id:
        for c in cards:
            if c.get("doc_id") == args.doc_id:
                selected = c
                break
        if not selected:
            print(f"Doc ID {args.doc_id} not found.")
            return
    else:
        idx = max(0, min(args.index, len(cards) - 1))
        selected = cards[idx]

    doc_id = selected.get("doc_id", "N/A")
    domain = selected.get("domain", "N/A")
    title = selected.get("title", "No Title")
    citation = selected.get("citation", "No Citation")
    lic = selected.get("license", "Unknown")
    doc_text = selected.get("text", "")
    card = selected.get("card", {})

    # Build Left Column: Document Text & Metadata
    left_lines = [
        f"DOC ID:   {doc_id} ({domain})",
        f"TITLE:    {title}",
        f"CITATION: {citation}",
        f"LICENSE:  {lic}",
        "",
        "DOCUMENT TEXT EXCERPT:",
        "-" * (args.width - 4),
    ]
    for p in doc_text[:2000].split("\n"):
        if p.strip():
            left_lines.append(p.strip())
    if len(doc_text) > 2000:
        left_lines.append("... [truncated for display] ...")

    # Build Right Column: Extracted Mechanism Card
    sub = card.get("subject", {})
    act = card.get("action", {})
    sc = card.get("state_change", {})
    ph = card.get("phenomenon", {})
    eff = card.get("effect", {})
    quants = card.get("quantities", [])
    evs = card.get("evidence", [])
    unsupp = card.get("unsupported_fields", [])

    right_lines = [
        f"CARD ID:     {card.get('card_id')}",
        f"CONFIDENCE:  {card.get('confidence')} | TIER: {card.get('tier')}",
        f"SUBJECT:     {sub.get('name')} ({sub.get('identifier', 'N/A')})",
        "",
        "SAPPhIRE CAUSAL CHAIN:",
        f"• Action:      {act.get('verb')} {act.get('object')}",
        f"• StateChange: {sc.get('state_variable')} ({sc.get('from_value')} -> {sc.get('to_value')})",
        f"• Phenomenon:  {ph.get('description')}",
        f"• Effect/Law:  {eff.get('canonical_name')}",
        f"  Equation:    {eff.get('governing_equation', 'N/A')}",
        "",
        f"QUANTITIES ({len(quants)} extracted):",
    ]
    for q in quants[:4]:
        right_lines.append(f"  - {q.get('name')}: {q.get('value')} {q.get('unit')} ({q.get('regime_of_validity', 'ambient')})")

    right_lines.append("")
    right_lines.append(f"EVIDENCE SPANS ({len(evs)} verified):")
    for ev in evs[:3]:
        span_str = ev.get("text_span", "")[:60] + "..." if len(ev.get("text_span", "")) > 60 else ev.get("text_span", "")
        right_lines.append(f"  - [{ev.get('char_start')}:{ev.get('char_end')}] \"{span_str}\"")

    if unsupp:
        right_lines.append("")
        right_lines.append(f"UNSUPPORTED FIELDS: {', '.join(unsupp)}")

    col_w = args.width
    left_box = render_box(f"SOURCE DOCUMENT ({doc_id})", left_lines, col_w)
    right_box = render_box(f"EXTRACTED SILVER CARD ({card.get('card_id')})", right_lines, col_w)

    # Pad boxes to equal height
    max_h = max(len(left_box), len(right_box))
    while len(left_box) < max_h:
        left_box.insert(-1, f"│ {'':<{col_w - 4}} │")
    while len(right_box) < max_h:
        right_box.insert(-1, f"│ {'':<{col_w - 4}} │")

    print("\n" + "=" * (col_w * 2 + 2))
    print(f" FLBDS MECHANISM VIEWER  [Card {args.index + 1} of {len(cards)}]")
    print("=" * (col_w * 2 + 2))
    for l, r in zip(left_box, right_box):
        print(f"{l}  {r}")
    print("=" * (col_w * 2 + 2) + "\n")


if __name__ == "__main__":
    main()
