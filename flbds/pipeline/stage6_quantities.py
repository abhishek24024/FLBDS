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

UNIVERSAL_CONSTANTS = {
    "r", "universal gas constant", "gas constant",
    "boltzmann", "boltzmann constant", "kb", "k_b",
    "avogadro", "avogadro constant", "na", "n_a",
    "planck", "planck constant", "h",
    "stefan-boltzmann", "stefan boltzmann", "stefan-boltzmann constant", "sigma",
    "speed of light", "c",
    "acceleration of gravity", "gravitational acceleration", "g",
    "faraday", "faraday constant", "f",
}

def is_universal_constant(name: str, val: float, unit: str) -> bool:
    n = name.strip().lower()
    if n in UNIVERSAL_CONSTANTS:
        return True
    if n == "r" and abs(val - 8.314) < 0.1:
        return True
    if n in ("kb", "k_b") and abs(val - 1.38e-23) < 1e-24:
        return True
    if n in ("na", "n_a") and abs(val - 6.022e23) < 1e22:
        return True
    if n in ("mw", "m_w") and abs(val - 0.018) < 1e-4:
        return True
    return False


def is_number_in_span(val: float, span: str) -> bool:
    """Check if numeric value or close formatting appears in span."""
    s_val = str(val)
    if s_val.endswith(".0"):
        s_val_int = str(int(val))
        if re.search(r'\b' + re.escape(s_val_int) + r'\b', span):
            return True
    if re.search(r'\b' + re.escape(s_val) + r'\b', span):
        return True
    if re.search(r'\b' + re.escape(f"{val:.1f}") + r'\b', span):
        return True
    if re.search(r'\b' + re.escape(f"{val:.2f}") + r'\b', span):
        return True
    return False


