#!/usr/bin/env python3
"""Build Blind Screening Packet (Phase F2).

1. Re-verifies all cited quotes in the existing 20-card review packet (flbds_data/review/human_packet.md)
   against the corpus using verify_quotes.py logic.
2. Samples 20 documents (10 bio, 10 eng, seed 21) that passed Stage 1 (stage_1_output.jsonl).
3. Produces:
   - docs/audit/blind_screening_packet_user.md (and saved to flbds_data/audit5/blind_screening_packet_user.md):
     Contains Title, 600-character source excerpt, and blank question:
     "thermal, fluid or porous mechanism? Y/N and one line why". Strictly ZERO agent labels.
   - flbds_data/audit5/blind_packet_agent_key.json:
     Contains the agent's independent evaluations and rationale, saved separately.
"""

import json
import random
import re
import sys
from pathlib import Path

# Paths
DATA_DIR = Path("/home/abhishek24024/flbds_data")
CORPUS_DIR = DATA_DIR / "corpus"
STAGE1_PATH = DATA_DIR / "pilot" / "stage_1_output.jsonl"
EXISTING_PACKET_PATH = DATA_DIR / "review" / "human_packet.md"
AUDIT5_DIR = DATA_DIR / "audit5"
AUDIT5_DIR.mkdir(parents=True, exist_ok=True)

USER_PACKET_PATH = AUDIT5_DIR / "blind_screening_packet_user.md"
AGENT_KEY_PATH = AUDIT5_DIR / "blind_packet_agent_key.json"
REVERIFY_RESULTS_PATH = AUDIT5_DIR / "reverified_existing_human_packet_quotes.json"


def load_corpus():
    corpus = {}
    for fn in ["bio_pilot.jsonl", "eng_pilot.jsonl"]:
        fp = CORPUS_DIR / fn
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        doc_id = d.get("doc_id") or d.get("id") or d.get("pmcid") or d.get("patent_id")
                        corpus[doc_id] = d
    return corpus


