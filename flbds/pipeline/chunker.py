"""Document chunking and section extraction for biological papers and patents."""

import json
import re
from pathlib import Path
from typing import Iterator


def clean_bio_text(text: str, max_chars: int = 12000) -> str:
    """Extract substantive paper body (Abstract, Intro, Methods, Results, Discussion) and strip metadata/refs."""
    # Strip terminal references and bibliography
    ref_match = re.search(r'\n(References|REFERENCES|Literature Cited|LITERATURE CITED)\b', text)
    if ref_match:
        text = text[:ref_match.start()]
    
    # Locate substantive beginning past journal header metadata
    start_markers = ['License URL:', 'Keywords:', 'Abstract\n', 'ABSTRACT\n']
    start_idx = 0
    for marker in start_markers:
        pos = text.find(marker)
        if pos != -1:
            nl = text.find('\n', pos)
            if nl != -1:
                start_idx = max(start_idx, nl + 1)
    
    clean = text[start_idx:].strip()
    if len(clean) < 500:  # fallback if marker stripped too aggressively
        clean = text.strip()
    return clean[:max_chars]


def clean_eng_text(text: str, max_chars: int = 12000) -> str:
    """Extract patent description and abstract, capped at max_chars."""
    return text.strip()[:max_chars]


def chunk_document(doc: dict, max_chars: int = 12000) -> dict:
    """Preprocess a raw document record into a clean, size-constrained document record."""
    domain = doc.get("domain", "bio")
    raw_text = doc.get("text", "")
    if domain == "bio":
        cleaned_text = clean_bio_text(raw_text, max_chars=max_chars)
    else:
        cleaned_text = clean_eng_text(raw_text, max_chars=max_chars)
    
    return {
        "doc_id": doc["doc_id"],
        "domain": domain,
        "title": doc.get("title", ""),
        "citation": doc.get("citation", ""),
        "license": doc.get("license", "Unknown"),
        "text": cleaned_text,
        "raw_char_len": len(raw_text),
        "chunk_char_len": len(cleaned_text),
    }


def process_corpus(input_path: Path, output_path: Path, limit: int | None = None, max_chars: int = 12000) -> int:
    """Process an input JSONL corpus into a chunked JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(input_path) as fin, open(output_path, "w") as fout:
        for line in fin:
            if not line.strip():
                continue
            doc = json.loads(line)
            chunked = chunk_document(doc, max_chars=max_chars)
            fout.write(json.dumps(chunked) + "\n")
            count += 1
            if limit and count >= limit:
                break
    return count
