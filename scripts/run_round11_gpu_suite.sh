#!/bin/bash
set -eo pipefail

ROOT_DIR="/home/abhishek24024/flbds"
cd "$ROOT_DIR"
export PATH="/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="/usr/local/cuda"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
mkdir -p /home/abhishek24024/flbds_data/audit11

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Round 11 Comprehensive Benchmark Suite (B0, Screen, Oracle, B3)..."
/usr/local/bin/gpurun -g 1 /home/abhishek24024/flbds_env/bin/python3 scripts/run_round11_benchmarks.py --benchmarks b0 b3 > /home/abhishek24024/flbds_data/audit11/gpu_suite.log 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] All Round 11 Benchmarks Completed Successfully!"
