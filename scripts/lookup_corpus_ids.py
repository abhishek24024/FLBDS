import json

corpus_docs = {}
for path in ['/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl', '/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl']:
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            corpus_docs[d['doc_id']] = d

check_ids = [
    'PMC8531342', 'US-PAT-F-0321', 'US-PAT-E-0493',
    'PMC9234854', 'PMC9502598', 'PMC9782502', 'PMC9915001', 'PMC10052300',
    'US-PAT-F-0104', 'US-PAT-F-0205', 'US-PAT-E-0312', 'US-PAT-E-0418', 'US-PAT-F-0520',
    'PMC8912401', 'PMC9123456', 'PMC9654321', 'US-PAT-F-0511',
    'PMC5697934', 'PMC13164731', 'US-PAT-F-0220', 'US-PAT-F-0063'
]

print(f'Total corpus docs indexed: {len(corpus_docs)}')
for cid in check_ids:
    if cid in corpus_docs:
        rec = corpus_docs[cid]
        print(f'{cid}: FOUND -> Title: {rec.get(title)}')
    else:
        print(f'{cid}: NOT FOUND in corpus!')
