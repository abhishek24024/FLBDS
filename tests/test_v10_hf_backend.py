"""HF backend test on a tiny Qwen2 checkpoint.

Set FLBDS_TINY_HF_MODEL to a local dir of e.g. trl-internal-testing/tiny-Qwen2ForCausalLM-2.5; skipped otherwise.
"""

from __future__ import annotations

import os

import pytest

from flbds.v10.gen import GenParams

MODEL = os.environ.get("FLBDS_TINY_HF_MODEL")
pytestmark = pytest.mark.skipif(not MODEL, reason="FLBDS_TINY_HF_MODEL not set")


def _msgs(n: int) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "word " * n},
    ]


def test_hf_generate_order_batching_and_shape() -> None:
    pytest.importorskip("torch")
    from flbds.v10.hf_backend import HFLLM

    llm = HFLLM(MODEL, threads=2, batch_size=2, dtype="float32", log_every=1)
    prompts = [_msgs(n) for n in (30, 2, 15, 7, 40)]
    greedy = [GenParams(temperature=0.0, seed=1, max_tokens=6) for _ in prompts]
    batched = llm.generate(prompts, greedy)
    assert len(batched) == len(prompts)
    singles = [llm.generate([p], [g])[0] for p, g in zip(prompts, greedy)]
    for b, s in zip(batched, singles):
        assert len(b.outputs[0].token_ids) <= 6
        assert (
            b.outputs[0].token_ids == s.outputs[0].token_ids
        )  # order preserved, left-padding correct
        assert isinstance(b.outputs[0].text, str)
    sampled = llm.generate(
        prompts[:3], [GenParams(temperature=0.7, top_p=0.9, seed=3, max_tokens=5)] * 3
    )
    again = llm.generate(
        prompts[:3], [GenParams(temperature=0.7, top_p=0.9, seed=3, max_tokens=5)] * 3
    )
    assert [o.outputs[0].token_ids for o in sampled] == [
        o.outputs[0].token_ids for o in again
    ]  # seeded
    assert "<|im_start|>assistant" in llm.render(_msgs(1))