def check_name_in_span(name: str, span: str) -> bool:
    """Check if key content words of quantity name appear in span."""
    name_words = re.findall(r'[a-zA-Z]{3,}', name.lower())
    stop = {"the", "and", "for", "with", "per", "from", "into", "over", "rate", "value", "level"}
    keywords = [w for w in name_words if w not in stop]
    if not keywords:
        return True
    span_lower = span.lower()
    return any(kw in span_lower for kw in keywords)


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
    - Unicode superscripts (⁻², ⁻¹, ², ³, etc.) -> '^-2', '^-1', '^2', '^3'
    - Dot products (J·mol−1·K−1, W·m−2·K−1) -> J * mol^-1 * K^-1
    - Dimensionless multipliers (fold, times, x) -> 'dimensionless'
    - vol.%, wt.%, vol %, wt %, volume %, weight % -> 'percent'
    - Compound slashes e.g. g/m2/h, kg/m2/s, kJ/kg/K -> g / (m^2 * hr), kg / (m^2 * s)
    - Scientific scaling prefixes e.g. 'x10^-6 m', '10^-3 Pa' -> scales numerical value, unit 'm', 'Pa'
    - Exponents and powers e.g. m2 -> m^2, J g-1 -> J * g^-1
    """
    u = unit_str.strip()
    # Normalize unicode minuses, dashes, and middle dots
    u = u.replace("−", "-").replace("–", "-").replace("—", "-")
    u = u.replace("·", " * ").replace("•", " * ")

    supers = {
        "⁻": "^-", "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3",
        "⁴": "^4", "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9"
    }
    for k, v in supers.items():
        u = u.replace(k, v)
    u = u.replace("^-^-", "^-").replace("^-^", "^-")

    # Extract scientific prefix multiplier if in unit string e.g. x10^-6, 10^-3, x10^5
    scale_match = re.search(r"[x×]?\s*10\s*\^\s*([+-]?\d+)", u)
    if scale_match:
        exp = int(scale_match.group(1))
        value = value * (10.0 ** exp)
        u = re.sub(r"[x×]?\s*10\s*\^\s*([+-]?\d+)\s*\*?", "", u).strip()

    # Dimensionless ratios and multipliers
    if u.lower() in ["fold", "times", "x", "-", "--"]:
        return value, "dimensionless"

    # Percentage variants
    if re.search(r"(wt|vol|weight|volume)\.?\s*%", u, re.IGNORECASE) or u.endswith("%"):
        return value, "percent"

    # Temperatures
    u = re.sub(r"^(°C|C|deg\s*C|degrees?\s*C)$", "degC", u, flags=re.IGNORECASE)
    u = re.sub(r"^(°F|F|deg\s*F|degrees?\s*F)$", "degF", u, flags=re.IGNORECASE)

    # Adjacent capital units: Wm^-2 -> W * m^-2
    u = re.sub(r"([a-z])([A-Z])", r"\1 * \2", u)
    if u.startswith("Wm^"):
        u = u.replace("Wm^", "W * m^")

    # Replace unit-1 -> unit^-1
    u = re.sub(r"([a-zA-Z]+)-(\d+)", r"\1^-\2", u)

    # Time units in rates: d^-1 -> day^-1, h^-1 -> hr^-1
    u = re.sub(r"\bd\^-", "day^-", u)
    u = re.sub(r"\bh\^-", "hr^-", u)

    # Spacing between unit tokens
    u = re.sub(r"(\^[-+]?\d+)\s+([a-zA-Z])", r"\1 * \2", u)
    u = re.sub(r"([a-zA-Z])\s+([a-zA-Z])", r"\1 * \2", u)

    # Hyphenated unit products (e.g. m-K -> m * K)
    u = re.sub(r"([a-zA-Z])-([a-zA-Z])", r"\1 * \2", u)
    u = re.sub(r"/mK\b", "/(m*K)", u)

    # Multi-slash division compound expressions
    slash_parts = [p.strip() for p in u.split("/")]
    if len(slash_parts) > 2:
        num = slash_parts[0]
        denom = " * ".join(f"({p})" if re.search(r"[\s*]", p) else p for p in slash_parts[1:])
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
    excluded_constants = []

    purged_not_in_span = []
    flagged_mismatched_name = []

    with open(output_path, "w") as fout:
        for rec, out in zip(records, outputs):
            card = rec["card"]
            quant_objs = []
            evidence_spans = [ev.get("text_span", "") for ev in card.get("evidence", [])]
            try:
                cand_list = QuantityList.model_validate_json(out.outputs[0].text.strip())
                for item in cand_list.items:
                    total_extracted += 1

                    # 0. Exclude universal constants and symbol definitions
                    if is_universal_constant(item.name, item.value, item.unit):
                        excluded_constants.append({
                            "doc_id": rec.get("doc_id", ""),
                            "name": item.name,
                            "value": item.value,
                            "unit": item.unit,
                        })
                        continue

                    # Rule 1: Keep quantity ONLY if its number is inside its cited span
                    matching_span = None
                    for span in evidence_spans:
                        if is_number_in_span(item.value, span):
                            matching_span = span
                            break
                    
                    if matching_span is None:
                        purged_not_in_span.append({
                            "doc_id": rec.get("doc_id", ""),
                            "name": item.name,
                            "value": item.value,
                            "unit": item.unit,
                            "reason": "number_not_in_cited_span"
                        })
                        continue

                    # Rule 2: Flag quantity if its name does not match the span wording
                    name_matches = check_name_in_span(item.name, matching_span)
                    regime_label = item.regime
                    if not name_matches:
                        regime_label = f"{item.regime} [FLAG: mismatched_name]"
                        flagged_mismatched_name.append({
                            "doc_id": rec.get("doc_id", ""),
                            "name": item.name,
                            "value": item.value,
                            "unit": item.unit,
                            "matching_span": matching_span[:120],
                            "reason": "name_words_not_in_span"
                        })

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
                            regime_of_validity=regime_label,
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
        "excluded_universal_constants_count": len(excluded_constants),
        "excluded_constants_sample": excluded_constants[:10],
        "purged_not_in_span_count": len(purged_not_in_span),
        "purged_not_in_span_sample": purged_not_in_span[:10],
        "flagged_mismatched_name_count": len(flagged_mismatched_name),
        "flagged_mismatched_name_sample": flagged_mismatched_name[:10],
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
        "all_excluded_constants": excluded_constants,
        "all_purged_not_in_span": purged_not_in_span,
        "all_flagged_mismatched_name": flagged_mismatched_name,
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
