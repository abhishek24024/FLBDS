import urllib.request
import json
import os

out_dir = "/home/abhishek24024/flbds_data/api_responses"
os.makedirs(out_dir, exist_ok=True)

dois = {
    "martins_2018": "10.1038/s41467-018-06257-3",
    "shi_2015": "10.1126/science.aab3564",
    "flynn_bush_2008": "10.1017/s0022112008002048",
    "shirtcliffe_2006": "10.1063/1.2347266",
    "scholander_1955": "10.1152/jappl.1955.8.3.279"
}

headers = {"User-Agent": "FLBDS_Audit/1.0 (mailto:abhishek@example.com)"}

for name, doi in dois.items():
    print(f"=== Processing {name} ({doi}) ===")
    
    # 1. Crossref
    cr_url = f"https://api.crossref.org/works/{doi}"
    try:
        req = urllib.request.Request(cr_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            out_file = f"{out_dir}/{name}_crossref.json"
            with open(out_file, "wb") as f:
                f.write(data)
            parsed = json.loads(data.decode())["message"]
            has_abstract = "abstract" in parsed and bool(parsed["abstract"])
            title = parsed.get("title", [""])[0]
            print(f"  Crossref Title: {title}")
            print(f"  Crossref has abstract: {has_abstract}")
            if has_abstract:
                print(f"  Crossref abstract snippet: {parsed['abstract'][:100]}")
    except Exception as e:
        print(f"  Crossref failed: {e}")

    # 2. OpenAlex
    oa_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        req = urllib.request.Request(oa_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            out_file = f"{out_dir}/{name}_openalex.json"
            with open(out_file, "wb") as f:
                f.write(data)
            parsed = json.loads(data.decode())
            inv_idx = parsed.get("abstract_inverted_index")
            has_abstract = inv_idx is not None and len(inv_idx) > 0
            title = parsed.get("title", "")
            print(f"  OpenAlex Title: {title}")
            print(f"  OpenAlex has abstract: {has_abstract}")
    except Exception as e:
        print(f"  OpenAlex failed: {e}")

    # 3. Europe PMC
    epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&format=json"
    try:
        req = urllib.request.Request(epmc_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            out_file = f"{out_dir}/{name}_europepmc.json"
            with open(out_file, "wb") as f:
                f.write(data)
            res_list = json.loads(data.decode()).get("resultList", {}).get("result", [])
            if res_list:
                item = res_list[0]
                has_abstract = "abstractText" in item and bool(item["abstractText"])
                title = item.get("title", "")
                print(f"  Europe PMC Title: {title}")
                print(f"  Europe PMC has abstract: {has_abstract}")
                if has_abstract:
                    print(f"  Europe PMC abstract snippet: {item['abstractText'][:100]}")
            else:
                print("  Europe PMC: no results found")
    except Exception as e:
        print(f"  Europe PMC failed: {e}")
    print()
