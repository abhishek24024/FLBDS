#!/bin/bash
set -eo pipefail

ROOT_DIR="/home/abhishek24024/flbds"
cd "$ROOT_DIR"
export PATH="/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="/usr/local/cuda"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
mkdir -p /home/abhishek24024/flbds_data/audit9

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Step 1: Stage 6 vLLM Seed Determinism (Item 6) ==="
/home/abhishek24024/flbds_env/bin/python3 scripts/test_stage6_determinism.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Step 2: B0 Re-run with Exposed Superheat Limits (Item 1) ==="
/home/abhishek24024/flbds_env/bin/python3 scripts/run_b0_exposed_rerun.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Step 3: A-NoOp 3-Turn Feedback Loop Benchmark (Item 10) ==="
/home/abhishek24024/flbds_env/bin/python3 scripts/run_a_noop_benchmark.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] All Audit 9 GPU jobs completed successfully!"
