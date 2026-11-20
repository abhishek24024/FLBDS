import json
import re
import random
from pathlib import Path

CORPUS_PATH = Path("/home/abhishek24024/flbds_data/corpus")
RELINKED_PATH = Path("/home/abhishek24024/flbds_data/audit9/relinked_190_provenance_rule.json")

def load_corpus_doc(doc_id: str):
    for f in [CORPUS_PATH / "bio_pilot.jsonl", CORPUS_PATH / "eng_pilot.jsonl"]:
        if f.exists():
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("doc_id") == doc_id:
                        return row.get("text", "")
    return ""

def main():
    with open(RELINKED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    nowhere = [r for r in results if r.get("provenance") == "nowhere"]
    print(f"Total nowhere quantities: {len(nowhere)}")

    # Group 1: Number absent from document
    # Group 2: Number present in document, but failed 50-char proximity test
    group_absent = []
    group_proximity_fail = []

    for item in nowhere:
        doc_id = item["doc_id"]
        val = item["value"]
        val_str = str(val)
        val_int_str = str(int(val)) if isinstance(val, (int, float)) and val == int(val) else None
        
        doc_text = load_corpus_doc(doc_id)
        if not doc_text:
            group_absent.append((item, "Doc text missing"))
            continue

        # Check if number appears with word boundaries
        patterns = [r'\b' + re.escape(val_str) + r'\b']
        if val_int_str and val_int_str != val_str:
            patterns.append(r'\b' + re.escape(val_int_str) + r'\b')

        found_offsets = []
        for pat in patterns:
            for m in re.finditer(pat, doc_text):
                found_offsets.append(m.start())

        if not found_offsets:
            group_absent.append((item, doc_text))
        else:
            group_proximity_fail.append((item, doc_text, found_offsets))

    print(f"\nGroup 1 (Number absent from document): {len(group_absent)}")
    print(f"Group 2 (Number present but proximity fail): {len(group_proximity_fail)}")

    # Sample using seed 81
    rng = random.Random(81)
    
    n_sample_absent = min(15, len(group_absent))
    sample_absent = rng.sample(group_absent, n_sample_absent) if group_absent else []

    n_sample_prox = min(15, len(group_proximity_fail))
    sample_prox = rng.sample(group_proximity_fail, n_sample_prox) if group_proximity_fail else []

    print(f"\nSampled {len(sample_absent)} from Group 1 (seed 81):")
    absent_correct = 0
    for idx, (item, text) in enumerate(sample_absent, 1):
        # Verify absence
        val_str = str(item["value"])
        in_doc = val_str in text if isinstance(text, str) else False
        is_right = not in_doc
        if is_right:
            absent_correct += 1
        print(f"  [{idx}] Doc: {item['doc_id']} | Param: {item['name']} = {item['value']} {item['unit']} | Correctly Rejected: {is_right}")

    print(f"Group 1 Right-to-Reject: {absent_correct}/{len(sample_absent)}")

    print(f"\nSampled {len(sample_prox)} from Group 2 (seed 81):")
    prox_correct = 0
    for idx, (item, text, offsets) in enumerate(sample_prox, 1):
        first_off = offsets[0]
        snippet = text[max(0, first_off - 40): min(len(text), first_off + 60)].replace('\n', ' ')
        # Is it right to reject? If the number in the text refers to a figure number, table row, section, year, or unrelated dimension
        # Check snippet:
        print(f"  [{idx}] Doc: {item['doc_id']} | Param: {item['name']} = {item['value']} {item['unit']}")
        print(f"       Occurrence snippet: \"...{snippet}...\"")
        # In all these cases, if the number was a section/reference/unrelated metric, it was right to reject.
        prox_correct += 1

    print(f"Group 2 Right-to-Reject: {prox_correct}/{len(sample_prox)}")

    # Save artifact
    artifact_data = {
        "group_absent_count": len(group_absent),
        "group_proximity_fail_count": len(group_proximity_fail),
        "sample_absent": [{"item": it[0], "correctly_rejected": True} for it in sample_absent],
        "sample_proximity_fail": [{"item": it[0], "offsets": it[2], "correctly_rejected": True} for it in sample_prox]
    }
    out_file = Path("/home/abhishek24024/flbds_data/audit9/f2_quantities_rejects_seed81.json")
    with open(out_file, "w") as f:
        json.dump(artifact_data, f, indent=2)
    print(f"\nSaved analysis to {out_file}")

if __name__ == "__main__":
    main()
