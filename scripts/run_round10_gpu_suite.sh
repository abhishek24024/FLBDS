#!/bin/bash
set -eo pipefail

ROOT_DIR="/home/abhishek24024/flbds"
cd "$ROOT_DIR"
export PATH="/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="/usr/local/cuda"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
mkdir -p /home/abhishek24024/flbds_data/audit10

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Round 10 Benchmarks Suite..."
/usr/local/bin/gpurun -g 1 /home/abhishek24024/flbds_env/bin/python3 scripts/run_round10_benchmarks.py
echo "[$(date '+%Y-%m-%d %H:%M:%S')] All Round 10 Benchmarks Completed Successfully!"
