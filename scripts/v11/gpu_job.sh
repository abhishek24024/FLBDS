#!/bin/bash
# V11 pilot GPU job: generation (Qwen3-VL-32B) -> judging (Qwen2.5-72B) -> renders (Qwen-Image)
set -x
export PATH=/home/abhishek24024/flbds_env/bin:/usr/local/cuda/bin:$PATH CUDA_HOME=/usr/local/cuda PYTHONPATH=/home/abhishek24024/flbds_v10
cd /home/abhishek24024/flbds_v10
P=/home/abhishek24024/flbds_env/bin/python3
$P scripts/v11/run_e1_e2.py && echo STAGE1_OK
$P scripts/v11/run_judge.py && echo STAGE2_OK
$P scripts/v11/render_blueprints.py && echo STAGE3_OK
echo ALLDONE
