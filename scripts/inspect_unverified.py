import json

with open('/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json', 'r') as f:
    av = json.load(f)

for a in av["all_card_audits"]:
    cid = a.get("doc_id")
    if cid in ["US-PAT-F-0291", "US-PAT-F-0115"]:
        print(f"=== {cid} ===")
        print("Flaw quote stored:", repr(a.get("quoted_source_passage_for_flaw")))
        print("Issues:", a.get("issues"))
