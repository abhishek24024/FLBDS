#!/bin/bash
set -eo pipefail

MODE="${1:---smoke}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PATH="/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME="/usr/local/cuda"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

if [ "$MODE" = "--full" ]; then
    OUT_DIR="/home/abhishek24024/flbds_data/pilot"
    LIMIT_ARG=""
    AGREE_SAMPLE=300
    echo "=========================================================="
    echo "  RUNNING FULL PILOT RUN (500 BIO + 500 ENG)"
    echo "=========================================================="
elif [ "$MODE" = "--smoke" ]; then
    OUT_DIR="/home/abhishek24024/flbds_data/pilot_smoke"
    LIMIT_ARG="--limit-per-domain 20"
    AGREE_SAMPLE=20
    echo "=========================================================="
    echo "  RUNNING SMOKE TEST (20 BIO + 20 ENG)"
    echo "=========================================================="
else
    echo "Usage: $0 [--smoke | --full]"
    exit 1
fi

mkdir -p "$OUT_DIR"
LOG_FILE="$OUT_DIR/run_pilot.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting pipeline in mode: $MODE (Output: $OUT_DIR)"

# Stage 0: Preprocessing & Chunking
CHUNKED_FILE="$OUT_DIR/corpus_chunked.jsonl"
if [ ! -s "$CHUNKED_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 0: Corpus Preprocessing & Chunking ==="
    python scripts/preprocess_corpus.py --out-dir "$OUT_DIR" $LIMIT_ARG
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 0 already complete ($CHUNKED_FILE exists), skipping."
fi

# Stage 1: 7B Relevance Filter
STAGE1_OUT="$OUT_DIR/stage_1_output.jsonl"
STAGE1_SUM="$OUT_DIR/stage_1_summary.json"
if [ ! -s "$STAGE1_OUT" ] || [ ! -s "$STAGE1_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 1: 7B Relevance Filter ==="
    gpurun python flbds/pipeline/stage1_filter.py \
        --input "$CHUNKED_FILE" \
        --output "$STAGE1_OUT" \
        --summary "$STAGE1_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 1 already complete, skipping."
fi

# Stage 2: 72B Teacher Drafting
STAGE2_OUT="$OUT_DIR/stage_2_output.jsonl"
STAGE2_SUM="$OUT_DIR/stage_2_summary.json"
if [ ! -s "$STAGE2_OUT" ] || [ ! -s "$STAGE2_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 2: 72B Teacher Drafting ==="
    gpurun python flbds/pipeline/stage2_teacher.py \
        --input "$STAGE1_OUT" \
        --output "$STAGE2_OUT" \
        --summary "$STAGE2_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 2 already complete, skipping."
fi

# Stage 3: 72B Agreement Sample
STAGE3_OUT="$OUT_DIR/stage_3_agreement_details.jsonl"
STAGE3_SUM="$OUT_DIR/stage_3_summary.json"
if [ ! -s "$STAGE3_OUT" ] || [ ! -s "$STAGE3_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 3: 72B Agreement Sample ==="
    gpurun python flbds/pipeline/stage3_agreement.py \
        --stage2-output "$STAGE2_OUT" \
        --output-details "$STAGE3_OUT" \
        --summary "$STAGE3_SUM" \
        --max-sample "$AGREE_SAMPLE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 3 already complete, skipping."
fi

# Stage 4: Deterministic Evidence Check (CPU)
STAGE4_OUT="$OUT_DIR/stage_4_output.jsonl"
STAGE4_SUM="$OUT_DIR/stage_4_summary.json"
if [ ! -s "$STAGE4_OUT" ] || [ ! -s "$STAGE4_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 4: Deterministic Evidence Check (CPU) ==="
    python flbds/pipeline/stage4_evidence.py \
        --input "$STAGE2_OUT" \
        --output "$STAGE4_OUT" \
        --summary "$STAGE4_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 4 already complete, skipping."
fi

# Stage 5: 32B Critic Entailment Check
STAGE5_OUT="$OUT_DIR/stage_5_output.jsonl"
STAGE5_SUM="$OUT_DIR/stage_5_summary.json"
if [ ! -s "$STAGE5_OUT" ] || [ ! -s "$STAGE5_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 5: 32B Critic Entailment Check ==="
    gpurun python flbds/pipeline/stage5_critic.py \
        --input "$STAGE4_OUT" \
        --output "$STAGE5_OUT" \
        --summary "$STAGE5_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 5 already complete, skipping."
fi

# Stage 6: 7B + Pint Quantity Extraction & Normalization
STAGE6_OUT="$OUT_DIR/stage_6_output.jsonl"
STAGE6_SUM="$OUT_DIR/stage_6_summary.json"
if [ ! -s "$STAGE6_OUT" ] || [ ! -s "$STAGE6_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 6: 7B + Pint Quantity Extraction ==="
    gpurun python flbds/pipeline/stage6_quantities.py \
        --input "$STAGE5_OUT" \
        --output "$STAGE6_OUT" \
        --summary "$STAGE6_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 6 already complete, skipping."
fi

# Stage 7: Near-Duplicate Removal (CPU)
STAGE7_OUT="$OUT_DIR/silver_cards.jsonl"
STAGE7_SUM="$OUT_DIR/stage_7_summary.json"
if [ ! -s "$STAGE7_OUT" ] || [ ! -s "$STAGE7_SUM" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Stage 7: Near-Duplicate Removal (CPU) ==="
    python flbds/pipeline/stage7_dedup.py \
        --input "$STAGE6_OUT" \
        --output "$STAGE7_OUT" \
        --summary "$STAGE7_SUM"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stage 7 already complete, skipping."
fi

# Step 6 Candidates
GOLD_CANDS="$OUT_DIR/gold_candidates.json"
if [ ! -s "$GOLD_CANDS" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Step 6: Sampling 30 Candidates for Gold Annotation ==="
    python scripts/sample_gold_candidates.py \
        --input "$CHUNKED_FILE" \
        --output "$GOLD_CANDS" \
        --seed 42 \
        --n-bio 15 \
        --n-eng 15
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Aggregating Run Metrics ==="
python - << PY
import json
from pathlib import Path

out_dir = Path("$OUT_DIR")
stages = [1, 2, 3, 4, 5, 6, 7]
summaries = []
total_gpu_hours = 0.0

for s in stages:
    sp = out_dir / f"stage_{s}_summary.json"
    if sp.exists():
        with open(sp) as f:
            d = json.load(f)
            summaries.append(d)
            total_gpu_hours += d.get("gpu_hours", 0.0)

print("\n" + "="*80)
print(f" PILOT PIPELINE RUN SUMMARY ({out_dir.name.upper()})")
print("="*80)
print(f"{'Stage':<8} {'Stage Name':<32} {'In':<6} {'Out':<6} {'Drop':<6} {'Tok/s':<10} {'GPU-h':<8}")
print("-" * 80)
for d in summaries:
    stg = str(d.get("stage", ""))
    name = d.get("stage_name", "")[:30]
    n_in = str(d.get("input_count", d.get("sample_size", "-")))
    n_out = str(d.get("output_count", d.get("valid_evaluations", "-")))
    n_drop = str(d.get("dropped_count", "-"))
    tok_s = str(d.get("decode_tokens_per_sec", d.get("tokens_per_sec", "-")))
    gpu_h = f"{d.get('gpu_hours', 0.0):.4f}"
    print(f"{stg:<8} {name:<32} {n_in:<6} {n_out:<6} {n_drop:<6} {tok_s:<10} {gpu_h:<8}")
print("-" * 80)
print(f"TOTAL ESTIMATED GPU-HOURS: {total_gpu_hours:.4f} h")
print("="*80 + "\n")

run_report = {
    "output_dir": str(out_dir),
    "total_gpu_hours": round(total_gpu_hours, 5),
    "stages": summaries
}
with open(out_dir / "pilot_run_summary.json", "w") as f:
    json.dump(run_report, f, indent=2)
PY

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pilot run finished successfully!"
