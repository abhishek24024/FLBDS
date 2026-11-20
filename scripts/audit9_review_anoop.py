import json
import random
import math

def wilson_ci(k, n, confidence=0.95):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959964  # 95%
    p_hat = k / n
    denom = 1.0 + (z**2) / n
    center = (p_hat + (z**2) / (2 * n)) / denom
    diff = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / n) + ((z**2) / (4 * n**2)))
    return (max(0.0, center - diff), min(1.0, center + diff))

def main():
    with open("flbds_data/audit9/a_noop_results.json") as f:
        data = json.load(f)

    results = data["results"]
    passes = [r for r in results if r["passed"]]
    fails = [r for r in results if not r["passed"]]

    n_total = len(results)
    k_passes = len(passes)
    p_rate = k_passes / n_total
    ci_low, ci_high = wilson_ci(k_passes, n_total)

    print(f"=== A-NoOp Benchmark Results ===")
    print(f"Total Runs: {n_total}")
    print(f"Passes: {k_passes} ({p_rate*100:.1f}%)")
    print(f"Fails: {len(fails)} ({len(fails)/n_total*100:.1f}%)")
    print(f"95% Wilson CI: [{ci_low:.3f}, {ci_high:.3f}] ({ci_low*100:.1f}% to {ci_high*100:.1f}%)")

    # B0 valid run comparison: 14/60 (23.3%)
    b0_passes = 14
    b0_low, b0_high = wilson_ci(b0_passes, 60)
    print(f"B0 Valid Baseline: {b0_passes}/60 ({b0_passes/60*100:.1f}%), 95% Wilson CI: [{b0_low:.3f}, {b0_high:.3f}]")

    # Sample 6 transcripts: 3 pass, 3 fail with seed 63
    rng = random.Random(63)
    sampled_passes = rng.sample(passes, 3)
    sampled_fails = rng.sample(fails, 3)

    print("\n=== Sampled 3 Passes (seed 63) ===")
    for p in sampled_passes:
        print(f"Case: {p['case_id']}, Seed: {p['seed']}, Turns used: {p['feedback_turns_used']}, Reason: {p['reason']}")

    print("\n=== Sampled 3 Fails (seed 63) ===")
    for f in sampled_fails:
        print(f"Case: {f['case_id']}, Seed: {f['seed']}, Turns used: {f['feedback_turns_used']}, Failure Type: {f['failure_type']}, Reason: {f['reason']}")

    # Detailed inspection of the 6 transcripts
    reviewed_cases = []
    
    # 1. First Pass
    for r in sampled_passes:
        history = r.get("feedback_history", [])
        reviewed_cases.append({
            "transcript_id": f"ANOOP-{r['case_id']}-S{r['seed']}",
            "case_id": r["case_id"],
            "seed": r["seed"],
            "true_verdict": "PASS",
            "turns_used": r["feedback_turns_used"],
            "final_reason": r["reason"],
            "feedback_history": history,
            "final_parsed_json": r["final_parsed_json"]
        })

    for r in sampled_fails:
        history = r.get("feedback_history", [])
        reviewed_cases.append({
            "transcript_id": f"ANOOP-{r['case_id']}-S{r['seed']}",
            "case_id": r["case_id"],
            "seed": r["seed"],
            "true_verdict": "FAIL",
            "failure_type": r["failure_type"],
            "turns_used": r["feedback_turns_used"],
            "final_reason": r["reason"],
            "feedback_history": history,
            "final_parsed_json": r["final_parsed_json"]
        })

    # Shuffle the 6 transcripts for the blind packet using seed 63
    shuffled_indices = list(range(6))
    rng.shuffle(shuffled_indices)

    blind_packet = []
    key_packet = []

    for item_idx, orig_idx in enumerate(shuffled_indices, 1):
        item = reviewed_cases[orig_idx]
        blind_entry = {
            "packet_id": f"BLIND-{item_idx:02d}",
            "case_id": item["case_id"],
            "feedback_turns_used": item["turns_used"],
            "feedback_history": item["feedback_history"],
            "final_design_json": item["final_parsed_json"]
        }
        blind_packet.append(blind_entry)
        key_packet.append({
            "packet_id": f"BLIND-{item_idx:02d}",
            "case_id": item["case_id"],
            "seed": item["seed"],
            "verdict": item["true_verdict"],
            "reason": item["final_reason"]
        })

    with open("flbds_data/audit9/anoop_blind_packet.json", "w") as f:
        json.dump(blind_packet, f, indent=2)

    with open("flbds_data/audit9/anoop_review_key.json", "w") as f:
        json.dump(key_packet, f, indent=2)

    print("\nSaved blind packet and review key to flbds_data/audit9/")

if __name__ == "__main__":
    main()
