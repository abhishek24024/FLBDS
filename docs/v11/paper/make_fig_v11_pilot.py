import json, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src))
arms = ["IMG", "NAME", "IMG+NAME"]
cols = {"IMG": "#0072B2", "NAME": "#C2560A", "IMG+NAME": "#00795A"}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.45, 1]})
# panel a: proportions and 0-2 mechanism score normalised? keep separate axis groups
mets = [("organism_correct", "organism\nidentified", 1), ("mechanism_score", "mechanism\nscore / 2", 2),
        ("rediscovery_hit1", "canonical app.\n#1", 1), ("rediscovery_hit5", "canonical app.\nin top 5", 1),
        ("hallucination", "hallucination", 1), ("specificity", "specificity / 5", 5)]
x = np.arange(len(mets)); w = 0.26
for i, a in enumerate(arms):
    m = [d["per_arm"][k][a]["mean"] / s for k, _, s in mets]
    lo = [d["per_arm"][k][a]["ci"][0] / s for k, _, s in mets]
    hi = [d["per_arm"][k][a]["ci"][1] / s for k, _, s in mets]
    err = np.array([np.array(m) - np.array(lo), np.array(hi) - np.array(m)])
    a1.bar(x + (i - 1) * w, m, w, yerr=err, capsize=2.5, color=cols[a], label=a, edgecolor="white", linewidth=0.5,
           error_kw={"elinewidth": 0.9, "ecolor": "#333"})
a1.set_xticks(x); a1.set_xticklabels([l for _, l, _ in mets], fontsize=8.5)
a1.set_ylim(0, 1.08); a1.set_ylabel("mean over organisms (scaled to 0–1)", fontsize=9)
a1.set_title("(a) E1 perception and rediscovery by input arm (n = 22 organisms)", fontsize=10, loc="left")
a1.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper right", bbox_to_anchor=(1.0, 1.0))
a1.spines[["top", "right"]].set_visible(False); a1.tick_params(axis="y", labelsize=8.5)
# panel b: pairwise
crit = ["novelty", "soundness", "implementability", "overall"]
x2 = np.arange(len(crit))
for i, a in enumerate(arms):
    pw = d["pairwise_bio_vs_nobio"][a]
    m = [pw[c]["mean_score(-1..1)"] for c in crit]
    lo = [pw[c]["ci"][0] for c in crit]; hi = [pw[c]["ci"][1] for c in crit]
    err = np.array([np.array(m) - np.array(lo), np.array(hi) - np.array(m)])
    a2.bar(x2 + (i - 1) * w, m, w, yerr=err, capsize=2.5, color=cols[a], label=a + " source", edgecolor="white",
           linewidth=0.5, error_kw={"elinewidth": 0.9, "ecolor": "#333"})
oc = d["judge_order_consistency"]
a2.set_xticks(x2); lab={"implementability":"implement-\nability"}
a2.set_xticklabels([f"{lab.get(c,c)}\norder cons. {oc[c]:.2f}" for c in crit], fontsize=7.8)
a2.axhline(0, color="#333", lw=0.8); a2.set_ylim(-0.85, 0.75)
a2.set_ylabel("pairwise score (+1 = BIO preferred)", fontsize=9)
a2.set_title("(b) E2 BIO vs NOBIO blueprints, same application", fontsize=10, loc="left")
a2.text(0.02, 0.97, "BIO better ↑", transform=a2.transAxes, fontsize=8, va="top", color="#555")
a2.text(0.02, 0.03, "NOBIO better ↓", transform=a2.transAxes, fontsize=8, va="bottom", color="#555")
a2.legend(frameon=False, fontsize=8, loc="upper right")
a2.spines[["top", "right"]].set_visible(False); a2.tick_params(axis="y", labelsize=8.5)
fig.tight_layout(); fig.savefig(out, dpi=170)
