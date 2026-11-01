import json
import re
from pathlib import Path
from pint import UnitRegistry

ureg = UnitRegistry()

def is_number_in_span(val: float, span: str) -> bool:
    s_val = str(val)
    if s_val.endswith(".0"):
        s_val_int = str(int(val))
        if re.search(r'\b' + re.escape(s_val_int) + r'\b', span):
            return True
    if re.search(r'\b' + re.escape(s_val) + r'\b', span):
        return True
    if re.search(r'\b' + re.escape(f"{val:.1f}") + r'\b', span):
        return True
    if re.search(r'\b' + re.escape(f"{val:.2f}") + r'\b', span):
        return True
    return False

def find_number_span_in_text(val: float, text: str):
    s_val = str(val)
    candidates = [s_val]
    if s_val.endswith(".0"):
        candidates.append(str(int(val)))
    candidates.append(f"{val:.1f}")
    candidates.append(f"{val:.2f}")

    for cand in candidates:
        m = re.search(r'\b' + re.escape(cand) + r'\b', text)
        if m:
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            snippet = text[start:end].replace('\n', ' ').strip()
            return snippet
    return None

def sanitize_quantity(val: float, unit_str: str):
    u = unit_str.strip()
    u = u.replace('−', '-').replace('–', '-')
    u = re.sub(r'wt\.?\s*%', 'percent', u, flags=re.IGNORECASE)
    u = re.sub(r'vol\.?\s*%', 'percent', u, flags=re.IGNORECASE)
    m = re.search(r'([x×*]\s*10\^?([+-]?\d+))', u)
    scale = 1.0
    if m:
        exp = int(m.group(2))
        scale = 10.0 ** exp
        u = u.replace(m.group(1), '').strip()
    val = val * scale
    return val, u

# Load full corpus text for relinking
corpus_texts = {}
for cp in ['/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl', '/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl']:
    with open(cp, 'r', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            cid = d.get('doc_id') or d.get('id')
            if cid:
                corpus_texts[cid] = (d.get('title', '') + ' ' + d.get('abstract', '') + ' ' + d.get('text', ''))

# Also load pilot stage 6 input
in_path = '/home/abhishek24024/flbds_data/pilot/stage_6_output.orig.jsonl'
if not Path(in_path).exists():
    in_path = '/home/abhishek24024/flbds_data/pilot/stage_6_output.jsonl'

print(f"Reading candidate quantities from {in_path}...")

in_cited_span = []
relinked_in_doc = []
nowhere = []

total_candidate_quantities = 0

with open(in_path, 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        doc_id = rec.get("doc_id")
        doc_text = corpus_texts.get(doc_id, "")
        card = rec.get("card", {})
        evidence_spans = [ev.get("text_span", "") for ev in card.get("evidence", [])]
        
        quantities = card.get("quantities", [])
        for q in quantities:
            total_candidate_quantities += 1
            val = q.get("value")
            name = q.get("name")
            unit = q.get("unit")
            
            # Check 1: in cited span
            in_span = False
            for span in evidence_spans:
                if is_number_in_span(val, span):
                    in_span = True
                    break
            
            if in_span:
                in_cited_span.append({"doc_id": doc_id, "name": name, "value": val, "unit": unit})
            else:
                # Check 2: in document text
                found_span = find_number_span_in_text(val, doc_text)
                if found_span:
                    relinked_in_doc.append({"doc_id": doc_id, "name": name, "value": val, "unit": unit, "relinked_span": found_span})
                else:
                    nowhere.append({"doc_id": doc_id, "name": name, "value": val, "unit": unit})

print("=========================================================")
print(f"Total candidate quantities evaluated: {total_candidate_quantities}")
print(f"  1. In cited span:     {len(in_cited_span)} ({len(in_cited_span)/total_candidate_quantities*100:.1f}%)")
print(f"  2. Re-linked in doc:  {len(relinked_in_doc)} ({len(relinked_in_doc)/total_candidate_quantities*100:.1f}%)")
print(f"  3. Nowhere in doc:    {len(nowhere)} ({len(nowhere)/total_candidate_quantities*100:.1f}%)")
print("=========================================================")

out_summary = {
    "total_candidates": total_candidate_quantities,
    "in_cited_span_count": len(in_cited_span),
    "relinked_in_doc_count": len(relinked_in_doc),
    "nowhere_in_doc_count": len(nowhere),
    "sample_in_span": in_cited_span[:5],
    "sample_relinked": relinked_in_doc[:5],
    "sample_nowhere": nowhere[:5],
}

with open('/home/abhishek24024/flbds_data/pilot/stage_6_relinked_summary.json', 'w') as f:
    json.dump(out_summary, f, indent=2)

print("Saved relinked summary to /home/abhishek24024/flbds_data/pilot/stage_6_relinked_summary.json")
