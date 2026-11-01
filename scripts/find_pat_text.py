import json

with open('/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl', 'r') as f:
    for line in f:
        d = json.loads(line)
        cid = d.get('doc_id')
        if cid == 'US-PAT-F-0291':
            text = d.get('text', '')
            print("US-PAT-F-0291 text len:", len(text))
            # find where 'speed of the fan' or 'fan motor' appears
            pos = text.lower().find('fan motor')
            if pos != -1:
                print("Found 'fan motor' at", pos)
                print("Context:", repr(text[pos-50:pos+250]))
            else:
                print("Did not find 'fan motor'")
        elif cid == 'US-PAT-F-0115':
            text = d.get('text', '')
            print("US-PAT-F-0115 text len:", len(text))
            pos = text.lower().find('subcooled')
            if pos != -1:
                print("Found 'subcooled' at", pos)
                print("Context:", repr(text[pos-50:pos+250]))
            else:
                print("Did not find 'subcooled'")
