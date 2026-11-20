"""Pass rate vs generated tokens per run for the 72B allocation arms (docs/v10/results_72b)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1] / "results_72b"
rows = {}
for d in (R, R / "alloc"):
    s = json.loads((d / "summary_all.json").read_text())
    for k, v in s.items():
        if k in {"L3", "BoN8", "B0", "A24x1", "A8x3", "A3x8", "V10"}:
            rows[k] = (v["tokens_mean_per_run"], v["pass_rate"], v["wilson_ci"])
lab = {"B0": "B0 (1×0)", "L3": "L3 (1×3)", "BoN8": "BoN8 (8×0)", "A24x1": "24×0", "A8x3": "8×2", "A3x8": "3×7", "V10": "V10 (8×3)"}
fig, ax = plt.subplots(figsize=(6.2, 3.6))
for k, (t, p, ci) in rows.items():
    rep = k in {"L3", "A8x3", "A3x8", "V10"}
    c = "#0072B2" if rep else "#E69F00"
    ax.errorbar(t, p * 100, yerr=[[p * 100 - ci[0] * 100], [ci[1] * 100 - p * 100]], fmt="o", color=c, capsize=3)
    ax.annotate(lab[k], (t, p * 100), textcoords="offset points", xytext=(6, 4), fontsize=8)
ax.axhline(67.7, ls="--", lw=1, color="#555555"); ax.text(60, 69, "optimiser only (no LLM) 67.7%", fontsize=8, color="#555555")
ax.set_xscale("log"); ax.set_xlabel("generated tokens per run (log scale)"); ax.set_ylabel("hidden-eval pass rate (%)")
ax.set_ylim(0, 85); ax.grid(alpha=0.3)
ax.plot([], [], "o", color="#0072B2", label="with screen repair"); ax.plot([], [], "o", color="#E69F00", label="no repair (sampling only)")
ax.legend(fontsize=8, loc="lower right"); fig.tight_layout()
fig.savefig(Path(__file__).parent / "fig" / "fig_alloc.png", dpi=200)
