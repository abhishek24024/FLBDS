#!/bin/bash
set -eo pipefail

ROOT_DIR="/home/abhishek24024/flbds"
cd "$ROOT_DIR"
export PATH="/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="/usr/local/cuda"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
mkdir -p /home/abhishek24024/flbds_data/audit6

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Audit 6 Stages 5, 6, 7 pipeline..."

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Running Stage 5 Critic ==="
/home/abhishek24024/flbds_env/bin/python3 /home/abhishek24024/flbds/flbds/pipeline/stage5_critic.py \
    --input /home/abhishek24024/flbds_data/pilot/stage_4_output.jsonl \
    --output /home/abhishek24024/flbds_data/audit6/stage_5_output.jsonl \
    --summary /home/abhishek24024/flbds_data/audit6/stage_5_summary.json

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Running Stage 6 Quantities ==="
/home/abhishek24024/flbds_env/bin/python3 /home/abhishek24024/flbds/flbds/pipeline/stage6_quantities.py \
    --input /home/abhishek24024/flbds_data/audit6/stage_5_output.jsonl \
    --output /home/abhishek24024/flbds_data/audit6/stage_6_output.jsonl \
    --summary /home/abhishek24024/flbds_data/audit6/stage_6_summary.json

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Running Stage 7 Dedup ==="
/home/abhishek24024/flbds_env/bin/python3 /home/abhishek24024/flbds/flbds/pipeline/stage7_dedup.py \
    --input /home/abhishek24024/flbds_data/audit6/stage_6_output.jsonl \
    --output /home/abhishek24024/flbds_data/audit6/silver_cards.jsonl \
    --summary /home/abhishek24024/flbds_data/audit6/stage_7_summary.json

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Audit 6 Pipeline Complete!"
