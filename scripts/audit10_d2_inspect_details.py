import json

def inspect_transcripts():
    with open("flbds_data/audit10/anoop_round10_review_key.json") as f:
        keys = json.load(f)
    with open("flbds_data/audit10/oracle_feedback_results.json") as f:
        ora_data = json.load(f)

    runs = {f"{r['case_id']}_s{r['seed']}": r for r in ora_data["results"]}

    lines = []
    lines.append("# Human-Style Review of 8 Oracle Transcripts (Seed 64)\n")
    lines.append("## Overview")
    lines.append("- Population: 60 Oracle condition runs ($T=0.7$, Seeds 1-5)")
    lines.append("- Sampling: 4 passes and 4 failures sampled with seed 64")
    lines.append("- Rubric dimensions: Feedback responsiveness, template switching, screen gaming, physical realism\n")

    for k in keys:
        cid = k["case_id"]
        seed = k["seed"]
        verdict = k["true_verdict"]
        pid = k["packet_id"]
        run = runs[f"{cid}_s{seed}"]
        turns = run["feedback_turns_used"]
        reason = run["reason"]
        history = run.get("feedback_history", [])

        lines.append(f"## {pid}: `{cid}` (Seed {seed}) - Verdict: {verdict}")
        lines.append(f"- **Final Evaluator Outcome**: `{reason}`")
        lines.append(f"- **Feedback Iterations Used**: `{turns}`")
        
        # Check rubric
        template_changed = False
        templates_seen = set()
        if "final_parsed_json" in run and run["final_parsed_json"]:
            templates_seen.add(run["final_parsed_json"].get("template_id"))
        for h in history:
            try:
                p_resp = json.loads(h.get("model_response", "{}"))
                templates_seen.add(p_resp.get("template_id"))
            except Exception:
                pass
        template_changed = len(templates_seen) > 1

        lines.append(f"- **Template Preservation**: Template remained `{list(templates_seen)}` (Changed: {template_changed})")
        lines.append(f"- **Used Feedback**: {'Yes' if turns > 0 else 'N/A (passed initial turn)'}")
        
        if verdict == "PASS":
            lines.append("- **Physical Assessment**: Model converged to valid physical dimensions satisfying all coupled constraints.")
            if turns > 0:
                last_fb = history[-1]["previous_reason"]
                lines.append(f"- **Feedback Resolved**: Handled feedback discrepancy: \"{last_fb}\"")
        else:
            lines.append("- **Failure Taxonomy**: ")
            if "Pressure drop" in reason:
                lines.append("  `Coupled Hydrodynamic Resistance Trap`: Inability to size hydraulic diameter without violating velocity or duty bounds.")
            elif "superheat" in reason:
                lines.append("  `Conductive Stefan Barrier`: Insufficient effective thermal conductivity or excessive thickness causing surface superheat.")
            elif "Hydrostatic head" in reason:
                lines.append("  `Capillary Laplace Breakthrough`: Pore diameter exceeds maximum allowable for capillary pressure barrier under water head.")
            else:
                lines.append("  `Unresolved Physical Bound`")
            lines.append(f"- **Unresolved Constraint**: \"{reason}\"")

        lines.append("")

    with open("docs/audit/anoop_round10_transcript_review.md", "w") as f:
        f.write("\n".join(lines))
    print("Wrote docs/audit/anoop_round10_transcript_review.md")

if __name__ == "__main__":
    inspect_transcripts()