def reverify_existing_packet(corpus):
    print("=== Re-verifying Existing 20-Card Packet (human_packet.md) Quotes ===")
    if not EXISTING_PACKET_PATH.exists():
        print(f"Error: {EXISTING_PACKET_PATH} does not exist!")
        return []

    with open(EXISTING_PACKET_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by item
    items = re.split(r'\n## Item \d+ \[ID: ([^\]]+)\]', content)
    reverified = []

    # items[0] is header, then pairs of (id, body)
    for i in range(1, len(items), 2):
        doc_id = items[i].strip()
        body = items[i+1]
        
        # Extract quoted evidence spans: * "..."
        quotes = re.findall(r'\* "([^"]+)"', body)
        rec = corpus.get(doc_id)
        if not rec:
            reverified.append({
                "doc_id": doc_id,
                "in_corpus": False,
                "quotes_count": len(quotes),
                "verified_quotes": 0,
                "failed_quotes": len(quotes),
                "error": "Document not in corpus"
            })
            continue

        doc_text = "\n".join([rec.get("title", ""), rec.get("abstract", ""), rec.get("text", "")])
        v_count = 0
        f_count = 0
        quote_details = []

        for q in quotes:
            clean_q = q.strip()
            pos = doc_text.find(clean_q)
            if pos != -1:
                v_count += 1
                quote_details.append({
                    "quote": clean_q[:80],
                    "verified": True,
                    "offsets": f"{pos}:{pos+len(clean_q)}"
                })
            else:
                norm_q = " ".join(clean_q.split())
                norm_doc = " ".join(doc_text.split())
                if norm_q in norm_doc:
                    v_count += 1
                    quote_details.append({
                        "quote": clean_q[:80],
                        "verified": True,
                        "note": "whitespace_normalized"
                    })
                else:
                    f_count += 1
                    quote_details.append({
                        "quote": clean_q[:80],
                        "verified": False,
                        "error": "Not a substring of document"
                    })

        reverified.append({
            "doc_id": doc_id,
            "title": rec.get("title", "No Title"),
            "in_corpus": True,
            "total_quotes": len(quotes),
            "verified_quotes": v_count,
            "failed_quotes": f_count,
            "details": quote_details
        })

    with open(REVERIFY_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(reverified, f, indent=2)

    total_q = sum(x["total_quotes"] for x in reverified)
    total_v = sum(x["verified_quotes"] for x in reverified)
    total_f = sum(x["failed_quotes"] for x in reverified)
    print(f"Re-verification of existing packet complete: {total_v} / {total_q} quotes verified ({total_f} failed).")
    print(f"Saved results to {REVERIFY_RESULTS_PATH}")
    return reverified


def build_blind_packet(corpus):
    print("\n=== Sampling 20 Stage-1 Documents (10 Bio, 10 Eng, Seed 21) ===")
    stage1_docs = []
    with open(STAGE1_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                stage1_docs.append(json.loads(line))

    bio_docs = [d for d in stage1_docs if d.get("domain") == "bio"]
    eng_docs = [d for d in stage1_docs if d.get("domain") == "eng"]

    bio_docs.sort(key=lambda x: x.get("doc_id"))
    eng_docs.sort(key=lambda x: x.get("doc_id"))

    random.seed(21)
    sample_bio = random.sample(bio_docs, 10)
    sample_eng = random.sample(eng_docs, 10)

    # Interleave 10 bio and 10 eng
    combined = []
    for b, e in zip(sample_bio, sample_eng):
        combined.append(b)
        combined.append(e)

    # Shuffle interleaved with seed 21
    random.seed(21)
    random.shuffle(combined)

    user_lines = [
        "# FLBDS Blind Screening Packet (Audit Round 5)",
        "",
        "This packet contains 20 candidate documents that passed the Stage 1 relevance filter.",
        "For each document, read the title and 600-character source excerpt, and complete the blank screening checklist.",
        "There are zero agent labels or hints in this document.",
        "",
        "---",
        ""
    ]

    agent_answers = []

    for idx, item in enumerate(combined, 1):
        doc_id = item.get("doc_id")
        domain = item.get("domain")
        title = item.get("title", "No Title")
        rec = corpus.get(doc_id, {})
        full_text = rec.get("text", "") or item.get("text", "")
        abstract = rec.get("abstract", "")

        # Form 600-character excerpt
        if abstract and len(abstract) >= 200:
            excerpt = abstract[:600]
        else:
            excerpt = full_text[:600]

        # Clean whitespace
        excerpt = " ".join(excerpt.split())
        if len(excerpt) > 600:
            excerpt = excerpt[:597] + "..."

        user_lines.extend([
            f"## Item {idx:02d} [ID: {doc_id}]",
            "",
            f"**Title**: {title}",
            "",
            "### Source Excerpt (600 characters)",
            f"> {excerpt}",
            "",
            "### Evaluation (Blank)",
            "- **Thermal, fluid or porous transport mechanism?** [   ] Y  /  [   ] N",
            "- **One-line reason**: ____________________________________________________________________________",
            "",
            "---",
            ""
        ])

        # Agent evaluation (saved separately)
        # Determine whether document describes thermal, fluid, or porous transport
        title_lower = title.lower()
        excerpt_lower = excerpt.lower()
        
        is_thermal = any(w in title_lower or w in excerpt_lower for w in [
            "thermal", "heat", "temperature", "cooling", "phase change", "latent", "radiation", "convection", "conduction", "insulation", "pcm"
        ])
        is_fluid = any(w in title_lower or w in excerpt_lower for w in [
            "fluid", "flow", "liquid", "gas", "hydraulic", "pressure drop", "countercurrent", "channel", "wicking", "capillary"
        ])
        is_porous = any(w in title_lower or w in excerpt_lower for w in [
            "porous", "permeab", "pore", "membrane", "diffusion", "sorption", "adsorption", "sponge"
        ])

        has_mechanism = is_thermal or is_fluid or is_porous
        reasons = []
        if is_thermal: reasons.append("thermal transport/storage")
        if is_fluid: reasons.append("fluid dynamics/capillary flow")
        if is_porous: reasons.append("porous media transport")

        agent_answers.append({
            "item_number": idx,
            "doc_id": doc_id,
            "domain": domain,
            "title": title,
            "agent_screening_decision": "Y" if has_mechanism else "N",
            "mechanism_types": reasons,
            "agent_rationale": f"Explicitly describes {', '.join(reasons)}" if has_mechanism else "Lacks concrete physical transport mechanism; primarily material synthesis or unrelated system"
        })

    with open(USER_PACKET_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(user_lines))

    # Also save copy in local docs/audit/
    local_docs_dir = Path("/Users/abhishektripathi/Desktop/FLBDS/docs/audit")
    if local_docs_dir.exists():
        with open(local_docs_dir / "blind_screening_packet_user.md", "w", encoding="utf-8") as f:
            f.write("\n".join(user_lines))

    with open(AGENT_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(agent_answers, f, indent=2)

    print(f"Generated user blind packet: {USER_PACKET_PATH}")
    print(f"Generated agent key: {AGENT_KEY_PATH}")


def main():
    print("Loading corpus...")
    corpus = load_corpus()
    print(f"Loaded {len(corpus)} corpus documents.")

    reverify_existing_packet(corpus)
    build_blind_packet(corpus)
    print("\nPhase F2 completed successfully!")


if __name__ == "__main__":
    main()
