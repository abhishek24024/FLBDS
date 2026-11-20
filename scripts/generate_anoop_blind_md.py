import json

def main():
    with open("flbds_data/audit9/anoop_blind_packet.json") as f:
        blind_packet = json.load(f)

    md = []
    md.append("# A-NoOp Blind Evaluation Packet (6 Transcripts)")
    md.append("")
    md.append("**Notice**: All pass/fail labels, evaluator assertions, and model identities have been stripped.")
    md.append("Transcripts are presented in random order (seeded by seed 63).")
    md.append("")

    for item in blind_packet:
        pid = item["packet_id"]
        cid = item["case_id"]
        turns = item["feedback_turns_used"]
        history = item["feedback_history"]
        final_design = item["final_design_json"]

        md.append(f"## Transcript {pid}")
        md.append(f"- **Benchmark Case**: `{cid}`")
        md.append(f"- **Feedback Iterations Used**: `{turns}`")
        md.append("")
        
        if not history:
            md.append("*(No feedback turns were required; initial proposed design was evaluated directly)*")
            md.append("")
        else:
            for h in history:
                md.append(f"### Feedback Round {h.get('feedback_turn')}")
                md.append(f"**Physical Feedback Delivered to Model**:")
                md.append("```text")
                md.append(str(h.get("previous_reason")))
                md.append("```")
                md.append(f"**Revised Model JSON Proposal**:")
                md.append("```json")
                md.append(str(h.get("model_response")))
                md.append("```")
                md.append("")

        md.append("### Final Proposed Design")
        md.append("```json")
        md.append(json.dumps(final_design, indent=2))
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    with open("docs/audit/anoop_blind_packet.md", "w") as f:
        f.write("\n".join(md))

    print("Wrote docs/audit/anoop_blind_packet.md")

if __name__ == "__main__":
    main()
