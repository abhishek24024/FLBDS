#!/usr/bin/env python3
"""Fetch one CC/PD-licensed photo per organism in flbds/v11/data/organisms.json from Wikimedia Commons.
Writes images to <out>/<id>.jpg and a manifest with source URL, author and licence for attribution."""
import json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "flbds/v11/data/images"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "FLBDS-research-image-fetcher/0.1 (academic research; python urllib)"}
API = "https://commons.wikimedia.org/w/api.php"
OK = ("cc0", "cc by", "cc-by", "public domain", "pd")

def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(10 * (attempt + 1))
    return {}

cases = json.loads((ROOT / "flbds/v11/data/organisms.json").read_text())["cases"]
mf = OUT / "images_manifest.json"
manifest = json.loads(mf.read_text()) if mf.exists() else {}
for c in cases:
    if c["id"] in manifest and (OUT / manifest[c["id"]]["file"]).exists():
        continue
    q = c["commons_query"]
    d = get({"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {q}",
             "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
             "iiurlwidth": 960})
    pages = sorted((d.get("query", {}).get("pages", {}) or {}).values(), key=lambda p: p.get("index", 99))
    pick = None
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName", {}).get("value") or "").lower()
        if ii.get("mime") in ("image/jpeg", "image/png") and any(k in lic for k in OK):
            pick = (p, ii, md, lic); break
    if not pick:
        print(c["id"], "NO LICENSED IMAGE for", q); continue
    p, ii, md, lic = pick
    dst = OUT / f"{c['id']}.jpg"
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60) as r:
                dst.write_bytes(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(5 * (attempt + 1))
    else:
        print(c["id"], "rate-limited, skipped"); continue
    manifest[c["id"]] = {"file": dst.name, "commons_title": p["title"], "page": ii.get("descriptionurl"),
                         "license": md.get("LicenseShortName", {}).get("value"),
                         "artist": md.get("Artist", {}).get("value", "")[:200], "query": q}
    print(c["id"], c["common"], "->", p["title"], "|", manifest[c["id"]]["license"], flush=True)
    mf.write_text(json.dumps(manifest, indent=1))
    time.sleep(3)
(OUT / "images_manifest.json").write_text(json.dumps(manifest, indent=1))
