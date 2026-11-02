#!/usr/bin/env python3
"""scripts/harvest_related_work_phase0.py
Harvests related-work candidates across Crossref, OpenAlex, Europe PMC, and arXiv API.
Saves raw responses to flbds_data/audit6/related_work_raw/.
Builds table of up to 40 candidates:
  title, authors, year, venue, DOI or URL, abstract (verbatim), matched queries, status=UNREAD.
Zero summaries or relevance claims added.
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

QUERIES = [
    "bio-inspired design large language model",
    "biomimicry generative AI",
    "analogical design LLM",
    "SAPPhIRE",
    "BioTRIZ",
    "AutoTRIZ",
    "LLM engineering design physics verification",
    "retrieval augmented analogical reasoning design",
    "biological analogy transfer constraint mechanism"
]


def clean_slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", s.strip().lower())[:40]


def fetch_url(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FLBDS-Literature-Harvester/1.0 (mailto:abhishek24024@example.com)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def query_crossref(query: str, raw_dir: Path) -> list[dict]:
    slug = clean_slug(query)
    raw_path = raw_dir / f"crossref_{slug}.json"
    url = f"https://api.crossref.org/works?query={urllib.parse.quote_plus(query)}&rows=5"
    try:
        raw_bytes = fetch_url(url)
        raw_path.write_bytes(raw_bytes)
        data = json.loads(raw_bytes)
        items = data.get("message", {}).get("items", [])
        results = []
        for it in items:
            title = it.get("title", [""])[0] if it.get("title") else ""
            if not title:
                continue
            authors = []
            for a in it.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)
            year = ""
            issued = it.get("issued", {}).get("date-parts", [[]])[0]
            if issued:
                year = str(issued[0])
            venue = it.get("container-title", [""])[0] if it.get("container-title") else ""
            doi = it.get("DOI", "")
            url_link = f"https://doi.org/{doi}" if doi else it.get("URL", "")
            # Abstract
            abstract = it.get("abstract", "")
            if abstract:
                abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            results.append({
                "title": title.strip(),
                "authors": ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else ""),
                "year": year,
                "venue": venue.strip(),
                "doi_or_url": url_link,
                "abstract": abstract,
                "source_api": "Crossref",
                "matched_query": query
            })
        return results
    except Exception as e:
        print(f"  [Crossref Error] for '{query}': {e}", file=sys.stderr)
        return []


def query_openalex(query: str, raw_dir: Path) -> list[dict]:
    slug = clean_slug(query)
    raw_path = raw_dir / f"openalex_{slug}.json"
    url = f"https://api.openalex.org/works?search={urllib.parse.quote_plus(query)}&per-page=5"
    try:
        raw_bytes = fetch_url(url)
        raw_path.write_bytes(raw_bytes)
        data = json.loads(raw_bytes)
        items = data.get("results", [])
        results = []
        for it in items:
            title = it.get("title", "") or ""
            if not title:
                continue
            authors = []
            for auth in it.get("authorships", []):
                name = auth.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)
            year = str(it.get("publication_year", "")) if it.get("publication_year") else ""
            loc = it.get("primary_location", {}) or {}
            source = loc.get("source", {}) or {}
            venue = source.get("display_name", "") or ""
            doi = it.get("doi", "") or loc.get("landing_page_url", "")
            # Abstract inverted index reconstruction
            abstract = ""
            inv = it.get("abstract_inverted_index")
            if inv:
                word_positions = []
                for word, pos_list in inv.items():
                    for p in pos_list:
                        word_positions.append((p, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)
            results.append({
                "title": title.strip(),
                "authors": ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else ""),
                "year": year,
                "venue": venue.strip(),
                "doi_or_url": doi,
                "abstract": abstract.strip(),
                "source_api": "OpenAlex",
                "matched_query": query
            })
        return results
    except Exception as e:
        print(f"  [OpenAlex Error] for '{query}': {e}", file=sys.stderr)
        return []


def query_europe_pmc(query: str, raw_dir: Path) -> list[dict]:
    slug = clean_slug(query)
    raw_path = raw_dir / f"europepmc_{slug}.json"
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote_plus(query)}&format=json&pageSize=5"
    try:
        raw_bytes = fetch_url(url)
        raw_path.write_bytes(raw_bytes)
        data = json.loads(raw_bytes)
        items = data.get("resultList", {}).get("result", [])
        results = []
        for it in items:
            title = it.get("title", "") or ""
            if not title:
                continue
            author_str = it.get("authorString", "")
            year = str(it.get("pubYear", "")) if it.get("pubYear") else ""
            venue = it.get("journalTitle", "") or ""
            doi = it.get("doi", "")
            url_link = f"https://doi.org/{doi}" if doi else (f"https://europepmc.org/article/MED/{it.get('pmid')}" if it.get("pmid") else "")
            abstract = it.get("abstractText", "") or ""
            if abstract:
                abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            results.append({
                "title": title.strip(),
                "authors": author_str.strip(),
                "year": year,
                "venue": venue.strip(),
                "doi_or_url": url_link,
                "abstract": abstract.strip(),
                "source_api": "EuropePMC",
                "matched_query": query
            })
        return results
    except Exception as e:
        print(f"  [EuropePMC Error] for '{query}': {e}", file=sys.stderr)
        return []


def query_arxiv(query: str, raw_dir: Path) -> list[dict]:
    slug = clean_slug(query)
    raw_path = raw_dir / f"arxiv_{slug}.xml"
    clean_q = "+".join(urllib.parse.quote_plus(w) for w in query.split())
    url = f"http://export.arxiv.org/api/query?search_query=all:{clean_q}&start=0&max_results=5"
    try:
        raw_bytes = fetch_url(url)
        raw_path.write_bytes(raw_bytes)
        root = ET.fromstring(raw_bytes)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            title = title_el.text if title_el is not None else ""
            title = re.sub(r"\s+", " ", title).strip()
            if not title:
                continue
            authors = []
            for a in entry.findall("atom:author", ns):
                name_el = a.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())
            pub_el = entry.find("atom:published", ns)
            year = pub_el.text[:4] if pub_el is not None and pub_el.text else ""
            id_el = entry.find("atom:id", ns)
            url_link = id_el.text.strip() if id_el is not None and id_el.text else ""
            summary_el = entry.find("atom:summary", ns)
            abstract = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
            abstract = re.sub(r"\s+", " ", abstract).strip()
            results.append({
                "title": title,
                "authors": ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else ""),
                "year": year,
                "venue": "arXiv",
                "doi_or_url": url_link,
                "abstract": abstract,
                "source_api": "arXiv",
                "matched_query": query
            })
        return results
    except Exception as e:
        print(f"  [arXiv Error] for '{query}': {e}", file=sys.stderr)
        return []


def normalize_title(t: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", " ", t).strip().lower()


def main():
    base_dir = Path("/home/abhishek24024/flbds_data/audit6")
    if not base_dir.exists():
        base_dir = Path("flbds_data/audit6")
    raw_dir = base_dir / "related_work_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting Related-Work Harvest across 4 APIs for {len(QUERIES)} queries...")
    print(f"Raw responses destination: {raw_dir}")

    candidates_by_title = {}

    for q in QUERIES:
        print(f"\n--- Query: '{q}' ---")
        time.sleep(0.5)

        # 1. Crossref
        cr_items = query_crossref(q, raw_dir)
        print(f"  Crossref returned {len(cr_items)} items")

        # 2. OpenAlex
        oa_items = query_openalex(q, raw_dir)
        print(f"  OpenAlex returned {len(oa_items)} items")

        # 3. Europe PMC
        pmc_items = query_europe_pmc(q, raw_dir)
        print(f"  Europe PMC returned {len(pmc_items)} items")

        # 4. arXiv
        ar_items = query_arxiv(q, raw_dir)
        print(f"  arXiv returned {len(ar_items)} items")

        for item in (cr_items + oa_items + pmc_items + ar_items):
            key = normalize_title(item["title"])
            if not key or len(key) < 8:
                continue
            if key not in candidates_by_title:
                candidates_by_title[key] = {
                    "title": item["title"],
                    "authors": item["authors"],
                    "year": item["year"],
                    "venue": item["venue"],
                    "doi_or_url": item["doi_or_url"],
                    "abstract": item["abstract"],
                    "matched_queries": [q],
                    "status": "UNREAD"
                }
            else:
                if q not in candidates_by_title[key]["matched_queries"]:
                    candidates_by_title[key]["matched_queries"].append(q)
                if not candidates_by_title[key]["abstract"] and item["abstract"]:
                    candidates_by_title[key]["abstract"] = item["abstract"]
                if not candidates_by_title[key]["doi_or_url"] and item["doi_or_url"]:
                    candidates_by_title[key]["doi_or_url"] = item["doi_or_url"]

    all_candidates = list(candidates_by_title.values())
    print(f"\nTotal unique candidates harvested: {len(all_candidates)}")

    # Sort candidates by number of matched queries (descending), then year (descending)
    all_candidates.sort(key=lambda x: (len(x["matched_queries"]), x["year"]), reverse=True)

    # Cap at 40
    selected_40 = all_candidates[:40]
    print(f"Selected top {len(selected_40)} candidates for literature gate.")

    # Save JSON
    out_json = base_dir / "related_work_candidates.json"
    out_json.write_text(json.dumps(selected_40, indent=2))
    print(f"Saved candidate list to {out_json}")

    # Write Markdown table
    md_lines = [
        "# Phase 0 Literature Gate: Related-Work Candidates",
        "",
        "**Harvest Date**: 2026-11-01  ",
        f"**Candidate Count**: {len(selected_40)}  ",
        "**Note**: Per standing instructions, all entries are marked UNREAD with zero summaries, interpretations, or relevance claims. Verbatim abstracts are included only when returned by the respective API.",
        "",
        "| # | Title | Authors | Year | Venue | DOI / URL | Matched Queries | Status |",
        "|---|---|---|---|---|---|---|---|"
    ]

    for idx, c in enumerate(selected_40, 1):
        q_str = "; ".join(c["matched_queries"])
        # Escape markdown pipes
        t_clean = c["title"].replace("|", "\\|")
        a_clean = c["authors"].replace("|", "\\|")
        v_clean = c["venue"].replace("|", "\\|")
        link = f"[{c['doi_or_url']}]({c['doi_or_url']})" if c["doi_or_url"] else "N/A"
        md_lines.append(f"| {idx} | {t_clean} | {a_clean} | {c['year']} | {v_clean} | {link} | {q_str} | **{c['status']}** |")

    # Abstract appendix (verbatim)
    md_lines.append("")
    md_lines.append("## Verbatim Abstracts (Unread)")
    md_lines.append("")
    for idx, c in enumerate(selected_40, 1):
        md_lines.append(f"### {idx}. {c['title']} ({c['year']})")
        md_lines.append(f"- **Authors**: {c['authors']}")
        md_lines.append(f"- **Link**: {c['doi_or_url']}")
        md_lines.append(f"- **Matched Queries**: {'; '.join(c['matched_queries'])}")
        md_lines.append(f"- **Status**: `{c['status']}`")
        if c["abstract"]:
            md_lines.append(f"- **Verbatim Abstract**:\n> {c['abstract']}\n")
        else:
            md_lines.append("- **Verbatim Abstract**: *(None returned by API)*\n")

    out_md = Path("docs/audit/related_work_candidates.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines))
    print(f"Saved Markdown table to {out_md}")


if __name__ == "__main__":
    main()
