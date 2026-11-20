#!/usr/bin/env python3
"""Prove Stage 6 determinism with explicit vLLM seed=42 across two consecutive runs on 20 cards."""

import json
import time
from pathlib import Path
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
from flbds.pipeline.stage6_quantities import QuantityList, build_quantity_prompt

def main():
    model_dir = "/home/abhishek24024/flbds_data/models/Qwen2.5-7B-Instruct"
    input_file = "/home/abhishek24024/flbds_data/audit6/stage_5_output.jsonl"
    
    # Load 20 cards
    cards = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))
            if len(cards) >= 20:
                break
                
    print(f"Loaded {len(cards)} cards for determinism verification.")
    
    # Prepare prompts
    prompts = [build_quantity_prompt(r) for r in cards]
        
    print(f"Initializing vLLM with model: {model_dir}")
    llm = LLM(
        model=model_dir,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.85,
        max_model_len=4096,
        trust_remote_code=True,
    )
    
    schema = QuantityList.model_json_schema()
    sampling_params = SamplingParams(
        temperature=0.0,
        seed=42,
        max_tokens=400,
        structured_outputs=StructuredOutputsParams(json=schema),
    )
    
    print("Running Run 1 on 20 cards...")
    t0 = time.perf_counter()
    out1 = llm.generate(prompts, sampling_params)
    t1 = time.perf_counter() - t0
    print(f"Run 1 completed in {t1:.2f} s.")
    
    print("Running Run 2 on 20 cards with same seed...")
    t0 = time.perf_counter()
    out2 = llm.generate(prompts, sampling_params)
    t2 = time.perf_counter() - t0
    print(f"Run 2 completed in {t2:.2f} s.")
    
    run1_texts = [o.outputs[0].text for o in out1]
    run2_texts = [o.outputs[0].text for o in out2]
    
    diff_count = 0
    diff_details = []
    for idx, (t1_str, t2_str) in enumerate(zip(run1_texts, run2_texts)):
        doc_id = cards[idx].get("doc_id")
        if t1_str != t2_str:
            diff_count += 1
            diff_details.append({
                "index": idx,
                "doc_id": doc_id,
                "run1": t1_str,
                "run2": t2_str,
            })
            
    out_dir = Path("/home/abhishek24024/flbds_data/audit9")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "stage6_run1.json", "w") as f:
        json.dump([{"doc_id": c.get("doc_id"), "output": t} for c, t in zip(cards, run1_texts)], f, indent=2)
    with open(out_dir / "stage6_run2.json", "w") as f:
        json.dump([{"doc_id": c.get("doc_id"), "output": t} for c, t in zip(cards, run2_texts)], f, indent=2)
        
    summary = {
        "total_cards": len(cards),
        "seed": 42,
        "temperature": 0.0,
        "differing_cards": diff_count,
        "identical_cards": len(cards) - diff_count,
        "determinism_pct": (len(cards) - diff_count) / len(cards) * 100.0,
        "diff_details": diff_details,
    }
    
    with open(out_dir / "stage6_determinism_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n=======================================================")
    print("STAGE 6 DETERMINISM VERIFICATION SUMMARY")
    print(f"  Total Cards:     {len(cards)}")
    print(f"  Identical Cards: {len(cards) - diff_count} / {len(cards)} ({summary['determinism_pct']:.1f}%)")
    print(f"  Differing Cards: {diff_count} / {len(cards)}")
    print("=======================================================")

if __name__ == "__main__":
    main()
