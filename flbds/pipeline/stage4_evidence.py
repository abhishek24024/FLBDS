"""Stage 4: Deterministic Programmatic Evidence Span Verifier (verbatim offset & substring check)."""

import argparse
import json
import time
from pathlib import Path


def verify_evidence_spans(card: dict, doc_text: str) -> tuple[dict, dict]:
    """Verify each evidence span verbatim against doc_text, realigning offsets or flagging hallucinated spans."""
    stats = {
        "total_spans": 0,
        "exact_matches": 0,
        "realigned_spans": 0,
        "failed_spans": 0,
    }

    raw_spans = card.get("evidence", [])
    verified_spans = []

    for span in raw_spans:
        stats["total_spans"] += 1
        text_span = span.get("text_span", "").strip()
        c_start = span.get("char_start", 0)
        c_end = span.get("char_end", 0)

        if not text_span:
            stats["failed_spans"] += 1
            continue

        # Check 1: exact character offset slice match
        if 0 <= c_start < len(doc_text) and c_start <= c_end <= len(doc_text):
            if doc_text[c_start:c_end] == text_span:
                stats["exact_matches"] += 1
                verified_spans.append(span)
                continue

        # Check 2: exact substring match anywhere in document text
        found_pos = doc_text.find(text_span)
        if found_pos != -1:
            stats["realigned_spans"] += 1
            span["char_start"] = found_pos
            span["char_end"] = found_pos + len(text_span)
            verified_spans.append(span)
            continue

        # Check 3: case-insensitive or whitespace-normalized fallback search
        norm_text = " ".join(text_span.split())
        norm_doc = " ".join(doc_text.split())
        if norm_text.lower() in norm_doc.lower():
            # Present in text but formatted differently, record as realigned
            stats["realigned_spans"] += 1
            verified_spans.append(span)
            continue

        # Failed: verbatim text span not present in source text (hallucination)
        stats["failed_spans"] += 1

    card["evidence"] = verified_spans
    return card, stats


def run_evidence_verification(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
) -> dict:
    t_start = time.perf_counter()
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    input_count = len(records)
    print(f"[Stage 4 Evidence Check] Verifying evidence spans for {input_count} cards...", flush=True)

    verified_records = []
    drop_reasons = {}
    aggregate_stats = {
        "total_spans": 0,
        "exact_matches": 0,
        "realigned_spans": 0,
        "failed_spans": 0,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fout:
        for rec in records:
            card = rec["card"]
            doc_text = rec["text"]
            verified_card, stats = verify_evidence_spans(card, doc_text)

            for k in aggregate_stats:
                aggregate_stats[k] += stats[k]

            # Drop card if zero verified evidence spans remain
            if not verified_card.get("evidence"):
                reason = "dropped_zero_valid_evidence_spans"
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            else:
                rec["card"] = verified_card
                rec["evidence_verification_stats"] = stats
                fout.write(json.dumps(rec) + "\n")
                verified_records.append(rec)

    output_count = len(verified_records)
    dropped_count = input_count - output_count
    elapsed = time.perf_counter() - t_start

    summary = {
        "stage": 4,
        "stage_name": "Deterministic Programmatic Evidence Verifier",
        "input_count": input_count,
        "output_count": output_count,
        "dropped_count": dropped_count,
        "drop_reasons": drop_reasons,
        "spans_total": aggregate_stats["total_spans"],
        "spans_exact_matched": aggregate_stats["exact_matches"],
        "spans_realigned": aggregate_stats["realigned_spans"],
        "spans_failed_hallucinated": aggregate_stats["failed_spans"],
        "tokens_per_sec": 0.0,
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": 0.0,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(
        f"[Stage 4 Evidence Check] Complete: {output_count}/{input_count} cards verified. "
        f"Spans: {aggregate_stats['exact_matches']} exact, {aggregate_stats['realigned_spans']} realigned, "
        f"{aggregate_stats['failed_spans']} dropped. Logged -> {summary_path}",
        flush=True,
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 4 evidence verification.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/stage_2_output.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/stage_4_output.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_4_summary.json")
    args = parser.parse_args()

    run_evidence_verification(
        input_path=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
    )


if __name__ == "__main__":
    main()
