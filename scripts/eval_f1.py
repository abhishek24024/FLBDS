#!/usr/bin/env python3
"""Step 6: Field-level Precision, Recall, and F1 evaluation script for Mechanism Cards."""

import argparse
import json
import math
from pathlib import Path
import pint

ureg = pint.UnitRegistry()


def token_f1(pred_str: str, gold_str: str) -> tuple[float, float, float]:
    """Compute token-level Precision, Recall, and F1 between two strings."""
    pred_toks = set(pred_str.lower().replace("_", " ").split())
    gold_toks = set(gold_str.lower().replace("_", " ").split())

    if not pred_toks and not gold_toks:
        return 1.0, 1.0, 1.0
    if not pred_toks or not gold_toks:
        return 0.0, 0.0, 0.0

    common = pred_toks & gold_toks
    prec = len(common) / len(pred_toks)
    rec = len(common) / len(gold_toks)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def quantity_match(pred_q: dict, gold_q: dict, val_tol: float = 0.10) -> bool:
    """Check if predicted quantity matches gold quantity within tolerance and unit compatibility."""
    # Name match
    if pred_q.get("name", "").lower() != gold_q.get("name", "").lower():
        return False

    # Unit dimensional compatibility
    p_unit = pred_q.get("unit", "")
    g_unit = gold_q.get("unit", "")
    try:
        p_val = pred_q.get("value", 0.0) * ureg(p_unit)
        g_val = gold_q.get("value", 0.0) * ureg(g_unit)
        # Convert pred to gold unit
        p_val_converted = p_val.to(g_unit).magnitude
        g_val_mag = g_val.magnitude
        # Relative error
        diff = abs(p_val_converted - g_val_mag)
        denom = max(abs(g_val_mag), 1e-9)
        return (diff / denom) <= val_tol
    except Exception:
        return False


def evaluate_quantities(pred_quants: list[dict], gold_quants: list[dict]) -> tuple[float, float, float]:
    """Compute Precision, Recall, and F1 for extracted physical quantities."""
    if not pred_quants and not gold_quants:
        return 1.0, 1.0, 1.0
    if not pred_quants:
        return 0.0, 0.0, 0.0
    if not gold_quants:
        return 0.0, 1.0, 0.0

    matched_gold = set()
    true_positives = 0

    for pq in pred_quants:
        for idx, gq in enumerate(gold_quants):
            if idx not in matched_gold and quantity_match(pq, gq):
                true_positives += 1
                matched_gold.add(idx)
                break

    prec = true_positives / len(pred_quants) if pred_quants else 0.0
    rec = true_positives / len(gold_quants) if gold_quants else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def evaluate_card_pair(pred_card: dict, gold_card: dict) -> dict:
    """Evaluate a single predicted card against its gold card on all SAPPhIRE fields."""
    # Effect F1
    pe_eff = pred_card.get("effect", {}).get("canonical_name", "")
    ge_eff = gold_card.get("effect", {}).get("canonical_name", "")
    eff_p, eff_r, eff_f1 = token_f1(pe_eff, ge_eff)
    eff_exact = 1.0 if pe_eff.strip().lower() == ge_eff.strip().lower() and ge_eff else 0.0

    # Action F1 (verb + object)
    pe_act = f"{pred_card.get('action', {}).get('verb', '')} {pred_card.get('action', {}).get('object', '')}"
    ge_act = f"{gold_card.get('action', {}).get('verb', '')} {gold_card.get('action', {}).get('object', '')}"
    act_p, act_r, act_f1 = token_f1(pe_act, ge_act)

    # StateChange F1
    pe_sc = pred_card.get("state_change", {}).get("state_variable", "")
    ge_sc = gold_card.get("state_change", {}).get("state_variable", "")
    sc_p, sc_r, sc_f1 = token_f1(pe_sc, ge_sc)

    # Phenomenon F1
    pe_ph = pred_card.get("phenomenon", {}).get("description", "")
    ge_ph = gold_card.get("phenomenon", {}).get("description", "")
    ph_p, ph_r, ph_f1 = token_f1(pe_ph, ge_ph)

    # Quantities F1
    q_p, q_r, q_f1 = evaluate_quantities(
        pred_card.get("quantities", []),
        gold_card.get("quantities", [])
    )

    macro_f1 = (eff_f1 + act_f1 + sc_f1 + ph_f1 + q_f1) / 5.0

    return {
        "effect_exact_match": eff_exact,
        "effect_f1": round(eff_f1, 4),
        "action_f1": round(act_f1, 4),
        "state_change_f1": round(sc_f1, 4),
        "phenomenon_f1": round(ph_f1, 4),
        "quantities_f1": round(q_f1, 4),
        "macro_f1": round(macro_f1, 4),
    }


def evaluate_corpus(pred_cards: list[dict], gold_cards: list[dict]) -> dict:
    """Evaluate an entire set of predicted cards against gold cards matched by card_id or doc_id."""
    gold_by_id = {}
    for g in gold_cards:
        gid = g.get("card_id") or g.get("doc_id")
        if gid:
            gold_by_id[gid] = g

    scores = []
    matched_count = 0

    for p in pred_cards:
        pid = p.get("card_id") or p.get("doc_id")
        if pid in gold_by_id:
            matched_count += 1
            scores.append(evaluate_card_pair(p, gold_by_id[pid]))

    if not scores:
        return {"error": "no_matching_ids", "pred_count": len(pred_cards), "gold_count": len(gold_cards)}

    n = len(scores)
    return {
        "evaluated_pairs": n,
        "mean_effect_exact_match": round(sum(s["effect_exact_match"] for s in scores) / n, 4),
        "mean_effect_f1": round(sum(s["effect_f1"] for s in scores) / n, 4),
        "mean_action_f1": round(sum(s["action_f1"] for s in scores) / n, 4),
        "mean_state_change_f1": round(sum(s["state_change_f1"] for s in scores) / n, 4),
        "mean_phenomenon_f1": round(sum(s["phenomenon_f1"] for s in scores) / n, 4),
        "mean_quantities_f1": round(sum(s["quantities_f1"] for s in scores) / n, 4),
        "overall_macro_f1": round(sum(s["macro_f1"] for s in scores) / n, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate predicted cards against gold cards.")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSON or JSONL")
    parser.add_argument("--gold", required=True, help="Path to gold cards JSON or JSONL")
    args = parser.parse_args()

    def load_cards(path_str):
        cards = []
        path = Path(path_str)
        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        with open(path) as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    cards.append(item.get("card", item))
        return cards

    preds = load_cards(args.predictions)
    golds = load_cards(args.gold)

    results = evaluate_corpus(preds, golds)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
