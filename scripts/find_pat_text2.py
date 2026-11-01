import json

with open('/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl', 'r') as f:
    for line in f:
        d = json.loads(line)
        if d.get('doc_id') == 'US-PAT-F-0291':
            text = d.get('text', '')
            for term in ['5°', 'kelvin', 'desired default']:
                pos = text.lower().find(term)
                print(f"Term '{term}' in F-0291: {pos}")
                if pos != -1:
                    print("Context:", repr(text[pos-40:pos+160]))
