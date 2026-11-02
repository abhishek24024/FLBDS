import json
from pathlib import Path

# Load corpus on server
data_dir = Path("/home/abhishek24024/flbds_data")
records = {}
for fn in ["bio_pilot.jsonl", "eng_pilot.jsonl"]:
    fp = data_dir / "corpus" / fn
    if fp.exists():
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                doc_id = d.get("doc_id") or d.get("id") or d.get("pmcid") or d.get("patent_id")
                if doc_id:
                    records[doc_id] = d

with open("/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json") as f:
    d = json.load(f)

majors = [c for c in d["all_card_audits"] if c["verdict"] == "MAJOR"]

print(f"Total MAJOR cards: {len(majors)}")
for m in majors:
    doc_id = m["doc_id"]
    rec = records.get(doc_id, {})
    text = rec.get("text", "")
    title = rec.get("title", "")
    card_fields = m.get("card_fields", {})
    action = card_fields.get("action")
    effect = card_fields.get("effect")
    subject = card_fields.get("subject")
    scores = m.get("rubric_scores", {})
    issues = m.get("issues", [])
    print("=" * 60)
    print(f"Doc ID: {doc_id}")
    print(f"Title: {title[:120]}")
    print(f"Card Subject: {subject}")
    print(f"Card Action: {action}")
    print(f"Card Effect: {effect}")
    print(f"Old Verdict: {m.get('verdict')} (Usefulness: {scores.get('usefulness')})")
    print(f"Old Issues: {issues}")
    spans = card_fields.get("evidence_spans", [])
    for sp in spans:
        found = sp in text
        print(f"  Evidence span in text ({found}): {repr(sp[:80])}")
    print(f"Abstract: {rec.get('abstract', '')[:200]}")
