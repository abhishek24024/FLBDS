#!/usr/bin/env python3
"""docs/v10/paper/make_figures.py
Figures for the FLBDS V10 research-proposal paper (PNG, dpi 200) written to docs/v10/paper/fig/.

    python3 docs/v10/paper/make_figures.py            # from the repo root (or anywhere)

Inputs (all read-only; no numbers are typed into this script except where a source file stores them only
as prose, noted inline):
    docs/v10/e0_results/e0_nontrivial.json   -> fig_e0.png
    flbds/v10/relaxation_audit.json          -> fig_relax.png
    flbds/v10/instances_v10.json             -> fig_generator.png (config, acceptance_stats and the
                                                per-instance `trivial_pass_rate` field only)
    docs/v10/results_72b/, docs/v10/results/ -> fig_v10_results.png (OPTIONAL; each skipped silently if absent).
                                                If both exist the two models are drawn side by side
                                                (RESULT_DIRS: 72B primary, 7B hatched).

Expected format of each results directory (written by scripts/run_v10.py and scripts/analyse_v10.py):
    summary_all.json        {COND: summary}     where summary = flbds.v10.runner.summarise(records, COND):
                              {"condition", "n_runs", "eval_passes", "pass_rate", "wilson_ci": [lo, hi],
                               "screen_passes", "screen_pass_rate", "screen_pass_eval_fail",
                               "screen_fail_eval_pass", "template_choice_errors", "schema_failure_final",
                               "parse_failures_total", "tokens_total", "tokens_mean_per_run",
                               "per_family": {FAMILY: {"n", "pass_rate"}}, ...}
    <COND>_summary.json     one summary each (used if summary_all.json is missing; any file matching
                            summary*.json or *_summary.json is merged)
    <COND>.jsonl            optional per-run records (keys used: instance_id, family, eval_pass). If present,
                            the per-condition CI is an instance-level percentile bootstrap (instances
                            resampled, seeds averaged within instance) instead of the run-level Wilson CI.
    analysis.json           optional output of scripts/analyse_v10.py:
                              {"per_condition": {...}, "pairs": [paired_compare(...) results with
                               "a", "b", "mean_diff", "ci95_bootstrap", "p_sign_flip", "p_holm"?]}
                            If present, a third panel shows the paired instance-level differences.
Missing keys are tolerated; anything unusable is skipped rather than raising.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FIG = HERE / "fig"
DPI = 200

# Okabe-Ito colour-blind-safe palette, used with the same meaning in every figure.
OI = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "grey": "#8C8C8C",
    "lightgrey": "#D9D9D9",
}
COND_COLOUR = {
    "B0": OI["grey"],
    "Screen": OI["blue"],
    "L3": OI["blue"],
    "Oracle": OI["sky"],
    "B3": OI["orange"],
    "BoN8": OI["green"],
    "V10": OI["green"],
    "OPT": OI["vermillion"],
    "OPTONLY": OI["black"],
    "L3_BIOMATCH": OI["purple"],
    "L3_BIOMISMATCH": OI["yellow"],
    "A24x1": OI["sky"],
    "A8x3": OI["green"],
    "A3x8": OI["orange"],
}
FAMILY_LABEL = {
    "F_PCM": "PCM\n(TPL_02)",
    "F_HX": "HX\n(TPL_08)",
    "F_RAD": "RAD\n(TPL_09)",
    "F_MEM": "MEM\n(TPL_10)",
}
FAMILY_ORDER = ["F_PCM", "F_HX", "F_RAD", "F_MEM"]
COND_ORDER = [
    "B0",
    "L3",
    "BoN8",
    "V10",
    "OPT",
    "OPTONLY",
    "L3_BIOMATCH",
    "L3_BIOMISMATCH",
    "A24x1",
    "A8x3",
    "A3x8",
]

plt.rcParams.update(
    {
        "font.family": "DejaVu Serif",
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    }
)


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, c - h), min(1.0, c + h)


def frac(s: str) -> tuple[int, int]:
    k, n = s.split("/")
    return int(k), int(n)


def save(fig: plt.Figure, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=DPI)
    plt.close(fig)
    print(f"wrote {FIG / name}")


# ----------------------------------------------------------------------------- fig_e0
def fig_e0() -> None:
    src = REPO / "docs/v10/e0_results/e0_nontrivial.json"
    data = json.loads(src.read_text())
    conds = ["B0", "Screen", "Oracle", "B3"]
    groups = [
        (
            "trivial_cases_pass",
            "Trivially passable cases\n(blank design passes; 5 cases)",
        ),
        ("nontrivial_cases_pass", "Non-trivial cases\n(7 cases)"),
    ]
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    width = 0.19
    for gi, (key, _) in enumerate(groups):
        for ci, c in enumerate(conds):
            k, n = frac(data[c][key])
            lo, hi = wilson(k, n)
            x = gi + (ci - 1.5) * width
            p = k / n
            ax.bar(
                x,
                p,
                width * 0.92,
                color=COND_COLOUR[c],
                edgecolor="black",
                linewidth=0.5,
                label=c if gi == 0 else None,
            )
            ax.errorbar(
                x,
                p,
                yerr=[[p - lo], [hi - p]],
                fmt="none",
                ecolor="black",
                elinewidth=0.8,
                capsize=2.2,
            )
            ax.text(x, hi + 0.02, f"{k}/{n}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[1] for g in groups])
    ax.set_ylabel("Hidden-eval pass rate (runs)")
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    ax.grid(axis="y", color=OI["lightgrey"], linewidth=0.5)
    ax.set_axisbelow(True)
    save(fig, "fig_e0.png")


# ----------------------------------------------------------------------------- fig_relax
RELAX_CATS = [
    ("both_pass", "both pass", OI["green"]),
    ("both_fail", "both fail", OI["lightgrey"]),
    (
        "false_rejection_screen_fail_eval_pass",
        "false rejection (screen fail, eval pass)",
        OI["vermillion"],
    ),
    (
        "false_assurance_screen_pass_eval_fail",
        "false assurance (screen pass, eval fail)",
        OI["purple"],
    ),
]


def fig_relax() -> None:
    src = REPO / "flbds/v10/relaxation_audit.json"
    data = json.loads(src.read_text())["families"]
    fams = [f for f in FAMILY_ORDER if f in data]
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    x = np.arange(len(fams))
    bottom = np.zeros(len(fams))
    for key, label, col in RELAX_CATS:
        vals = np.array([data[f]["total"][key] for f in fams], dtype=float)
        ax.bar(
            x,
            vals,
            0.6,
            bottom=bottom,
            color=col,
            edgecolor="black",
            linewidth=0.5,
            label=label,
        )
        bottom += vals
    for xi, f in enumerate(fams):
        t = data[f]["total"]
        ax.text(xi, bottom[xi] + 25, f"FR {t['false_rejection_screen_fail_eval_pass']} · "
                f"FA {t['false_assurance_screen_pass_eval_fail']}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([FAMILY_LABEL[f] for f in fams])
    ax.set_ylabel("Designs per family")
    ax.set_ylim(0, max(bottom) * 1.09)
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.27))
    ax.grid(axis="y", color=OI["lightgrey"], linewidth=0.5)
    ax.set_axisbelow(True)
    save(fig, "fig_relax.png")


# ----------------------------------------------------------------------------- fig_generator
def fig_generator() -> None:
    src = REPO / "flbds/v10/instances_v10.json"
    raw = json.loads(src.read_text())
    stats = raw["acceptance_stats"]
    thr = raw["config"]["max_trivial_rate"]
    fams = [f for f in FAMILY_ORDER if f in stats]
    fig, (a1, a2) = plt.subplots(
        1, 2, figsize=(6.5, 2.7), gridspec_kw={"width_ratios": [1.15, 1]}
    )
    x = np.arange(len(fams))
    w = 0.25
    series = [
        ("candidates", "candidates drawn", OI["lightgrey"]),
        ("kept", "kept (certified, not too easy)", OI["blue"]),
        ("too_easy", "rejected: too easy", OI["orange"]),
    ]
    for i, (key, lab, col) in enumerate(series):
        vals = [stats[f][key] for f in fams]
        a1.bar(
            x + (i - 1) * w,
            vals,
            w * 0.92,
            color=col,
            edgecolor="black",
            linewidth=0.5,
            label=lab,
        )
        for xi, v in zip(x, vals):
            a1.text(
                xi + (i - 1) * w, v + 0.5, str(v), ha="center", va="bottom", fontsize=7
            )
    a1.set_xticks(x)
    a1.set_xticklabels([FAMILY_LABEL[f] for f in fams])
    a1.set_ylabel("Instances")
    a1.set_ylim(0, max(stats[f]["candidates"] for f in fams) * 1.25)
    a1.legend(frameon=False, loc="upper left", fontsize=7.5)
    a1.set_title(
        "(a) Generator acceptance (seed %d)" % raw["config"]["seed"], loc="left"
    )

    rng = np.random.default_rng(0)
    for xi, f in enumerate(fams):
        rates = [i["trivial_pass_rate"] for i in raw["instances"] if i["family"] == f]
        jitter = rng.uniform(-0.12, 0.12, len(rates))
        a2.scatter(
            np.full(len(rates), xi) + jitter,
            rates,
            s=12,
            color=OI["blue"],
            alpha=0.75,
            edgecolor="none",
            zorder=3,
        )
        m = stats[f]["mean_trivial_rate_kept"]
        a2.plot([xi - 0.25, xi + 0.25], [m, m], color="black", linewidth=1.4, zorder=4)
        a2.text(xi + 0.27, m, f"{m:.2f}", va="center", fontsize=7)
    a2.axhline(thr, color=OI["vermillion"], linestyle="--", linewidth=1)
    a2.text(
        len(fams) - 0.5,
        thr + 0.015,
        f"rejection threshold {thr:.1f}",
        ha="right",
        va="bottom",
        fontsize=7,
        color=OI["vermillion"],
    )
    a2.set_xticks(range(len(fams)))
    a2.set_xticklabels([FAMILY_LABEL[f] for f in fams])
    a2.set_ylim(0, 0.6)
    a2.set_ylabel("Random-design pass rate\n(200 uniform designs)")
    a2.set_title("(b) Trivial-pass rate of kept instances", loc="left")
    for a in (a1, a2):
        a.grid(axis="y", color=OI["lightgrey"], linewidth=0.5)
        a.set_axisbelow(True)
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig_generator.png")


# ----------------------------------------------------------------------------- fig_v10_results (optional)
def _load_results(
    rdir: Path,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, Any] | None]:
    summaries: dict[str, Any] = {}
    p_all = rdir / "summary_all.json"
    if p_all.exists():
        try:
            obj = json.loads(p_all.read_text())
            if isinstance(obj, dict):
                summaries.update({k: v for k, v in obj.items() if isinstance(v, dict)})
        except Exception:  # noqa: BLE001
            pass
    for p in sorted(set(rdir.glob("*_summary.json")) | set(rdir.glob("summary*.json"))):
        if p.name == "summary_all.json":
            continue
        try:
            obj = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict) and "condition" in obj:
            summaries.setdefault(obj["condition"], obj)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict) and "n_runs" in v:
                    summaries.setdefault(k, v)
    records: dict[str, list[dict[str, Any]]] = {}
    for p in rdir.glob("*.jsonl"):
        recs = []
        for line in p.read_text().splitlines():
            try:
                recs.append(json.loads(line))
            except Exception:  # noqa: BLE001
                continue
        if recs:
            records[p.stem] = recs
    analysis = None
    if (rdir / "analysis.json").exists():
        try:
            analysis = json.loads((rdir / "analysis.json").read_text())
        except Exception:  # noqa: BLE001
            analysis = None
    return summaries, records, analysis


def _instance_bootstrap(
    recs: list[dict[str, Any]], n_boot: int = 10_000
) -> tuple[float, float, float] | None:
    acc: dict[str, list[float]] = {}
    for r in recs:
        if "instance_id" in r and ("eval_pass" in r or "passed" in r):
            acc.setdefault(r["instance_id"], []).append(
                float(bool(r.get("eval_pass", r.get("passed"))))
            )
    if len(acc) < 2:
        return None
    v = np.array([np.mean(x) for x in acc.values()])
    rng = np.random.default_rng(0)
    means = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    return (
        float(v.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


RESULT_DIRS = [  # (label, directory relative to the repo); first existing = primary model
    ("Qwen2.5-72B", "docs/v10/results_72b"),
    ("Qwen2.5-7B", "docs/v10/results"),
]
NO_LLM_CONDS = {"OPTONLY"}  # identical across models (no LLM); a reused run is not "partial"
MODEL_STYLE = [  # (hatch, alpha, marker) per model, in RESULT_DIRS order of the models found
    ("", 1.0, "o"),
    ("////", 0.45, "s"),
]


def _condition_rows(summaries: dict[str, Any], records: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """-> {cond: {p, lo, hi, k, n, per_family, ci}} using an instance bootstrap if records exist, else Wilson."""
    out: dict[str, dict[str, Any]] = {}
    for c in sorted(set(summaries) | set(records)):
        s = summaries.get(c, {})
        n, k = s.get("n_runs"), s.get("eval_passes")
        if (not isinstance(n, int) or not isinstance(k, int)) and c in records:
            n = len(records[c])
            k = sum(bool(r.get("eval_pass", r.get("passed"))) for r in records[c])
        if not isinstance(n, int) or not isinstance(k, int) or n <= 0:
            continue
        boot = _instance_bootstrap(records[c]) if c in records else None
        if boot is not None:
            p, lo, hi = boot
            ci = "boot"
        else:
            p = k / n
            w = s.get("wilson_ci")
            lo, hi = (w[0], w[1]) if isinstance(w, list) and len(w) == 2 else wilson(k, n)
            ci = "wilson"
        per_fam = s.get("per_family") or {}
        if not per_fam and c in records:
            tmp: dict[str, list[float]] = {}
            for r in records[c]:
                tmp.setdefault(r.get("family", "?"), []).append(float(bool(r.get("eval_pass", r.get("passed")))))
            per_fam = {f: {"n": len(v), "pass_rate": float(np.mean(v))} for f, v in tmp.items()}
        out[c] = {"p": p, "lo": lo, "hi": hi, "k": k, "n": n, "per_family": per_fam, "ci": ci}
    return out


def fig_v10_results() -> None:
    models = []
    for label, rel in RESULT_DIRS:
        rdir = REPO / rel
        if not rdir.is_dir():
            continue
        summaries, records, analysis = _load_results(rdir)
        rows = _condition_rows(summaries, records)
        if not rows:
            continue
        pairs = [r for r in (analysis or {}).get("pairs", []) if isinstance(r, dict) and "mean_diff" in r]
        models.append({"label": label, "rows": rows, "pairs": pairs})
    if not models:
        return
    models = models[: len(MODEL_STYLE)]
    nm = len(models)
    conds = [c for c in COND_ORDER if any(c in m["rows"] for m in models)]
    conds += sorted({c for m in models for c in m["rows"]} - set(conds))
    pair_keys: list[tuple[str, str]] = []
    for m in models:
        for r in m["pairs"]:
            key = (str(r.get("a", "?")), str(r.get("b", "?")))
            if key not in pair_keys:
                pair_keys.append(key)
    has_pairs = bool(pair_keys)

    heights = [1.25, 0.8] + ([0.25 + 0.17 * len(pair_keys)] if has_pairs else [])
    fig = plt.figure(figsize=(6.8, 2.15 * sum(heights) + 0.7))
    gs = fig.add_gridspec(len(heights), nm, height_ratios=heights, left=0.24, right=0.97, top=0.965,
                          bottom=0.08, hspace=0.62, wspace=0.3)
    partial_any = False

    # (a) per condition, all models
    a1 = fig.add_subplot(gs[0, :])
    bh = 0.8 / nm
    y = np.arange(len(conds))[::-1]
    for mi, m in enumerate(models):
        hatch, alpha, _ = MODEL_STYLE[mi]
        n_full = max(r["n"] for r in m["rows"].values())
        for yi, c in zip(y, conds):
            r = m["rows"].get(c)
            if r is None:
                continue
            yy = yi + (nm - 1) / 2 * bh - mi * bh
            a1.barh(yy, r["p"], bh * 0.9, color=COND_COLOUR.get(c, OI["grey"]), alpha=alpha, hatch=hatch,
                    edgecolor="black", linewidth=0.5)
            a1.errorbar(r["p"], yy, xerr=[[r["p"] - r["lo"]], [r["hi"] - r["p"]]], fmt="none", ecolor="black",
                        elinewidth=0.7, capsize=1.6)
            star = " *" if (r["n"] < n_full and c not in NO_LLM_CONDS) else ""
            partial_any |= bool(star)
            a1.text(min(r["hi"] + 0.015, 0.93), yy, f"{r['k']}/{r['n']}{star}", va="center", fontsize=6.8)
    a1.set_yticks(y)
    a1.set_yticklabels(conds)
    a1.set_xlim(0, 1.0)
    a1.set_xlabel("Hidden-eval pass rate (95% CI)")
    a1.set_title("(a) Per condition", loc="left")
    a1.grid(axis="x", color=OI["lightgrey"], linewidth=0.5)
    a1.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=OI["grey"], alpha=MODEL_STYLE[i][1], hatch=MODEL_STYLE[i][0],
                             edgecolor="black", linewidth=0.5) for i in range(nm)]
    a1.legend(handles, [m["label"] for m in models], frameon=False, loc="lower right", fontsize=7.5)

    # (b..) per family, one panel per model
    fam_axes = []
    for mi, m in enumerate(models):
        ax = fig.add_subplot(gs[1, mi])
        fam_axes.append(ax)
        hatch, alpha, _ = MODEL_STYLE[mi]
        mconds = [c for c in conds if c in m["rows"]]
        fams = [f for f in FAMILY_ORDER if any(f in m["rows"][c]["per_family"] for c in mconds)]
        w = 0.8 / max(1, len(mconds))
        for i, c in enumerate(mconds):
            pf = m["rows"][c]["per_family"]
            vals = [pf.get(f, {}).get("pass_rate", np.nan) for f in fams]
            ax.bar(np.arange(len(fams)) + (i - (len(mconds) - 1) / 2) * w, vals, w * 0.95,
                   color=COND_COLOUR.get(c, OI["grey"]), alpha=alpha, hatch=hatch, edgecolor="black",
                   linewidth=0.3, label=c)
        ax.set_xticks(range(len(fams)))
        ax.set_xticklabels([FAMILY_LABEL.get(f, f).split("\n")[0] for f in fams])
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("Pass rate")
        ax.set_title(f"({chr(98 + mi)}) Per family, {m['label']}", loc="left")
        ax.grid(axis="y", color=OI["lightgrey"], linewidth=0.5)
        ax.set_axisbelow(True)
    cond_handles = [plt.Rectangle((0, 0), 1, 1, facecolor=COND_COLOUR.get(c, OI["grey"]), edgecolor="black",
                                  linewidth=0.4) for c in conds]
    y0 = min(ax.get_position().y0 for ax in fam_axes)
    fig.legend(cond_handles, conds, frameon=False, ncol=min(4, len(conds)), fontsize=6.8, loc="upper center",
               bbox_to_anchor=(0.6, y0 - 0.035))

    # (last) paired contrasts, all models
    if has_pairs:
        ax = fig.add_subplot(gs[2, :])
        yp = np.arange(len(pair_keys))[::-1]
        off = 0.36 / max(1, nm - 1) if nm > 1 else 0.0
        for mi, m in enumerate(models):
            _, _, marker = MODEL_STYLE[mi]
            n_full = max((r.get("n_instances", 0) for r in m["pairs"]), default=0)
            lookup = {(str(r.get("a")), str(r.get("b"))): r for r in m["pairs"]}
            for yi, key in zip(yp, pair_keys):
                r = lookup.get(key)
                if r is None:
                    continue
                yy = yi + (nm - 1) / 2 * off - mi * off
                d = r["mean_diff"]
                lo, hi = (r.get("ci95_bootstrap") or [d, d])[:2]
                ax.errorbar(d, yy, xerr=[[d - lo], [hi - d]], fmt=marker, color=OI["blue"] if mi == 0 else OI["grey"],
                            ms=3.6, ecolor="black", elinewidth=0.7, capsize=1.6)
                ph, ps = r.get("p_holm"), r.get("p_sign_flip")
                if isinstance(ph, (int, float)) and not math.isnan(ph):
                    t = f"Holm p={ph:.2g}"
                elif isinstance(ps, (int, float)) and not math.isnan(ps):
                    t = f"p={ps:.2g} (expl.)"
                else:
                    t = ""
                if r.get("n_instances", 0) < n_full:
                    t += f" *N={r.get('n_instances')}"
                    partial_any = True
                ax.text(1.0, yy, f"{m['label'].split('-')[-1]}: {t}", va="center", ha="right", fontsize=6.3,
                        transform=ax.get_yaxis_transform())
        lo_all = [min((r.get("ci95_bootstrap") or [r["mean_diff"]] * 2)[0], r["mean_diff"]) for m in models for r in m["pairs"]]
        hi_all = [max((r.get("ci95_bootstrap") or [r["mean_diff"]] * 2)[1], r["mean_diff"]) for m in models for r in m["pairs"]]
        xmin, xmax = min(lo_all + [0.0]) - 0.02, max(hi_all + [0.0]) + 0.02
        ax.set_xlim(xmin, xmax + 0.42 * (xmax - xmin))
        ax.axvline(0, color="black", linewidth=0.7)
        ax.set_yticks(yp)
        ax.set_yticklabels([f"{a} − {b}" for a, b in pair_keys], fontsize=7)
        ax.set_ylim(-0.6, len(pair_keys) - 0.4)
        ax.set_xlabel("Paired per-instance difference in pass rate (instance bootstrap 95% CI)")
        ax.set_title("(" + chr(98 + nm) + ") Paired contrasts (" + ", ".join(
            f"{'filled circle' if i == 0 else 'grey square'} = {m['label']}" for i, m in enumerate(models)) + ")",
            loc="left")
        ax.grid(axis="x", color=OI["lightgrey"], linewidth=0.5)
    if partial_any:
        fig.text(0.01, 0.003, "* partial: fewer runs/instances than the other conditions of that model "
                 "(run in progress); not comparable.", fontsize=7, ha="left", va="bottom")
    save(fig, "fig_v10_results.png")


def main() -> None:
    fig_e0()
    fig_relax()
    fig_generator()
    fig_v10_results()


if __name__ == "__main__":
    main()
