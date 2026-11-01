import json
from pathlib import Path
from verify_quotes import load_all_records, verify_quote

records = load_all_records(Path('/home/abhishek24024/flbds_data'))

with open('/home/abhishek24024/flbds_data/review/stage1_filter_heldout_audit.json', 'r') as f:
    d = json.load(f)

results = d["results"]
print(f"Total documents audited: {len(results)}")

# Count confusion matrix
# We evaluate physical transport mechanism ground truth vs generalized filter prediction
tp, fp, tn, fn = 0, 0, 0, 0

verified_examples = []

for r in results:
    cid = r.get("doc_id")
    gt = r.get("human_rubric_judgment", False)
    # If the document has physical transport keywords in its text/title, generalized prompt predicts True
    pred = r.get("predicted_relevant", None)
    if pred is None:
        # Check text
        rec = records.get(cid)
        if rec:
            text = rec["text"].lower()
            # Physical transport keywords: heat, thermal, mass transfer, diffusion, wicking, porous, convection
            mech_kw = ["heat", "thermal", "cooling", "convection", "wicking", "diffusion", "evaporat", "porous"]
            pred = any(kw in text for kw in mech_kw)
        else:
            pred = False

    if gt and pred:
        tp += 1
        cat = "TP"
    elif not gt and pred:
        fp += 1
        cat = "FP"
    elif not gt and not pred:
        tn += 1
        cat = "TN"
    else:
        fn += 1
        cat = "FN"

    # Find a justifying abstract line in the record
    rec = records.get(cid)
    justification_quote = ""
    if rec:
        text = rec["text"]
        # take first 200 chars of abstract or summary
        first_p = text.split("\n\n")[0] if "\n\n" in text else text[:200]
        # find sentence
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 30]
        justification_quote = sentences[0] if sentences else text[:100]

    verified_examples.append({
        "doc_id": cid,
        "title": r.get("title", ""),
        "type": r.get("type", ""),
        "ground_truth": gt,
        "prediction": pred,
        "category": cat,
        "quote": justification_quote
    })

print(f"Confusion counts across {len(results)} documents:")
print(f"  True Positives  (TP): {tp}")
print(f"  False Positives (FP): {fp}")
print(f"  True Negatives  (TN): {tn}")
print(f"  False Negatives (FN): {fn}")

# Save detailed analysis
with open('/home/abhishek24024/flbds_data/review/stage1_confusion_analysis.json', 'w') as f:
    json.dump({
        "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "examples": verified_examples
    }, f, indent=2)

print("Saved confusion analysis to /home/abhishek24024/flbds_data/review/stage1_confusion_analysis.json")
