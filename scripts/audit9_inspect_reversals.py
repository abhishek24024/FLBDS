import json
from pathlib import Path

# Load corpus documents
docs = {}
for cpath in ['/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl', '/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl']:
    with open(cpath) as f:
        for line in f:
            d = json.loads(line)
            did = d.get('doc_id') or d.get('id')
            if did:
                docs[did] = d

targets = ['PMC8593863', 'US-PAT-E-0478', 'US-PAT-E-0427', 'US-PAT-F-0220']

with open('/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json') as f:
    av = json.load(f)
r3_records = {a['doc_id']: a for a in av.get('all_card_audits', []) if a['doc_id'] in targets}

# Round 8 descriptions
r8_descriptions = {
    'PMC8593863': 'MINOR: Capillary wicking is primary mechanism; 1 span had minor paraphrasing.',
    'US-PAT-E-0478': 'MINOR: Vacuum annulus insulation genuine; missing subject repaired in audit6.',
    'US-PAT-E-0427': 'GOOD: Cryogenic tank insulation authentic across 2 exact spans.',
    'US-PAT-F-0220': 'MINOR: Piping insulation genuine; ungrounded candidate pruned by Rule 1.',
}

results = []

for did in targets:
    cdoc = docs.get(did, {})
    text = cdoc.get('text', cdoc.get('body', ''))
    title = cdoc.get('title', '')
    first_400 = text[:400]
    
    r3 = r3_records.get(did, {})
    r3_quote = r3.get('quoted_source_passage_for_flaw', '')
    r3_verdict = r3.get('verdict', '')
    r3_issues = r3.get('issues', [])
    
    # Locate quote in corpus
    start_idx = text.find(r3_quote) if r3_quote else -1
    end_idx = start_idx + len(r3_quote) if start_idx != -1 else -1
    
    # Also check card evidence spans
    spans = r3.get('card_fields', {}).get('evidence_spans', [])
    span_matches = []
    for s in spans:
        idx = text.find(s)
        span_matches.append((s, idx, idx + len(s) if idx != -1 else -1))
        
    results.append({
        'doc_id': did,
        'title': title,
        'first_400': first_400,
        'r3_quote': r3_quote,
        'r3_offsets': (start_idx, end_idx),
        'corpus_slice': text[start_idx:end_idx] if start_idx != -1 else None,
        'r3_verdict': r3_verdict,
        'r3_issues': r3_issues,
        'r8_desc': r8_descriptions.get(did, ''),
        'spans_in_corpus': span_matches,
    })

for res in results:
    print('======================================================================')
    print(f"DOCUMENT ID: {res['doc_id']}")
    print(f"CORPUS TITLE: {res['title']}")
    print("--- FIRST 400 CHARACTERS OF SOURCE TEXT ---")
    print(repr(res['first_400']))
    print("--- ROUND 3 QUOTED PASSAGE & OFFSETS ---")
    print(f"Quote: {repr(res['r3_quote'])}")
    print(f"Offsets: {res['r3_offsets']}")
    if res['r3_offsets'][0] != -1:
        print(f"corpus[{res['r3_offsets'][0]}:{res['r3_offsets'][1]}]: {repr(res['corpus_slice'])}")
    else:
        print("-> QUOTE NOT FOUND EXACTLY IN CORPUS!")
    print("--- EVIDENCE SPANS GROUNDING ---")
    for s, st, en in res['spans_in_corpus']:
        found = "FOUND" if st != -1 else "NOT FOUND"
        print(f"  [{found}] [{st}:{en}] {repr(s[:80])}")
    print("--- ROUND 3 VERDICT & ISSUES ---")
    print(f"R3 Verdict: {res['r3_verdict']} | Issues: {res['r3_issues']}")
    print("--- ROUND 8 DESCRIPTION ---")
    print(f"R8 Desc: {res['r8_desc']}")
