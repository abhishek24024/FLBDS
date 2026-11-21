#!/usr/bin/env python3
"""scripts/run_v10.py
V10 batched runner over the sealed parametric instances (or the 12 dev cases with --instances dev).

CPU / HF transformers (default):
    python scripts/run_v10.py --backend hf \
        --model-dir /home/abhishek24024/flbds_data/models/Qwen2.5-7B-Instruct \
        --output-dir /home/abhishek24024/flbds_data/v10_cpu_run1

Results are appended incrementally to <output-dir>/<COND>.jsonl (one line per instance x seed), processed
in chunks of --chunk-instances instances; re-running the same command RESUMES (skips instance x seed lines
already present). <COND>_summary.json and summary_all.json are rewritten after every chunk.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from flbds.v10.gen import Completion, GenParams, RequestOutput
from flbds.v10.generator import load_instances
from flbds.v10.runner import (
    CONDITIONS,
    DEFAULT_CONDITIONS,
    RunConfig,
    run_condition,
    summarise,
)


class VLLMAdapter:
    """Wraps vllm.LLM so it accepts chat messages + GenParams (no constrained decoding, same as HF)."""

    def __init__(self, llm: Any, log_every: int = 1) -> None:
        from vllm import SamplingParams

        self.llm = llm
        self.SP = SamplingParams
        self.tok = llm.get_tokenizer()
        self.n_calls = 0
        self.log_every = log_every

    def generate(
        self, prompts: list[list[dict[str, str]]], params: list[GenParams]
    ) -> list[Any]:
        self.n_calls += 1
        t0 = time.perf_counter()
        texts = [
            self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
            for m in prompts
        ]
        sps = [
            self.SP(
                temperature=p.temperature,
                top_p=p.top_p,
                seed=p.seed,
                max_tokens=p.max_tokens,
            )
            for p in params
        ]
        outs = self.llm.generate(texts, sps, use_tqdm=False)
        if self.log_every and self.n_calls % self.log_every == 0:
            print(
                f"    [vllm] call {self.n_calls}: {len(texts)} prompts in {time.perf_counter() - t0:.1f}s",
                flush=True,
            )
        return [
            RequestOutput([Completion(o.outputs[0].text, list(o.outputs[0].token_ids))])
            for o in outs
        ]


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def select_instances(
    instances: list[dict[str, Any]], max_instances: int, smoke: int
) -> list[dict[str, Any]]:
    if smoke > 0:
        per: dict[str, int] = {}
        sel = []
        for inst in instances:
            if per.get(inst["family"], 0) < smoke:
                sel.append(inst)
                per[inst["family"]] = per.get(inst["family"], 0) + 1
        instances = sel
    if max_instances > 0:
        # round-robin over families so a truncated run stays balanced
        by_fam: dict[str, list[dict[str, Any]]] = {}
        for inst in instances:
            by_fam.setdefault(inst["family"], []).append(inst)
        rr: list[dict[str, Any]] = []
        while len(rr) < min(max_instances, len(instances)):
            for fam in sorted(by_fam):
                if by_fam[fam] and len(rr) < max_instances:
                    rr.append(by_fam[fam].pop(0))
        instances = rr
    return instances


def load_done(path: Path) -> tuple[list[dict[str, Any]], set[tuple[str, int]]]:
    if not path.exists():
        return [], set()
    recs = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # truncated last line from an interrupted run
    return recs, {(r["instance_id"], r["seed"]) for r in recs}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["vllm", "hf"], default="hf")
    ap.add_argument(
        "--model-dir",
        default="/home/abhishek24024/flbds_data/models/Qwen2.5-7B-Instruct",
    )
    ap.add_argument(
        "--instances",
        default=str(REPO / "flbds/v10/instances_v10.json"),
        help="path to sealed instance JSON, or 'dev' for the 12 dev cases",
    )
    ap.add_argument(
        "--output-dir", default="/home/abhishek24024/flbds_data/v10_cpu_run1"
    )
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2])
    ap.add_argument("--conditions", nargs="+", default=DEFAULT_CONDITIONS)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=350)
    ap.add_argument(
        "--max-instances",
        type=int,
        default=0,
        help="0 = all; else family-balanced subset",
    )
    ap.add_argument(
        "--smoke", type=int, default=0, help="if >0, first N instances per family"
    )
    ap.add_argument(
        "--chunk-instances",
        type=int,
        default=12,
        help="instances per incremental chunk",
    )
    ap.add_argument(
        "--log-every", type=int, default=1, help="print every N generate batches"
    )
    ap.add_argument("--threads", type=int, default=96)
    ap.add_argument("--batch-size", type=int, default=48)
    ap.add_argument("--max-model-len", type=int, default=8192)
    ap.add_argument("--tp", type=int, default=1)
    ap.add_argument("--gpu-mem", type=float, default=0.90)
    return ap


def make_llm(args: argparse.Namespace) -> Any:
    if args.backend == "hf":
        from flbds.v10.hf_backend import HFLLM

        return HFLLM(
            args.model_dir,
            threads=args.threads,
            batch_size=args.batch_size,
            log_every=args.log_every,
        )
    from vllm import LLM

    llm = LLM(
        model=args.model_dir,
        tensor_parallel_size=args.tp,
        gpu_memory_utilization=args.gpu_mem,
        max_model_len=args.max_model_len,
        trust_remote_code=True,
        enable_prefix_caching=True,
    )
    return VLLMAdapter(llm, log_every=args.log_every)


def run(args: argparse.Namespace, llm: Any = None) -> dict[str, Any]:
    unknown = [c for c in args.conditions if c not in CONDITIONS]
    if unknown:
        raise SystemExit(f"unknown conditions {unknown}; known: {list(CONDITIONS)}")
    if args.instances == "dev":
        from flbds.v10.dev_instances import build_dev_instances

        instances, inst_sha = build_dev_instances(), "dev"
    else:
        instances = load_instances(args.instances)
        inst_sha = json.loads(Path(args.instances).read_text())["sha256"]
    instances = select_instances(instances, args.max_instances, args.smoke)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "git_sha": git_sha(),
        "instances": args.instances,
        "instances_sha256": inst_sha,
        "n_instances": len(instances),
        "args": {k: v for k, v in vars(args).items()},
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps(meta, indent=2, default=str), flush=True)

    if llm is None and any(CONDITIONS[c].llm for c in args.conditions):
        llm = make_llm(args)
    cfg = RunConfig(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        log=lambda s: print(s, flush=True),
    )

    summ_path = out_dir / "summary_all.json"
    all_summ: dict[str, Any] = (
        json.loads(summ_path.read_text()) if summ_path.exists() else {}
    )
    for cond in args.conditions:
        print(
            "=" * 80 + f"\nCONDITION {cond}: {CONDITIONS[cond]}\n" + "=" * 80,
            flush=True,
        )
        jpath = out_dir / f"{cond}.jsonl"
        recs, done = load_done(jpath)
        todo = [
            i
            for i in instances
            if any((i["instance_id"], s) not in done for s in args.seeds)
        ]
        if done:
            print(
                f"  resuming: {len(recs)} records present, {len(todo)} instances to run",
                flush=True,
            )
        t0 = time.perf_counter()
        for c0 in range(0, len(todo), max(1, args.chunk_instances)):
            chunk = todo[c0 : c0 + args.chunk_instances]
            new = run_condition(llm, chunk, args.seeds, cond, cfg)
            new = [r for r in new if (r["instance_id"], r["seed"]) not in done]
            with open(jpath, "a") as f:
                f.writelines(json.dumps(r) + "\n" for r in new)
            recs += new
            done |= {(r["instance_id"], r["seed"]) for r in new}
            s = summarise(recs, cond)
            s["elapsed_seconds_this_invocation"] = round(time.perf_counter() - t0, 1)
            (out_dir / f"{cond}_summary.json").write_text(json.dumps(s, indent=2))
            all_summ[cond] = s
            summ_path.write_text(json.dumps(all_summ, indent=2))
            print(
                f"  {cond} after {len(recs)} runs: eval {s['eval_passes']}/{s['n_runs']} ({s['pass_rate']:.3f}) "
                f"screen {s['screen_passes']} | S&!E {s['screen_pass_eval_fail']} !S&E {s['screen_fail_eval_pass']} "
                f"| tmpl_err {s['template_choice_errors']} schema_fail {s['schema_failure_final']} "
                f"| tokens {s['tokens_total']} | {s['elapsed_seconds_this_invocation']}s",
                flush=True,
            )
    return all_summ


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
