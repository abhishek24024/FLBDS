#!/usr/bin/env python3
"""Audit Round 9: Strict Provenance Rule Implementation for Stage 6 Quantities.

Rule requirements:
1. Word-boundary number matching (\b<num>\b).
2. Exclusion of:
   - Figure/Table references (e.g. 'Fig. 1', 'Figure 2', 'Table 3', 'Scheme 1')
   - Reference brackets (e.g. '[1]', '[1, 2]', '[12-15]')
   - Section numbers (e.g. 'Section 2', '2. Methods')
3. Requirement:
   - Unit string OR a name token (len >= 3) within 50 characters of the match.
4. Classification:
   - 'span': match falls within an evidence span of the card.
   - 'document': match is in document outside spans.
   - 'nowhere': no valid match found.
"""

import json
import re
from pathlib import Path

# Load corpus texts
corpus = {}
for cpath in ['/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl', '/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl']:
    with open(cpath) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            did = d.get('doc_id') or d.get('id')
            if did:
                corpus[did] = d.get('text') or d.get('body', '')

# Load cards to get evidence spans
cards_by_doc = {}
for cpath in ['/home/abhishek24024/flbds_data/pilot/silver_cards.jsonl', '/home/abhishek24024/flbds_data/audit6/silver_cards.jsonl']:
    with open(cpath) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            did = rec.get('doc_id')
            c = rec.get('card', rec)
            if did and did not in cards_by_doc:
                cards_by_doc[did] = c

# Load the 190 dropped quantities
with open('/home/abhishek24024/flbds_data/audit8/relinked_190_quantities.json') as f:
    r190 = json.load(f)

# Combine in_document and nowhere lists
all_190 = []
if 'in_document' in r190:
    all_190.extend(r190['in_document'])
if 'nowhere' in r190:
    all_190.extend(r190['nowhere'])
if not all_190 and isinstance(r190, list):
    all_190 = r190

print(f"Loaded {len(all_190)} quantities to audit.")

def normalize_unit(unit_str):
    if not unit_str:
        return []
    u = unit_str.strip()
    variants = [u]
    if u in ["°C", "degC", "° C", "deg C"]:
        variants.extend(["°C", "° C", "degC", "deg C", "degrees C", "Celsius", "C"])
    elif u in ["%", "percent"]:
        variants.extend(["%", "percent", "wt%"])
    elif "m2" in u or "m^2" in u:
        variants.extend(["m2", "m^2", "m²"])
    elif "m3" in u or "m^3" in u:
        variants.extend(["m3", "m^3", "m³"])
    elif u == "Pa":
        variants.extend(["Pa", "kPa", "MPa"])
    elif u == "W":
        variants.extend(["W", "kW", "mW"])
    return list(set(variants))

def is_citation_or_fig(text, start, end):
    # Context window 40 chars before and after
    pre = text[max(0, start - 40):start]
    post = text[end:min(len(text), end + 40)]
    
    # 1. Figure / Table / Scheme
    if re.search(r'(?i)\b(?:fig(?:ure)?\.?|table|scheme)\s*$', pre):
        return True, "figure_or_table_label"
    if re.search(r'(?i)^\s*(?:fig(?:ure)?\.?|table|scheme)', post):
        return True, "figure_or_table_label"
        
    # 2. Reference brackets: e.g. [1], [12], [1-3], [4, 5]
    # Check if immediately enclosed in square brackets
    b_pre = text[max(0, start - 5):start]
    b_post = text[end:min(len(text), end + 5)]
    if '[' in b_pre and ']' in b_post:
        # Check inside brackets
        bracket_content = text[text.rfind('[', 0, start):text.find(']', end) + 1]
        if re.match(r'\[\s*[\d,\s–-]+\s*\]', bracket_content):
            return True, "citation_bracket"
            
    # 3. Section number at start of line: e.g. "\n1. Introduction" or "\n2.3 "
    line_start = text.rfind('\n', 0, start)
    if line_start == -1:
        line_start = 0
    line_pre = text[line_start:start].strip()
    if line_pre == "" and re.match(r'^\s*[\.\)]\s+[A-Z]', post):
        return True, "section_header_number"
        
    return False, ""

