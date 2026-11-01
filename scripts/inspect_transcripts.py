import json

with open('/home/abhishek24024/flbds_data/benchmark/selected_10_transcripts.json') as f:
    d = json.load(f)

print('=== 5 PASSES ===\n')
for i, p in enumerate(d['passes']):
    print(f'PASS #{i+1}: Case {p["case_id"]} (Seed {p["seed"]}, Split {p["split"]})')
    print('Template chosen:', p.get('parsed_json', {}).get('template_id'))
    print('Turn 1 Model Thought/Proposal (excerpt):')
    print('  ' + p['turn1_response'][:300].replace('\n', '\n  '))
    print('Turn 2 Self-Critique (excerpt):')
    print('  ' + p['turn2_response'][:300].replace('\n', '\n  '))
    print('Turn 3 Refined Parameters:')
    print('  ' + json.dumps(p['parsed_json'], indent=4).replace('\n', '\n  '))
    print('-'*60 + '\n')

print('=== 5 FAILS ===\n')
for i, f in enumerate(d['fails']):
    print(f'FAIL #{i+1}: Case {f["case_id"]} (Seed {f["seed"]}, Split {f["split"]})')
    print('Failure Type:', f['failure_type'])
    print('Failure Reason:', f['reason'])
    print('Template chosen:', f.get('parsed_json', {}).get('template_id'))
    print('Turn 1 Model Thought/Proposal (excerpt):')
    print('  ' + f['turn1_response'][:300].replace('\n', '\n  '))
    print('Turn 2 Self-Critique (excerpt):')
    print('  ' + f['turn2_response'][:300].replace('\n', '\n  '))
    print('Turn 3 Refined Parameters:')
    print('  ' + json.dumps(f['parsed_json'], indent=4).replace('\n', '\n  '))
    print('-'*60 + '\n')
