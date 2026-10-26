#!/usr/bin/env python3
"""Run a throughput calibration benchmark on an open model using vLLM on NVIDIA H200."""

import argparse
import json
import time
import yaml
from pathlib import Path
import torch
from vllm import LLM, SamplingParams


def load_sample_prompts(num_prompts: int = 10, max_chars: int = 4000) -> list[str]:
    """Build real prompts from the harvested pilot corpus."""
    prompts = []
    bio_path = Path("/home/abhishek24024/flbds_data/corpus/bio_pilot.jsonl")
    eng_path = Path("/home/abhishek24024/flbds_data/corpus/eng_pilot.jsonl")

    for path in [bio_path, eng_path]:
        if path.exists():
            with open(path) as f:
                for line in f:
                    doc = json.loads(line)
                    text = doc.get("text", "")[:max_chars]
                    prompt = (
                        f"Below is a technical document describing a physical mechanism:\n\n"
                        f"Title: {doc.get('title')}\n"
                        f"Text:\n{text}\n\n"
                        f"Task: Extract the core physical mechanism, governing law, and state change."
                    )
                    prompts.append(prompt)
                    if len(prompts) >= num_prompts:
                        return prompts
    return prompts


def main():
    parser = argparse.ArgumentParser(description="Calibrate model throughput.")
    parser.add_argument("--role", choices=["filter", "critic", "teacher"], required=True)
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--num-prompts", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)[args.role]

    model_dir = cfg["local_dir"]
    quant = cfg.get("quantization")
    max_model_len = cfg.get("max_model_len", 8192)
    gpu_mem = cfg.get("gpu_memory_utilization", 0.90)

    prompts = load_sample_prompts(num_prompts=args.num_prompts)
    print(f"=== Throughput Calibration: {args.role} ({model_dir}) ===", flush=True)
    print(f"Loaded {len(prompts)} real corpus prompts. Initializing vLLM...", flush=True)

    t0 = time.perf_counter()
    llm = LLM(
        model=model_dir,
        quantization=quant,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_mem,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t0
    print(f"Model loaded in {load_time:.2f} s. Running benchmark...", flush=True)

    sampling_params = SamplingParams(
        temperature=cfg.get("temperature", 0.0),
        max_tokens=args.max_tokens,
    )

    # Warmup pass
    _ = llm.generate([prompts[0]], sampling_params)

    # Timed run
    start_time = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    total_time = time.perf_counter() - start_time

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)

    overall_tok_s = (total_prompt_tokens + total_output_tokens) / total_time
    decode_tok_s = total_output_tokens / total_time
    prefill_est_tok_s = total_prompt_tokens / max(0.001, total_time - (total_output_tokens / decode_tok_s * 0.5))

    vram_used_gb = torch.cuda.max_memory_allocated() / (1024**3)

    summary = {
        "role": args.role,
        "model_dir": model_dir,
        "quantization": quant or "BF16",
        "num_prompts": len(prompts),
        "total_prompt_tokens": total_prompt_tokens,
        "total_output_tokens": total_output_tokens,
        "elapsed_seconds": round(total_time, 2),
        "decode_tokens_per_sec": round(decode_tok_s, 1),
        "overall_tokens_per_sec": round(overall_tok_s, 1),
        "vram_peak_gb": round(vram_used_gb, 1),
    }

    print("\n=== Calibration Results ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)

    # Append to docs/throughput.md
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    out_file = docs_dir / "throughput.md"

    if not out_file.exists():
        with open(out_file, "w") as f:
            f.write("# Measured vLLM Throughput on NVIDIA H200 (141 GB SXM)\n\n")
            f.write("| Role | Model | Quantization | Prompts | Prompt Tokens | Output Tokens | Measured Decode (tok/s) | Doc Assumption Decode | Ratio (Measured/Assumed) | Peak VRAM (GB) |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|\n")

    assumed_decode = {"filter": 12000, "critic": 5000, "teacher": 2000}.get(args.role, 0)
    ratio = round(decode_tok_s / assumed_decode, 2) if assumed_decode else 1.0

    with open(out_file, "a") as f:
        f.write(
            f"| {args.role} | {Path(model_dir).name} | {summary['quantization']} | "
            f"{len(prompts)} | {total_prompt_tokens} | {total_output_tokens} | "
            f"**{summary['decode_tokens_per_sec']}** | {assumed_decode} | {ratio}x | {summary['vram_peak_gb']} GB |\n"
        )
    print(f"Logged calibration results to {out_file}.", flush=True)


if __name__ == "__main__":
    main()
