#!/usr/bin/env python3
"""Download model weights from Hugging Face snapshot to /home/abhishek24024/flbds_data/models/."""

import argparse
import sys
import yaml
from pathlib import Path
from huggingface_hub import snapshot_download


def main():
    parser = argparse.ArgumentParser(description="Download model weights.")
    parser.add_argument("--role", choices=["filter", "critic", "teacher"], required=True, help="Model role from configs/models.yaml")
    parser.add_argument("--config", default="configs/models.yaml", help="Path to config file")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)[args.role]

    repo_id = cfg["repo_id"]
    local_dir = Path(cfg["local_dir"])
    local_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting download for {args.role}: '{repo_id}' -> '{local_dir}'...", flush=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        max_workers=8,
        resume_download=True,
    )
    print(f"Successfully downloaded {args.role} to {local_dir}!", flush=True)


if __name__ == "__main__":
    main()
