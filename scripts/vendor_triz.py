#!/usr/bin/env python3
"""Vendor the canonical TRIZ corpus into JSON.

Source: the MATRIZ TRIZ Knowledge Base (https://wiki.matriz.org), CC-BY with
attribution, as distributed by the MIT-licensed `pytriz` package
(https://github.com/mmysior/pytriz). We re-normalise the ragged 39x39 CSV into
an explicit integer matrix and attach a synonym list per parameter so the
lexical matcher works without an embedding model.

Usage:  python scripts/vendor_triz.py [--wheel path/to/pytriz.whl]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "flbds" / "data" / "triz"

KEYWORDS: dict[int, list[str]] = {
    1: ["weight", "mass", "heavy", "light", "payload", "inertia of moving"],
    2: ["stationary weight", "dead load", "static mass", "foundation load"],
    3: ["length", "span", "stroke", "reach", "moving length"],
    4: ["stationary length", "width", "height", "envelope", "footprint"],
    5: ["area", "surface", "contact area", "moving area"],
    6: ["stationary area", "floor area", "plate area"],
    7: ["volume", "capacity", "displacement", "moving volume"],
    8: ["stationary volume", "enclosure volume", "tank volume"],
    9: ["speed", "velocity", "rapidity", "throughput rate"],
    10: ["force", "load", "thrust", "tension", "compression"],
    11: ["stress", "pressure", "stress concentration", "bending stress"],
    12: ["shape", "geometry", "form", "profile", "topology"],
    13: ["stability", "composition stability", "buckling", "overturning"],
    14: ["strength", "yield", "ultimate strength", "fracture"],
    15: ["durability moving", "wear", "fatigue life", "service life"],
    16: ["durability stationary", "creep", "corrosion life"],
    17: ["temperature", "heat", "thermal", "cooling", "heating"],
    18: ["illumination", "light", "brightness", "optical"],
    19: ["energy use moving", "power draw moving", "energy consumption"],
    20: ["energy use stationary", "standby power", "idle energy"],
    21: ["power", "wattage", "power density", "actuation power"],
    22: ["energy loss", "dissipation", "efficiency loss", "heat loss"],
    23: ["substance loss", "material loss", "leakage", "waste"],
    24: ["information loss", "data loss", "signal loss"],
    25: ["time loss", "delay", "latency", "cycle time"],
    26: ["quantity of substance", "amount of material", "mass of material"],
    27: ["reliability", "failure rate", "robustness", "mtbf"],
    28: ["measurement accuracy", "precision", "tolerance", "error"],
    29: ["manufacturing precision", "machining tolerance", "process capability"],
    30: ["harmful external factor", "environmental attack", "corrosion", "contamination"],
    31: ["harmful generated factor", "vibration", "noise", "emissions", "heat rejection"],
    32: ["ease of manufacture", "manufacturability", "assembly", "cost to make"],
    33: ["ease of operation", "usability", "ergonomics", "operability"],
    34: ["ease of repair", "maintainability", "serviceability"],
    35: ["adaptability", "versatility", "flexibility", "reconfigurability"],
    36: ["complexity", "part count", "device complexity", "control complexity"],
    37: ["difficulty of detection", "difficulty of measurement", "sensing"],
    38: ["automation", "autonomy", "extent of automation"],
    39: ["productivity", "throughput", "yield rate", "output rate"],
}


def fetch_wheel(dest: Path) -> Path:
    subprocess.run(
        [sys.executable, "-m", "pip", "download", "pytriz", "--no-deps", "-q", "-d", str(dest)],
        check=True,
    )
    wheels = sorted(dest.glob("pytriz-*.whl"))
    if not wheels:
        raise SystemExit("could not download pytriz wheel")
    return wheels[-1]


def extract(wheel: Path, dest: Path) -> Path:
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(dest)
    return dest / "pytriz" / "resources"


def parse_matrix(csv_path: Path) -> list[list[list[int]]]:
    with csv_path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh, delimiter=";"))
    if len(rows) != 39 or any(len(r) != 39 for r in rows):
        raise SystemExit(f"unexpected matrix shape: {len(rows)}x{set(len(r) for r in rows)}")
    matrix: list[list[list[int]]] = []
    for row in rows:
        out_row: list[list[int]] = []
        for cell in row:
            ids = sorted({int(t) for t in re.findall(r"\d+", cell) if 1 <= int(t) <= 40})
            out_row.append(ids)
        matrix.append(out_row)
    return matrix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wheel", type=Path, default=None)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        wheel = args.wheel or fetch_wheel(tmp)
        res = extract(wheel, tmp / "x")

        params_raw = json.loads((res / "parameters.json").read_text(encoding="utf-8"))["parameters"]
        principles_raw = json.loads((res / "principles.json").read_text(encoding="utf-8"))["principles"]
        separations_raw = json.loads((res / "separations.json").read_text(encoding="utf-8"))["separations"]
        matrix = parse_matrix(res / "matrix_values.csv")

    parameters = [
        {
            "id": int(p["id"]),
            "name": str(p["name"]).strip(),
            "description": " ".join(str(p.get("description", "")).split()),
            "keywords": KEYWORDS.get(int(p["id"]), []),
        }
        for p in params_raw
    ]
    principles = [
        {
            "id": int(p["id"]),
            "name": str(p["name"]).strip(),
            "description": " ".join(str(p.get("description", "")).split()),
            "rules": [str(r).strip() for r in p.get("rules", [])],
        }
        for p in principles_raw
    ]
    separations = [
        {
            "id": int(s["id"]),
            "name": str(s["name"]).strip(),
            "description": " ".join(str(s.get("description", "")).split()),
            "guidelines": [str(g_.strip()) for g_ in s.get("guidelines", [])],
            "principle_ids": [int(i) for i in s.get("principle_ids", [])],
        }
        for s in separations_raw
    ]

    parameters.sort(key=lambda p: p["id"])
    principles.sort(key=lambda p: p["id"])
    separations.sort(key=lambda s: s["id"])
    if len(parameters) != 39 or len(principles) != 40:
        raise SystemExit(f"unexpected corpus size: {len(parameters)} params, {len(principles)} principles")

    (OUT / "parameters.json").write_text(json.dumps(parameters, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "principles.json").write_text(json.dumps(principles, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "separations.json").write_text(json.dumps(separations, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "matrix.json").write_text(json.dumps(matrix, separators=(",", ":")) + "\n", encoding="utf-8")
    (OUT / "ATTRIBUTION.md").write_text(
        "# TRIZ reference data\n\n"
        "Parameters, principles, separation operators and the 39x39 contradiction\n"
        "matrix are derived from the **MATRIZ TRIZ Knowledge Base**\n"
        "(https://wiki.matriz.org), distributed under a Creative Commons licence that\n"
        "requires attribution. The transcription was obtained from the MIT-licensed\n"
        "`pytriz` package (https://github.com/mmysior/pytriz) and re-normalised into\n"
        "`matrix.json` (39 rows = improving parameter, 39 columns = worsening\n"
        "parameter, cells = inventive principle ids).\n\n"
        "Regenerate with `python scripts/vendor_triz.py`.\n",
        encoding="utf-8",
    )

    filled = sum(1 for row in matrix for cell in row if cell)
    print(f"parameters   : {len(parameters)}")
    print(f"principles   : {len(principles)}")
    print(f"separations  : {len(separations)}")
    print(f"matrix       : 39x39, {filled}/{39*39} cells populated")
    print(f"written to   : {OUT}")


if __name__ == "__main__":
    main()
