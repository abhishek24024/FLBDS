import json

with open('/home/abhishek24024/flbds_data/audit9/sample20_seed72_provenance.json') as f:
    sample = json.load(f)

for i, q in enumerate(sample):
    print(f"[{i+1}/20] {q['doc_id']}: {q['name']} = {q['value']} {q['unit']} | Prov: {q['provenance']}")
    print(f"   Reason: {q['reason']}")
    print(f"   Snippet: {repr(q['snippet'])}")
