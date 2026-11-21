import json
import glob

files = glob.glob("/home/abhishek24024/flbds_data/**/silver_cards.jsonl", recursive=True)
print("Found files:", files)
target_file = None
for f in files:
    if "audit6" in f or "clean" in f or "pilot" in f:
        target_file = f
        break
if not target_file and files:
    target_file = files[0]

print("Using target file:", target_file)
if target_file:
    with open(target_file) as f:
        cards = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(cards)} cards from {target_file}")
    
    # Check clusters:
    # DEV-M1: African elephant (Loxodonta africana)
    # DEV-M2: Bluefin tuna / Rete mirabile (Thunnus thynnus)
    # DEV-M3: Saharan silver ant (Cataglyphis bombycina) / Namib beetle (Stenocara gracilipes)
    # DEV-M4: Insect respiration / spiracles / tracheae
    
    terms = {
        "DEV-M1": ["elephant", "loxodonta", "martins"],
        "DEV-M2": ["tuna", "thunnus", "rete", "mirabile", "countercurrent"],
        "DEV-M3": ["cataglyphis", "silver ant", "stenocara", "namib", "beetle"],
        "DEV-M4": ["spiracle", "trachea", "bosanquet", "stomata", "respiration"]
    }
    
    matches = {c: [] for c in terms}
    for item in cards:
        card = item.get("card", {})
        doc_id = item.get("doc_id", "")
        subj = card.get("subject", {})
        org = subj.get("organism", "") if isinstance(subj, dict) else str(subj)
        title = item.get("title", "")
        combined = f"{org} {title} {doc_id} {json.dumps(card)}".lower()
        
        for cluster, tlist in terms.items():
            for t in tlist:
                if t in combined:
                    matches[cluster].append({
                        "doc_id": doc_id,
                        "organism": org,
                        "title": title[:70],
                        "matched_term": t,
                        "card": card
                    })
                    break

    for cluster, mlist in matches.items():
        print(f"\n=== Cluster {cluster} (Matches: {len(mlist)}) ===")
        if not mlist:
            print("  STATUS: MISSING (No real silver card in pilot corpus)")
        else:
            for m in mlist[:3]:
                print(f"  Match: doc_id={m['doc_id']} org={m['organism']} title={m['title']}")
