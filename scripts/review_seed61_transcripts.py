import json

with open("/home/abhishek24024/flbds_data/audit8/seed61_sampled_6_transcripts.json") as f:
    d = json.load(f)

for category in ["sampled_passes", "sampled_fails"]:
    print("=" * 80)
    print(f"Category: {category}")
    for r in d[category]:
        cid = r["case_id"]
        split = r["split"]
        seed = r["seed"]
        passed = r["passed"]
        ft = r.get("failure_type")
        reason = r.get("reason")
        params = r.get("parsed_json", {})
        print("-" * 60)
        print(f"Case: {cid} | Split: {split} | Seed: {seed} | Passed: {passed} | Failure: {ft}")
        print(f"Outcome Reason: {reason}")
        print(f"Turn 1 Proposal: {r.get('turn1_response', '')[:250]}...")
        print(f"Turn 2 Critique: {r.get('turn2_response', '')[:250]}...")
        print(f"Turn 3 JSON: {json.dumps(params, indent=2)}")
