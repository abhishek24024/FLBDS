"""Stage 6: Physical Quantity Extraction and Pint Unit Normalization using Qwen2.5-7B-Instruct."""

import argparse
import json
import time
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
import pint
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
from flbds.schema import Quantity

ureg = pint.UnitRegistry()


class CandidateQuantity(BaseModel):
    name: str = Field(..., description="Quantity name (e.g. thermal_conductivity, latent_heat, temperature, pore_size)")
    value: float = Field(..., description="Numerical value")
    unit: str = Field(..., description="Unit string (e.g. 'W / (m * K)', 'degC', 'kJ / kg', 'mm', 'bar')")
    regime: str = Field(default="ambient", description="Operational regime or boundary condition")


class QuantityList(BaseModel):
    items: list[CandidateQuantity] = Field(default_factory=list)


def normalize_unit_string(unit_str: str) -> str:
    """Normalize common unit colloquialisms into strict Pint-parseable expressions."""
    u = unit_str.strip()
    replacements = {
        "°C": "degC",
        "C": "degC",
        "deg C": "degC",
        "degrees C": "degC",
        "°F": "degF",
        "F": "degF",
        "W/m-K": "W / (m * K)",
        "W/mK": "W / (m * K)",
        "W/m*K": "W / (m * K)",
        "J/g": "J / g",
        "kJ/kg": "kJ / kg",
        "W/m^2": "W / m^2",
        "W/m2": "W / m^2",
    }
    return replacements.get(u, u)


def build_quantity_prompt(rec: dict) -> str:
    text = rec["text"][:3000]
    title = rec.get("title", "")

    system_prompt = (
        "You are an expert physical metrologist extracting quantitative parameters from technical text.\n"
        "Domain: Thermal, fluid, and porous-media quantities (temperatures, thermal conductivities, latent heat, "
        "flow rates, pore diameters, contact angles, pressures, convective heat transfer coefficients).\n"
        "Extract only physical parameters with explicit numerical values and units stated in the text.\n"
        "Respond strictly with the required JSON."
    )

    user_prompt = (
        f"Title: {title}\n"
        f"Text excerpt:\n{text}\n\n"
        f"Extract all explicit physical quantities with numerical value, unit, and regime."
    )

    return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"


def run_quantities(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    model_dir: str,
    max_docs: int | None = None,
) -> dict:
    t_start = time.perf_counter()
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                if max_docs and len(records) >= max_docs:
                    break

    input_count = len(records)
    print(f"[Stage 6 Quantities] Loaded {input_count} cards for physical parameter extraction", flush=True)

    prompts = [build_quantity_prompt(r) for r in records]

    print(f"[Stage 6 Quantities] Initializing vLLM with 7B model: {model_dir}...", flush=True)
    t_load = time.perf_counter()
    llm = LLM(
        model=model_dir,
        max_model_len=4096,
        gpu_memory_utilization=0.85,
        trust_remote_code=True,
    )
    load_time = time.perf_counter() - t_load
    print(f"[Stage 6 Quantities] Model loaded in {load_time:.2f} s. Running quantity extraction...", flush=True)

    schema = QuantityList.model_json_schema()
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=400,
        structured_outputs=StructuredOutputsParams(json=schema),
    )

    t_gen = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params)
    gen_time = time.perf_counter() - t_gen

    total_prompt_tokens = sum(len(o.prompt_token_ids) for o in outputs)
    total_output_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    decode_tok_s = total_output_tokens / max(0.001, gen_time)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_extracted = 0
    pint_valid = 0
    pint_rejected = 0

    with open(output_path, "w") as fout:
        for rec, out in zip(records, outputs):
            card = rec["card"]
            quant_objs = []
            try:
                cand_list = QuantityList.model_validate_json(out.outputs[0].text.strip())
                for item in cand_list.items:
                    total_extracted += 1
                    norm_unit = normalize_unit_string(item.unit)
                    try:
                        # Verify dimensional validity via Pint
                        ureg.parse_units(norm_unit)
                        q = Quantity(
                            name=item.name,
                            value=item.value,
                            unit=norm_unit,
                            regime_of_validity=item.regime,
                        )
                        quant_objs.append(q.model_dump())
                        pint_valid += 1
                    except Exception:
                        pint_rejected += 1
            except Exception:
                pass

            card["quantities"] = quant_objs
            rec["card"] = card
            fout.write(json.dumps(rec) + "\n")

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    summary = {
        "stage": 6,
        "stage_name": "7B + Pint Quantity Extraction & Normalization",
        "model": Path(model_dir).name,
        "input_count": input_count,
        "output_count": input_count,
        "dropped_count": 0,
        "drop_reasons": {},
        "quantities_extracted": total_extracted,
        "pint_valid_quantities": pint_valid,
        "pint_rejected_quantities": pint_rejected,
        "prompt_tokens": total_prompt_tokens,
        "output_tokens": total_output_tokens,
        "decode_tokens_per_sec": round(decode_tok_s, 1),
        "elapsed_seconds": round(elapsed, 2),
        "gpu_hours": gpu_hours,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(
        f"[Stage 6 Quantities] Complete: Extracted {total_extracted} quantities "
        f"({pint_valid} Pint-validated, {pint_rejected} rejected). Logged -> {summary_path}",
        flush=True,
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 6 quantity extraction.")
    parser.add_argument("--input", default="/home/abhishek24024/flbds_data/pilot/stage_5_output.jsonl")
    parser.add_argument("--output", default="/home/abhishek24024/flbds_data/pilot/stage_6_output.jsonl")
    parser.add_argument("--summary", default="/home/abhishek24024/flbds_data/pilot/stage_6_summary.json")
    parser.add_argument("--config", default="configs/models.yaml")
    parser.add_argument("--max-docs", type=int, default=None)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)["extractor"]

    run_quantities(
        input_path=Path(args.input),
        output_path=Path(args.output),
        summary_path=Path(args.summary),
        model_dir=cfg["local_dir"],
        max_docs=args.max_docs,
    )


if __name__ == "__main__":
    main()
