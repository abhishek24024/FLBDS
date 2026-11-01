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


import re

def old_normalize_unit_string(unit_str: str) -> str:
    """Original un-sanitized unit normalizer from pilot run."""
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


def sanitize_quantity(value: float, unit_str: str) -> tuple[float, str]:
    """Robust physical quantity and unit sanitizer.

    Handles:
    - Unicode minus (\\u2212) and dashes (\\u2013, \\u2014) -> '-'
    - vol.%, wt.%, vol %, wt %, volume %, weight % -> 'percent'
    - Compound slashes e.g. g/m2/h, kg/m2/s, kJ/kg/K -> g / (m^2 * hr), kg / (m^2 * s)
    - Scientific scaling prefixes e.g. 'x10^-6 m', '10^-3 Pa' -> scales numerical value, unit 'm', 'Pa'
    - Exponents and powers e.g. m2 -> m^2, J g-1 -> J * g^-1
    """
    u = unit_str.strip()
    # Normalize unicode minuses and dashes
    u = u.replace("−", "-").replace("–", "-").replace("—", "-")
    u = u.replace("²", "^2").replace("³", "^3").replace("⁻¹", "^-1").replace("⁻²", "^-2")

    # Extract scientific prefix multiplier if in unit string e.g. x10^-6, 10^-3, x10^5
    scale_match = re.search(r"[x×]?\s*10\s*\^\s*([+-]?\d+)", u)
    if scale_match:
        exp = int(scale_match.group(1))
        value = value * (10.0 ** exp)
        u = re.sub(r"[x×]?\s*10\s*\^\s*([+-]?\d+)\s*\*?", "", u).strip()

    # Percentage variants
    u = re.sub(r"^(vol|wt|weight|volume)\.?\s*%", "percent", u, flags=re.IGNORECASE)
    u = re.sub(r"^(vol|wt|weight|volume)\s*percent", "percent", u, flags=re.IGNORECASE)
    u = re.sub(r"%\s*(vol|wt)", "percent", u, flags=re.IGNORECASE)

    # Temperatures
    u = re.sub(r"^(°C|C|deg\s*C|degrees?\s*C)$", "degC", u, flags=re.IGNORECASE)
    u = re.sub(r"^(°F|F|deg\s*F|degrees?\s*F)$", "degF", u, flags=re.IGNORECASE)

    # Hyphenated unit products (e.g. m-K -> m * K)
    u = re.sub(r"([a-zA-Z])-([a-zA-Z])", r"\1 * \2", u)
    u = re.sub(r"/mK\b", "/(m*K)", u)

    # Multi-slash division compound expressions
    slash_parts = [p.strip() for p in u.split("/")]
    if len(slash_parts) > 2:
        num = slash_parts[0]
        denom = " * ".join(slash_parts[1:])
        u = f"{num} / ({denom})"

    # Unmarked powers e.g. m2 -> m^2, m3 -> m^3
    u = re.sub(r"([a-zA-Z])([23])\b", r"\1^\2", u)

    # Negative exponents written as space-separated e.g. J g-1 -> J * g^-1
    u = re.sub(r"\b([a-df-zA-DF-Z])\s*-\s*(\d+)", r"\1^-\2", u)

    # Hour abbreviation
    u = re.sub(r"\b(h|hr|hour|hours)\b", "hr", u)

    # Implicit multiplication between tokens
    parts = u.split("*")
    new_parts = []
    for p in parts:
        sub = re.sub(r"([a-zA-Z\^0-9\-\+]+)\s+([a-zA-Z\^0-9\-\+]+)", r"\1 * \2", p.strip())
        new_parts.append(sub)
    u = " * ".join(new_parts)

    return value, u


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
    old_valid_count = 0
    old_rejected_count = 0
    pint_valid = 0
    pint_rejected = 0

    recovered_items = []
    remaining_rejected_items = []

    with open(output_path, "w") as fout:
        for rec, out in zip(records, outputs):
            card = rec["card"]
            quant_objs = []
            try:
                cand_list = QuantityList.model_validate_json(out.outputs[0].text.strip())
                for item in cand_list.items:
                    total_extracted += 1

                    # 1. Test original un-sanitized normalizer
                    old_unit = old_normalize_unit_string(item.unit)
                    old_passed = False
                    try:
                        ureg.parse_units(old_unit)
                        old_passed = True
                        old_valid_count += 1
                    except Exception:
                        old_rejected_count += 1

                    # 2. Test new sanitizer
                    san_val, san_unit = sanitize_quantity(item.value, item.unit)
                    try:
                        parsed_u = ureg.parse_units(san_unit)
                        q = Quantity(
                            name=item.name,
                            value=san_val,
                            unit=san_unit,
                            regime_of_validity=item.regime,
                        )
                        quant_objs.append(q.model_dump())
                        pint_valid += 1

                        if not old_passed:
                            recovered_items.append({
                                "doc_id": rec.get("doc_id", ""),
                                "name": item.name,
                                "raw_value": item.value,
                                "raw_unit": item.unit,
                                "sanitized_value": san_val,
                                "sanitized_unit": san_unit,
                                "pint_parsed": str(parsed_u),
                            })
                    except Exception as e:
                        pint_rejected += 1
                        remaining_rejected_items.append({
                            "doc_id": rec.get("doc_id", ""),
                            "name": item.name,
                            "raw_value": item.value,
                            "raw_unit": item.unit,
                            "sanitized_unit": san_unit,
                            "pint_error": str(e),
                        })
            except Exception:
                pass

            card["quantities"] = quant_objs
            rec["card"] = card
            fout.write(json.dumps(rec) + "\n")

    elapsed = time.perf_counter() - t_start
    gpu_hours = round(elapsed / 3600.0, 5)

    audit_path = output_path.parent / "stage_6_recovery_audit.json"
    audit_data = {
        "total_extracted": total_extracted,
        "old_pipeline": {
            "valid": old_valid_count,
            "purged": old_rejected_count,
        },
        "new_pipeline": {
            "valid": pint_valid,
            "purged": pint_rejected,
            "recovered_count": len(recovered_items),
        },
        "recovered_sample_10": recovered_items[:10],
        "remaining_rejected_sample_10": remaining_rejected_items[:10],
        "all_recovered": recovered_items,
        "all_remaining_rejected": remaining_rejected_items,
    }
    with open(audit_path, "w") as fa:
        json.dump(audit_data, fa, indent=2)

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
        "old_valid_quantities": old_valid_count,
        "old_purged_quantities": old_rejected_count,
        "recovered_quantities": len(recovered_items),
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
