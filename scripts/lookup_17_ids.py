import json

corpus = {}
for p in ['/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl', '/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl']:
    with open(p, 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            corpus[d['doc_id']] = d

minor_ids = ['PMC9234854', 'PMC9502598', 'PMC9782502', 'PMC9915001', 'PMC10052300',
             'US-PAT-F-0104', 'US-PAT-F-0205', 'US-PAT-E-0312', 'US-PAT-E-0418', 'US-PAT-F-0520']
major_ids = ['PMC8531342', 'PMC8912401', 'PMC9123456', 'PMC9654321',
             'US-PAT-F-0321', 'US-PAT-E-0493', 'US-PAT-F-0511']

print('=== 10 MINOR IDS IN ACTUAL CORPUS ===')
for cid in minor_ids:
    if cid in corpus:
        print(f'{cid}: FOUND -> Title: {corpus[cid].get("title")}')
    else:
        print(f'{cid}: NOT IN CORPUS')

print('\n=== 7 MAJOR IDS IN ACTUAL CORPUS ===')
for cid in major_ids:
    if cid in corpus:
        print(f'{cid}: FOUND -> Title: {corpus[cid].get("title")}')
    else:
        print(f'{cid}: NOT IN CORPUS')
