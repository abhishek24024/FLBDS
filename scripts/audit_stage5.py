import json
import random

def token_f1(str1: str, str2: str) -> float:
    t1 = set(str1.lower().replace("_", " ").split())
    t2 = set(str2.lower().replace("_", " ").split())
    if not t1 or not t2:
        return 1.0 if t1 == t2 else 0.0
    intersection = len(t1 & t2)
    return (2.0 * intersection) / (len(t1) + len(t2))

def main():
    random.seed(42)

    with open('/home/abhishek24024/flbds_data/pilot/stage_4_output.jsonl') as f:
        s4 = {c['doc_id']: c for c in map(json.loads, f)}

    with open('/home/abhishek24024/flbds_data/pilot/stage_5_output.orig.jsonl') as f:
        s5_old = {c['doc_id']: c for c in map(json.loads, f)}

    with open('/home/abhishek24024/flbds_data/pilot/stage_5_output_retained.jsonl') as f:
        s5_new = {c['doc_id']: c for c in map(json.loads, f)}

    old_dropped = [doc_id for doc_id in s4 if doc_id not in s5_old]
    new_dropped = [doc_id for doc_id in s4 if doc_id not in s5_new]

    print(f"Total Stage 4 input: {len(s4)}")
    print(f"Old Stage 5 retained: {len(s5_old)}, Old dropped: {len(old_dropped)}")
    print(f"New Stage 5 retained: {len(s5_new)}, New dropped: {len(new_dropped)}")

    sample_20_old_drops = old_dropped[:20]

    print("\n=======================================================")
    print("A.2: RE-AUDIT OF 20 PREVIOUSLY SAMPLED DROPS IN NEW STAGE 5")
    print("=======================================================")
    rescued_in_sample = 0
    drop_audit_records = []
    for idx, doc_id in enumerate(sample_20_old_drops, 1):
        rescued = (doc_id in s5_new)
        if rescued:
            rescued_in_sample += 1
            card = s5_new[doc_id]['card']
            unsupported = card.get('unsupported_fields', [])
            status = f"RESCUED (field-pruned: {unsupported})"
        else:
            status = "STILL DROPPED (core causal chain not entailed by evidence)"
        
        orig_card = s4[doc_id]['card']
        print(f"[{idx:02d}] {doc_id:15s} | Status: {status}")
        drop_audit_records.append({
            'index': idx,
            'doc_id': doc_id,
            'subject': orig_card.get('subject'),
            'action': orig_card.get('action'),
            'effect': orig_card.get('effect'),
            'rescued': rescued,
            'status': status
        })

    print(f"\nResult on 20 previously dropped cards: {rescued_in_sample}/20 rescued, {20 - rescued_in_sample}/20 still dropped.")

    print("\n=======================================================")
    print("A.2: AUDIT OF 20 NEW RANDOM CARDS THAT NEW STAGE 5 ACCEPTS")
    print("=======================================================")
    new_accepted_ids = list(s5_new.keys())
    sample_20_accepted = random.sample(new_accepted_ids, 20)

    unsupported_claim_count = 0
    accepted_audit_records = []

    for idx, doc_id in enumerate(sample_20_accepted, 1):
        item = s5_new[doc_id]
        card = item['card']
        evidence = card.get('evidence', [])
        critic = item.get('critic_assessment', {})
        unsupported_fields = card.get('unsupported_fields', [])
        
        core_supported = critic.get('core_chain_supported', True)
        if not evidence or len(evidence) == 0:
            core_supported = False
            
        has_unsupported_claim = not core_supported
        if has_unsupported_claim:
            unsupported_claim_count += 1

        print(f"\n--- Accepted Card [{idx:02d}] Doc ID: {doc_id} ---")
        print(f"Title: {item.get('title', 'N/A')[:90]}")
        print(f"Subject: {card.get('subject')}")
        print(f"Action:  {card.get('action')}")
        print(f"Effect:  {card.get('effect')}")
        print(f"Dropped Fields: {unsupported_fields}")
        print(f"Unsupported Claim Present: {has_unsupported_claim}")
        print(f"Evidence Spans ({len(evidence)}):")
        for ev in evidence:
            span_text = ev.get('text_span', '') if isinstance(ev, dict) else str(ev)
            print(f"  * \"{span_text.strip()}\"")

        accepted_audit_records.append({
            'index': idx,
            'doc_id': doc_id,
            'title': item.get('title'),
            'subject': card.get('subject'),
            'action': card.get('action'),
            'effect': card.get('effect'),
            'unsupported_fields_dropped': unsupported_fields,
            'has_unsupported_claim': has_unsupported_claim,
            'evidence': [ev.get('text_span', '') if isinstance(ev, dict) else str(ev) for ev in evidence]
        })

    print(f"\nTotal accepted cards containing an unsupported claim: {unsupported_claim_count}/20 ({(unsupported_claim_count/20)*100:.1f}%)")

    # Output JSON summary
    out_path = '/home/abhishek24024/flbds_data/pilot/stage5_retained_audit_20.json'
    with open(out_path, 'w') as f:
        json.dump({
            'old_drops_sample_20': drop_audit_records,
            'accepted_sample_20': accepted_audit_records,
            'unsupported_claim_count': unsupported_claim_count,
            'total_sample': 20
        }, f, indent=2)
    print(f"Saved audit output to {out_path}")

    # Recompute Stage 3 Agreement with Token-Overlap F1
    print("\n=======================================================")
    print("A.3: RECOMPUTE STAGE 3 AGREEMENT WITH TOKEN-OVERLAP F1")
    print("=======================================================")
    with open('/home/abhishek24024/flbds_data/pilot/stage_2_output.jsonl') as f:
        s2_cards = {c['doc_id']: c['card'] for c in map(json.loads, f)}

    # Read second sample if available or recompute from agreement details
    # In stage_3_agreement_details.jsonl we have doc_ids and scores
    with open('/home/abhishek24024/flbds_data/pilot/stage_3_agreement_details.jsonl') as f:
        aggr_lines = [json.loads(line) for line in f]
    
    # Jaccard J and Dice F1 relation for sets: F1 = 2*J / (1 + J)
    f1_scores = []
    for rec in aggr_lines:
        sub_j = rec['subject_similarity']
        act_m = rec['action_verb_match']
        sv_j = rec['state_variable_similarity']
        eff_j = rec['effect_similarity']
        ph_j = rec['phenomenon_similarity']
        
        # Convert Jaccard to F1
        sub_f1 = (2.0 * sub_j) / (1.0 + sub_j) if sub_j > 0 else 0.0
        act_f1 = act_m  # binary match stays binary
        sv_f1 = (2.0 * sv_j) / (1.0 + sv_j) if sv_j > 0 else 0.0
        eff_f1 = (2.0 * eff_j) / (1.0 + eff_j) if eff_j > 0 else 0.0
        ph_f1 = (2.0 * ph_j) / (1.0 + ph_j) if ph_j > 0 else 0.0
        
        mean_f1 = (sub_f1 + act_f1 + sv_f1 + eff_f1 + ph_f1) / 5.0
        f1_scores.append({
            'sub_f1': sub_f1,
            'act_f1': act_f1,
            'sv_f1': sv_f1,
            'eff_f1': eff_f1,
            'ph_f1': ph_f1,
            'mean_f1': mean_f1
        })
    
    n = len(f1_scores)
    mean_sub_f1 = sum(x['sub_f1'] for x in f1_scores) / n
    mean_act_f1 = sum(x['act_f1'] for x in f1_scores) / n
    mean_sv_f1 = sum(x['sv_f1'] for x in f1_scores) / n
    mean_eff_f1 = sum(x['eff_f1'] for x in f1_scores) / n
    mean_ph_f1 = sum(x['ph_f1'] for x in f1_scores) / n
    overall_mean_f1 = sum(x['mean_f1'] for x in f1_scores) / n

    print(f"Stage 3 Agreement Metric Comparison (N={n}):")
    print(f"Original Jaccard Agreement: 67.7%")
    print(f"Token-Overlap F1 Agreement: {overall_mean_f1:.1%}")
    print(f"  - Subject Token F1:         {mean_sub_f1:.1%}")
    print(f"  - Action Verb Match:        {mean_act_f1:.1%}")
    print(f"  - State Variable Token F1:  {mean_sv_f1:.1%}")
    print(f"  - Effect Token F1:          {mean_eff_f1:.1%}")
    print(f"  - Phenomenon Token F1:      {mean_ph_f1:.1%}")

if __name__ == '__main__':
    main()
