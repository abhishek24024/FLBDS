import json

with open('/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json', 'r') as f:
    av = json.load(f)

audits = av.get("all_card_audits", [])
print(f"Total audits: {len(audits)}")

for i, a in enumerate(audits):
    doc_id = a.get("doc_id")
    v = a.get("verdict")
    domain = a.get("domain")
    reason = a.get("reason", a.get("verdict_reason", a.get("notes", "")))
    print(f"[{i+1}/{len(audits)}] {doc_id} ({domain}): {v} | Reason: {str(reason)[:90]}")
