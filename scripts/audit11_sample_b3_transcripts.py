#!/usr/bin/env python3
"""scripts/audit11_sample_b3_transcripts.py
Performs seeded human-style sampling (seed 65) of 8 B3 transcripts (4 pass, 4 fail).
Generates:
1. docs/audit/b3_round11_blind_packet.md (blind review packet with labels stripped)
2. docs/audit/b3_round11_review_key.json (answer key mapping packet ID to ground truth)
3. docs/audit/b3_round11_transcript_review.md (auditor review against rubric and taxonomy)
"""

import json
import random
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent
    b3_path = repo_root / "flbds_data" / "audit11" / "b3_dev_results.json"
    
    if not b3_path.is_file():
        print(f"Error: {b3_path} does not exist yet. Run after benchmarks complete.")
        return

    with open(b3_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    passes = [r for r in results if r["passed"]]
    fails = [r for r in results if not r["passed"]]

    print(f"Total B3 runs: {len(results)} (Passes: {len(passes)}, Fails: {len(fails)})")

    # Sample 4 passes and 4 fails using seed 65
    rng = random.Random(65)
    sampled_passes = rng.sample(passes, 4)
    sampled_fails = rng.sample(fails, 4)

    print("\nSampled Passes (seed 65):")
    for p in sampled_passes:
        print(f"  Pass: {p['case_id']}_s{p['seed']} | Op: {p['applied_operator']} | Turns: {p['feedback_turns_used']} | Reason: {p['reason'][:70]}")

    print("\nSampled Fails (seed 65):")
    for f in sampled_fails:
        print(f"  Fail: {f['case_id']}_s{f['seed']} | Op: {f['applied_operator']} | Turns: {f['feedback_turns_used']} | Reason: {f['reason'][:70]}")

    # Combine and shuffle with seed 65 for blind packet
    combined = []
    for p in sampled_passes:
        combined.append({"item": p, "true_verdict": "PASS"})
    for f in sampled_fails:
        combined.append({"item": f, "true_verdict": "FAIL"})

    shuffled_indices = list(range(8))
    rng.shuffle(shuffled_indices)

    blind_packet = []
    key_verdicts = []

    for packet_num, idx in enumerate(shuffled_indices, 1):
        c = combined[idx]
        run = c["item"]
        v = c["true_verdict"]
        pid = f"BLIND-B3-R11-{packet_num:02d}"

        # Strip pass/fail labels from feedback history
        blind_history = []
        for h in run.get("feedback_history", []):
            blind_history.append({
                "feedback_turn": h.get("feedback_turn"),
                "screen_feedback_received": h.get("previous_reason"),
                "model_revised_response": h.get("model_response")
            })

        blind_entry = {
            "packet_id": pid,
            "case_id": run["case_id"],
            "seed": run["seed"],
            "target_template": run["target_template"],
            "applied_operator": run["applied_operator"],
            "proof_obligation": run["proof_obligation"],
            "feedback_turns_used": run["feedback_turns_used"],
            "initial_model_response": run["initial_response"],
            "feedback_iterations": blind_history,
            "final_model_parameters": run["final_parsed_json"]
        }
        blind_packet.append(blind_entry)

        key_verdicts.append({
            "packet_id": pid,
            "case_id": run["case_id"],
            "seed": run["seed"],
            "true_verdict": v,
            "applied_operator": run["applied_operator"],
            "screen_verdict": "PASS" if run.get("screen_passed") else "FAIL",
            "screen_reason": run.get("screen_reason"),
            "eval_verdict": v,
            "eval_reason": run.get("reason")
        })

    out_dir = repo_root / "docs" / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "b3_round11_review_key.json", "w", encoding="utf-8") as f:
        json.dump(key_verdicts, f, indent=2)

    # Generate Markdown blind packet
    md = []
    md.append("# Audit Round 11 Blind Evaluation Packet (8 B3 Transcripts)")
    md.append("")
    md.append("> **Instructions for Reviewer**: Pass/fail labels, verifier internal statuses, and seed numbers have been stripped.")
    md.append("> Review each transcript against physical reality. Evaluate whether:")
    md.append("> 1. Did the model accept and respect the M4 Operator transformation and proof obligation?")
    md.append("> 2. Did the model preserve the assigned physical template?")
    md.append("> 3. Did the parameters physically satisfy the lumped Screen and coupled Eval checks, or did it game the bounds?")
    md.append("")

    for b in blind_packet:
        pid = b["packet_id"]
        cid = b["case_id"]
        op = b["applied_operator"]
        proof = b["proof_obligation"]
        turns = b["feedback_turns_used"]
        init_resp = b["initial_model_response"]
        hist = b["feedback_iterations"]
        final_params = b["final_model_parameters"]

        md.append(f"## Transcript {pid}")
        md.append(f"- **Benchmark Case**: `{cid}`")
        md.append(f"- **Assigned Operator Guidance**: `{op}`")
        md.append(f"- **Target Template**: `{b['target_template']}`")
        md.append(f"- **Proof Obligation**: `{proof}`")
        md.append(f"- **Feedback Iterations Used**: `{turns}`")
        md.append("")
        md.append("### Initial Model Proposal")
        md.append("```text")
        md.append(init_resp.strip())
        md.append("```")
        md.append("")

        if hist:
            md.append("### Feedback Iterations")
            for h in hist:
                md.append(f"#### Turn {h['feedback_turn']} M5-Screen Feedback:")
                md.append(f"> `{h['screen_feedback_received']}`")
                md.append("")
                md.append("#### Model Revised Response:")
                md.append("```json")
                md.append(h['model_revised_response'].strip())
                md.append("```")
                md.append("")

        md.append("### Final Extracted Design Parameters")
        md.append("```json")
        md.append(json.dumps(final_params, indent=2))
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    blind_md_path = out_dir / "b3_round11_blind_packet.md"
    with open(blind_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Successfully generated blind packet at: {blind_md_path}")
    print(f"Successfully generated review key at: {out_dir / 'b3_round11_review_key.json'}")

if __name__ == "__main__":
    main()
