import hashlib
import glob
from pathlib import Path

def get_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "docs" / "audit" / "freeze_hashes.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# FLBDS Dev Case & Evaluator Freeze Hashes (SHA-256)")
    lines.append("# Generated for Audit Round 10 Freeze\n")

    lines.append("## 1. Dev Case Benchmark Files (12 Cases x 3 Files = 36 Files)")
    dev_cases = sorted([d.name for d in (repo_root / "flbds" / "benchmark" / "dev").iterdir() if d.is_dir() and d.name.startswith("DEV-")])
    
    for case in dev_cases:
        lines.append(f"\n### {case}")
        for fname in ["problem_card.json", "ground_truth_eval.json", "reference_design.json"]:
            fpath = repo_root / "flbds" / "benchmark" / "dev" / case / fname
            if fpath.is_file():
                sha = get_sha256(str(fpath))
                lines.append(f"{sha}  flbds/benchmark/dev/{case}/{fname}")
            else:
                lines.append(f"MISSING: flbds/benchmark/dev/{case}/{fname}")

    lines.append("\n## 2. Physics & Evaluator Code Files")
    eval_files = [
        "flbds/physics/capacity_bound.py",
        "flbds/physics/tpl01_conduction.py",
        "flbds/physics/tpl02_pcm.py",
        "flbds/physics/tpl03_evaporation.py",
        "flbds/physics/tpl04_sorption.py",
        "flbds/physics/tpl05_wicking.py",
        "flbds/physics/tpl06_porous_flow.py",
        "flbds/physics/tpl07_fin.py",
        "flbds/physics/tpl08_countercurrent.py",
        "flbds/physics/tpl09_radiative.py",
        "flbds/physics/tpl10_diffusion.py",
        "flbds/schema/templates.py",
        "flbds/schema/problem_card.py",
        "flbds/schema/ground_truth_eval.py",
    ]

    for rel_path in eval_files:
        fpath = repo_root / rel_path
        if fpath.is_file():
            sha = get_sha256(str(fpath))
            lines.append(f"{sha}  {rel_path}")
        else:
            lines.append(f"MISSING: {rel_path}")

    full_text = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(full_text)

    print(full_text)
    print(f"\nSaved freeze hashes to {output_path}")

if __name__ == "__main__":
    main()
