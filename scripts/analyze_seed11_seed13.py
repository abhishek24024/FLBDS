import json

with open('/home/abhishek24024/flbds_data/review/seed11_sampled_24.json', 'r') as f:
    s11 = json.load(f)

with open('/home/abhishek24024/flbds_data/review/stage5_effect_audit_seed13.json', 'r') as f:
    s13 = json.load(f)

s11_bio = [x['doc_id'] for x in s11.get('bio', [])]
s11_eng = [x['doc_id'] for x in s11.get('eng', [])]
s11_all = s11_bio + s11_eng

s13_accepted = [x['doc_id'] for x in s13.get('sampled_accepted', [])]
s13_drops = [x['doc_id'] for x in s13.get('sampled_drops', [])]

overlap_s11_s13_acc = set(s11_all).intersection(set(s13_accepted))
overlap_s11_s13_drp = set(s11_all).intersection(set(s13_drops))

print(f"Seed 11 total: {len(s11_all)} (12 bio, 12 eng)")
print(f"Seed 13 accepted total: {len(s13_accepted)}")
print(f"Overlap between Seed 11 and Seed 13 accepted: {len(overlap_s11_s13_acc)} -> {sorted(list(overlap_s11_s13_acc))}")
print(f"Overlap between Seed 11 and Seed 13 drops: {len(overlap_s11_s13_drp)} -> {sorted(list(overlap_s11_s13_drp))}")

union_accepted = sorted(list(set(s11_all).union(set(s13_accepted))))
print(f"Total unique cards in union of accepted samples: {len(union_accepted)}")
