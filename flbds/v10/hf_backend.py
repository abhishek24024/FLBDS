"""flbds/v10/hf_backend.py
CPU HuggingFace-transformers backend that mimics vLLM's generate() output shape.

    llm = HFLLM("/path/Qwen2.5-7B-Instruct", threads=96, batch_size=48)
    outs = llm.generate([messages, ...], [GenParams(...), ...])
    outs[i].outputs[0].text / .token_ids

No constrained decoding (GenParams.json_schema / choice are ignored). Prompts are sorted by token length
and left-padded per batch; torch.manual_seed(first seed of the batch) before each batch. Batches are formed
from prompts sharing (temperature, top_p, max_tokens).
"""

from __future__ import annotations

import time
from typing import Any

from flbds.v10.gen import Completion, GenParams, RequestOutput


class HFLLM:
    def __init__(
        self,
        model_dir: str,
        threads: int = 96,
        batch_size: int = 48,
        dtype: str = "bfloat16",
        log_every: int = 1,
        model: Any = None,
        tokenizer: Any = None,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        torch.set_num_threads(threads)
        self.tok = tokenizer or AutoTokenizer.from_pretrained(model_dir)
        self.tok.padding_side = "left"
        if self.tok.pad_token_id is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = model or AutoModelForCausalLM.from_pretrained(
            model_dir, dtype=getattr(torch, dtype)
        )
        self.model.eval()
        self.batch_size = batch_size
        self.log_every = log_every
        self.n_batches = 0
        self.tokens_out = 0
        self.t_start = time.perf_counter()
        eos = (
            self.model.generation_config.eos_token_id
            if self.model.generation_config is not None
            else None
        )
        eos_ids = eos if isinstance(eos, list) else ([eos] if eos is not None else [])
        self.stop_ids = set(eos_ids) | {
            self.tok.eos_token_id,
            self.tok.pad_token_id,
        } - {None}

    def render(self, messages: list[dict[str, str]]) -> str:
        return self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    def _trim(self, ids: list[int]) -> list[int]:
        for j, t in enumerate(ids):
            if t in self.stop_ids:
                return ids[:j]
        return ids

    def generate(
        self, prompts: list[list[dict[str, str]]], params: list[GenParams]
    ) -> list[RequestOutput]:
        torch = self.torch
        texts = [self.render(m) for m in prompts]
        lens = [len(self.tok(t, add_special_tokens=False)["input_ids"]) for t in texts]
        # group by sampling config, then sort by length inside the group
        order = sorted(
            range(len(texts)),
            key=lambda i: (
                params[i].temperature,
                params[i].top_p,
                params[i].max_tokens,
                lens[i],
            ),
        )
        results: list[RequestOutput | None] = [None] * len(texts)
        batches: list[list[int]] = []
        cur: list[int] = []
        for i in order:
            if cur and (
                len(cur) >= self.batch_size or _cfg(params[cur[0]]) != _cfg(params[i])
            ):
                batches.append(cur)
                cur = []
            cur.append(i)
        if cur:
            batches.append(cur)
        for b in batches:
            gp = params[b[0]]
            torch.manual_seed(gp.seed)
            enc = self.tok(
                [texts[i] for i in b],
                return_tensors="pt",
                padding=True,
                add_special_tokens=False,
            )
            t0 = time.perf_counter()
            with torch.inference_mode():
                gen = self.model.generate(
                    **enc,
                    do_sample=gp.temperature > 0,
                    temperature=gp.temperature if gp.temperature > 0 else None,
                    top_p=gp.top_p if gp.temperature > 0 else None,
                    max_new_tokens=gp.max_tokens,
                    pad_token_id=self.tok.pad_token_id,
                )
            new = gen[:, enc["input_ids"].shape[1] :]
            n_tok = 0
            for row, i in enumerate(b):
                ids = self._trim(new[row].tolist())
                n_tok += len(ids)
                results[i] = RequestOutput(
                    [Completion(self.tok.decode(ids, skip_special_tokens=True), ids)]
                )
            self.n_batches += 1
            self.tokens_out += n_tok
            if self.log_every and self.n_batches % self.log_every == 0:
                dt = time.perf_counter() - t0
                print(
                    f"    [hf] batch {self.n_batches}: {len(b)} prompts, max_in {enc['input_ids'].shape[1]} tok, "
                    f"{n_tok} out tok in {dt:.1f}s ({n_tok / max(dt, 1e-9):.1f} tok/s); total out "
                    f"{self.tokens_out} tok, elapsed {time.perf_counter() - self.t_start:.0f}s",
                    flush=True,
                )
        return [r for r in results if r is not None]


def _cfg(p: GenParams) -> tuple[float, float, int]:
    return (p.temperature, p.top_p, p.max_tokens)
