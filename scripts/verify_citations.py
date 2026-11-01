#!/usr/bin/env python3
"""Search Crossref and verify papers."""

import urllib.request
import json
import re

def fetch_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    req = urllib.request.Request(url, headers={"User-Agent": "FLBDS_Audit/1.0 (mailto:abhishek@example.com)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            item = data["message"]
            title = item.get("title", ["No title"])[0]
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                authors.append(f"{given} {family}".strip())
            abstract = item.get("abstract", "")
            abstract_clean = re.sub(r'<[^>]+>', '', abstract).strip()
            return {
                "status": "FOUND",
                "url": url,
                "doi": doi,
                "title": title,
                "authors": ", ".join(authors),
                "container": item.get("container-title", [""])[0],
                "abstract": abstract_clean
            }
    except Exception as e:
        return {"status": "FAILED", "url": url, "error": str(e)}

def search_crossref(query):
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows=3"
    req = urllib.request.Request(url, headers={"User-Agent": "FLBDS_Audit/1.0 (mailto:abhishek@example.com)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            items = data["message"]["items"]
            results = []
            for it in items:
                title = it.get("title", ["No title"])[0]
                doi = it.get("DOI", "")
                authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])]
                abstract = re.sub(r'<[^>]+>', '', it.get("abstract", "")).strip()
                results.append({
                    "doi": doi,
                    "title": title,
                    "authors": ", ".join(authors),
                    "abstract": abstract,
                    "container": it.get("container-title", [""])[0]
                })
            return {"status": "FOUND", "url": url, "results": results}
    except Exception as e:
        return {"status": "FAILED", "url": url, "error": str(e)}

if __name__ == "__main__":
    queries = [
        "Wang elephant skin hydrogel ACS Applied Materials 2022",
        "Song Bhushan counter-current heat exchange rete mirabile 2010",
        "Zhai ant-inspired daytime passive radiative cooling Solar Energy Materials 2021",
        "Norman Nan Shi Keeping cool Enhanced optical reflection Saharan silver ants Science",
        "Flynn Bush Underwater breathing mechanics plastron respiration Journal of Fluid Mechanics",
        "Shirtcliffe Plastron properties of a superhydrophobic surface Applied Physics Letters"
    ]

    for q in queries:
        print("=== QUERY:", q)
        res = search_crossref(q)
        if res["status"] == "FOUND":
            for r in res["results"]:
                print("  DOI:", r['doi'])
                print("  Container:", r['container'])
                print("  Title:", r['title'])
                print("  Authors:", r['authors'][:80])
                print("  Abstract snippet:", r['abstract'][:150])
                print()
        else:
            print("  FAILED:", res.get("error"))
        print("-" * 50)
