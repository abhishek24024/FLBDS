import json

with open("flbds_data/audit9/a_noop_results.json") as f:
    data = json.load(f)

runs = {}
for r in data["results"]:
    runs[f"{r['case_id']}_S{r['seed']}"] = r

sample_keys = [
    "DEV-M1-S3_S4", "DEV-M1-S3_S3", "DEV-M4-S3_S2",
    "DEV-M1-S1_S3", "DEV-M3-S2_S4", "DEV-M2-S1_S1"
]

for k in sample_keys:
    r = runs[k]
    print("="*70)
    print(f"CASE: {r['case_id']} | SEED: {r['seed']} | PASSED: {r['passed']} | TURNS: {r['feedback_turns_used']}")
    print(f"INITIAL TURN 3 OUTPUT:\n{r.get('initial_turn3_raw')}")
    print(f"FEEDBACK TURNS ({len(r.get('feedback_history', []))}):")
    for h in r.get("feedback_history", []):
        print(f"  -- Feedback Turn {h.get('feedback_turn')} (Total Turn {h.get('total_turn')}):")
        print(f"     Reason Failed: {h.get('previous_reason')}")
        print(f"     Model Response: {h.get('model_response')}")
        print(f"     New Result: passed={h.get('new_passed')}, reason={h.get('new_reason')}")
    print(f"FINAL OUTPUT:\n{r.get('final_raw_output')}")
    print(f"FINAL VERDICT: passed={r.get('passed')}, failure_type={r.get('failure_type')}")
    print(f"FINAL REASON: {r.get('reason')}")
