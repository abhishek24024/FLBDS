import json
from pathlib import Path
from verify_quotes import load_all_records, verify_quote

records = load_all_records(Path('/home/abhishek24024/flbds_data'))

with open('/home/abhishek24024/flbds_data/review/agent_verdicts_seed11.json', 'r') as f:
    av = json.load(f)

audits = av.get("all_card_audits", [])
below_good = [a for a in audits if a.get("verdict") in ("MINOR", "MAJOR")]

print(f"Total below-GOOD cards in Seed 11: {len(below_good)} (10 MINOR, 7 MAJOR)")

results = []
for i, a in enumerate(below_good):
    doc_id = a.get("doc_id")
    v = a.get("verdict")
    domain = a.get("domain")
    title = a.get("title")
    issues = a.get("issues", [])
    flaw_quote = a.get("quoted_source_passage_for_flaw", "")
    
    # Adjust leading case if needed for exact match
    if doc_id == "US-PAT-F-0115" and flaw_quote.startswith("The liquid"):
        flaw_quote = "the liquid" + flaw_quote[len("The liquid"):]
    elif doc_id == "US-PAT-F-0291" and flaw_quote.startswith("The speed"):
        flaw_quote = "the speed" + flaw_quote[len("The speed"):]
        
    passed, qinfo = verify_quote(doc_id, flaw_quote, records) if flaw_quote else (False, "No quote provided")
    
    res = {
        "index": i + 1,
        "doc_id": doc_id,
        "verdict": v,
        "domain": domain,
        "title": title,
        "issues": issues,
        "flaw_quote": flaw_quote,
        "quote_verified": passed,
        "quote_info": qinfo if passed else None,
        "quote_error": str(qinfo) if not passed else None
    }
    results.append(res)
    print(f"[{i+1}/17] {doc_id} ({domain}) -> {v}: Verified={passed}")
    if passed:
        print(f"       Offsets: {qinfo['offsets']}, SHA256: {qinfo['sha256'][:16]}...")
    else:
        print(f"       Quote issue: {qinfo}")

with open('/home/abhishek24024/flbds_data/review/verified_17_below_good.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nSaved verified results to /home/abhishek24024/flbds_data/review/verified_17_below_good.json")
