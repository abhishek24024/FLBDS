import json
import random

def main():
    with open("flbds_data/audit10/oracle_feedback_results.json") as f:
        data = json.load(f)

    results = data["results"]
    passes = [r for r in results if r["passed"]]
    fails = [r for r in results if not r["passed"]]

    print(f"Total Oracle runs: {len(results)} (Passes: {len(passes)}, Fails: {len(fails)})")

    # Sample 4 passes and 4 fails using seed 64
    rng = random.Random(64)
    sampled_passes = rng.sample(passes, 4)
    sampled_fails = rng.sample(fails, 4)

    print("\nSampled Passes (seed 64):")
    for p in sampled_passes:
        print(f"  Pass: {p['case_id']}_s{p['seed']} | Turns: {p['feedback_turns_used']} | Reason: {p['reason'][:70]}")

    print("\nSampled Fails (seed 64):")
    for f in sampled_fails:
        print(f"  Fail: {f['case_id']}_s{f['seed']} | Turns: {f['feedback_turns_used']} | Reason: {f['reason'][:70]}")

    # Combine and shuffle with seed 64 for blind packet
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
        pid = f"BLIND-R10-{packet_num:02d}"

        # Strip pass/fail labels from feedback history
        blind_history = []
        for h in run.get("feedback_history", []):
            blind_history.append({
                "feedback_turn": h.get("feedback_turn"),
                "evaluator_feedback_given_to_model": h.get("previous_reason"),
                "model_revised_response": h.get("model_response")
            })

        blind_entry = {
            "packet_id": pid,
            "case_id": run["case_id"],
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
            "final_reason": run["reason"]
        })

    with open("flbds_data/audit10/anoop_round10_blind_packet.json", "w") as f:
        json.dump(blind_packet, f, indent=2)

    with open("flbds_data/audit10/anoop_round10_review_key.json", "w") as f:
        json.dump(key_verdicts, f, indent=2)

    # Generate Markdown blind packet
    md = []
    md.append("# Audit Round 10 Blind Evaluation Packet (8 Transcripts)")
    md.append("")
    md.append("> **Instructions**: Pass/fail labels, verifier internal statuses, and seed numbers have been stripped.")
    md.append("> Review each transcript against physical reality. Evaluate whether the model appropriately resolved the engineering requirements, changed templates, or merely gamed the feedback.")
    md.append("")

    for b in blind_packet:
        pid = b["packet_id"]
        cid = b["case_id"]
        turns = b["feedback_turns_used"]
        init_resp = b["initial_model_response"]
        hist = b["feedback_iterations"]
        final_params = b["final_model_parameters"]

        md.append(f"## Transcript {pid}")
        md.append(f"- **Benchmark Case**: `{cid}`")
        md.append(f"- **Feedback Iterations Used**: `{turns}`")
        md.append("")
        md.append("### Initial Model Proposal")
        md.append("```text")
        md.append(init_resp.strip())
        md.append("```")
        md.append("")

        if not hist:
            md.append("*(No feedback turns needed; initial proposal evaluated directly)*\n")
        else:
            for h in hist:
                md.append(f"### Feedback Round {h.get('feedback_turn')}")
                md.append("**Physical Feedback Delivered to Model**:")
                md.append("```text")
                md.append(str(h.get("evaluator_feedback_given_to_model")))
                md.append("```")
                md.append("**Model Revised JSON Proposal**:")
                md.append("```json")
                md.append(str(h.get("model_revised_response")))
                md.append("```")
                md.append("")

        md.append("### Final Proposed Design JSON")
        md.append("```json")
        md.append(json.dumps(final_params, indent=2))
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    with open("docs/audit/anoop_round10_blind_packet.md", "w") as f:
        f.write("\n".join(md))

    print("\nWrote blind packet to docs/audit/anoop_round10_blind_packet.md")
    print("Wrote review key to flbds_data/audit10/anoop_round10_review_key.json")

if __name__ == "__main__":
    main()