def find_provenance(q, full_text, card_spans):
    val = q.get('value')
    if val is None:
        return 'nowhere', None, None, "null_value"
        
    # Generate number representation variants
    num_strs = []
    if isinstance(val, (int, float)):
        if float(val).is_integer():
            num_strs.append(str(int(val)))
            num_strs.append(f"{float(val):.1f}")
        else:
            num_strs.append(str(val))
            # also round to 2 and 3 decimals
            num_strs.append(f"{val:.2f}")
            num_strs.append(f"{val:.3f}")
    else:
        num_strs.append(str(val))
        
    num_strs = list(set(num_strs))
    
    name = str(q.get('name', ''))
    unit = str(q.get('unit', ''))
    name_tokens = [w.lower() for w in re.split(r'\W+', name) if len(w) >= 3 and w.lower() not in ["the", "and", "for", "with"]]
    unit_variants = normalize_unit(unit)
    
    # Search for valid occurrences
    valid_matches = []
    
    for n_str in sorted(num_strs, key=len, reverse=True):
        pattern = re.compile(r'(?<![\d\.-])' + re.escape(n_str) + r'(?![\d\.-])')
        for m in pattern.finditer(full_text):
            st, en = m.start(), m.end()
            
            # Check exclusions
            is_excl, excl_reason = is_citation_or_fig(full_text, st, en)
            if is_excl:
                continue
                
            # Check proximity requirement: within 50 chars pre or post
            prox_window = full_text[max(0, st - 50):min(len(full_text), en + 50)].lower()
            
            unit_found = any(u.lower() in prox_window for u in unit_variants) if unit_variants else False
            name_found = any(tok in prox_window for tok in name_tokens) if name_tokens else False
            
            if unit_found or name_found:
                valid_matches.append({
                    'start': st,
                    'end': en,
                    'snippet': full_text[max(0, st - 30):min(len(full_text), en + 30)].replace('\n', ' '),
                    'matched_num': n_str,
                    'unit_match': unit_found,
                    'name_match': name_found
                })
                
        if valid_matches:
            break
            
    if not valid_matches:
        return 'nowhere', None, None, "no_verified_proximity_match"
        
    # Check if any match falls within evidence spans
    for m in valid_matches:
        st, en = m['start'], m['end']
        for span in card_spans:
            if not span:
                continue
            span_st = full_text.find(span)
            if span_st != -1 and span_st <= st and en <= (span_st + len(span)):
                return 'span', m, span, "in_cited_evidence_span"
                
    # Otherwise, it's valid document provenance
    return 'document', valid_matches[0], None, "in_document_co_occurring"

provenance_results = []
span_cnt = 0
doc_cnt = 0
nowhere_cnt = 0

for q in all_190:
    did = q.get('doc_id')
    ftext = corpus.get(did, "")
    card = cards_by_doc.get(did, {})
    
    spans = []
    # Extract evidence spans from card
    ev_list = card.get('evidence', [])
    for ev in ev_list:
        if isinstance(ev, dict) and 'verbatim_quote' in ev:
            spans.append(ev['verbatim_quote'])
        elif isinstance(ev, str):
            spans.append(ev)
    if 'evidence_spans' in card:
        spans.extend(card['evidence_spans'])
        
    prov, match_info, matching_span, reason = find_provenance(q, ftext, spans)
    
    if prov == 'span':
        span_cnt += 1
    elif prov == 'document':
        doc_cnt += 1
    else:
        nowhere_cnt += 1
        
    provenance_results.append({
        'doc_id': did,
        'name': q.get('name'),
        'value': q.get('value'),
        'unit': q.get('unit'),
        'provenance': prov,
        'offset_start': match_info['start'] if match_info else None,
        'offset_end': match_info['end'] if match_info else None,
        'snippet': match_info['snippet'] if match_info else None,
        'reason': reason
    })

print(f"\n=======================================================")
print(f"AUDIT ROUND 9 PROVENANCE RULE RESULTS (N={len(all_190)})")
print(f"  Span Provenance:     {span_cnt:3d} ({span_cnt/len(all_190)*100:.1f}%)")
print(f"  Document Provenance: {doc_cnt:3d} ({doc_cnt/len(all_190)*100:.1f}%)")
print(f"  Nowhere (Purged):    {nowhere_cnt:3d} ({nowhere_cnt/len(all_190)*100:.1f}%)")

out_file = Path('/home/abhishek24024/flbds_data/audit9/relinked_190_provenance_rule.json')
with open(out_file, 'w') as f:
    json.dump({
        'total': len(all_190),
        'span_count': span_cnt,
        'document_count': doc_cnt,
        'nowhere_count': nowhere_cnt,
        'results': provenance_results
    }, f, indent=2)
print(f"Saved results to {out_file}")

# Seed 72 random sample of 20 quantities for human-style verification
import random
random.seed(72)
sample_20 = random.sample(provenance_results, 20)

sample_file = Path('/home/abhishek24024/flbds_data/audit9/sample20_seed72_provenance.json')
with open(sample_file, 'w') as f:
    json.dump(sample_20, f, indent=2)
print(f"Saved Seed 72 sample (N=20) to {sample_file}")
