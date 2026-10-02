"""Report figures derived only from saved split metrics; no model fitting."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "outputs/split_metrics.csv").open() as handle:
    rows = [r for r in csv.DictReader(handle) if r["design"] == "repeated_host_split"]
assert len(rows) == 50
with (ROOT / "outputs/paired_summary.csv").open() as handle:
    summary = {r["metric"]: r for r in csv.DictReader(handle)}
navy, teal, orange, grey = "#142C45", "#007F7D", "#C66A34", "#667788"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": navy,
                     "axes.labelcolor": navy, "xtick.color": grey, "ytick.color": grey,
                     "svg.fonttype": "none", "savefig.facecolor": "white"})
fig, axes = plt.subplots(1, 3, figsize=(12.8, 5.3))
fig.subplots_adjust(left=.065, right=.98, top=.67, bottom=.28, wspace=.33)
fig.text(.065, .945, "Does the model improve on simple group rates?", fontsize=22, weight="bold")
fig.text(.065, .875, "50 paired host splits · same test listings and shortlist quota in each split", fontsize=12, color=grey)
specs = [
    ("precision_difference_pp", "Shortlist target rate", "+.1f", "Logistic − baseline (percentage points)", "higher"),
    ("auc_difference", "Ranking quality (AUC)", "+.3f", "Logistic − baseline", "higher"),
    ("brier_difference", "Probability error (Brier)", "+.4f", "Logistic − baseline", "lower"),
]
for ax, (metric, title, number_format, xlabel, direction) in zip(axes, specs):
    values = np.array([float(r[metric]) for r in rows])
    row = summary[metric]
    # Deterministic vertical placement separates points. Height has no statistical meaning.
    offsets = .16 + .12 * np.sin(np.arange(50) * 2.399963)
    better = values > 0 if direction == "higher" else values < 0
    ax.scatter(values, offsets, c=[teal if b else orange for b in better], s=28, alpha=.78, linewidths=.45, edgecolors="white", zorder=3)
    low, high = float(row["p05_difference"]), float(row["p95_difference"])
    mean = float(row["mean_difference"])
    headline = format(mean, number_format).replace("-", "−")
    if metric == "precision_difference_pp":
        headline += " pp"
    ax.plot([low, high], [-.1, -.1], color=navy, lw=3, solid_capstyle="round")
    ax.scatter([mean], [-.1], marker="D", color=navy, s=45, zorder=4)
    ax.axvline(0, color=grey, lw=1, ls=(0, (3, 3)))
    ax.set_ylim(-.25, .4)
    ax.set_yticks([])
    ax.set_xlabel(xlabel, labelpad=10, fontsize=9)
    ax.set_title(title, loc="left", fontsize=13, weight="bold", pad=36)
    ax.text(0, 1.05, f"{headline} mean · better in {row['better_splits']}/50", transform=ax.transAxes, fontsize=11, color=teal)
    ax.text(0, -.33, "Higher is better →" if direction == "higher" else "← Lower is better", transform=ax.transAxes, color=grey, fontsize=9)
    for side in ["top", "left", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#CED7DF")
    ax.tick_params(axis="x", labelsize=9, length=3)
fig.text(.065, .095, "Each dot is one split. Diamond = mean; line = 5th–95th percentiles of paired differences (not a confidence interval).", fontsize=9, color=grey)
fig.text(.065, .048, "Exploratory retrospective comparison. Splits overlap; this does not validate future success or profit. Source: outputs/split_metrics.csv.", fontsize=9, color=grey)
out = ROOT / "figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "paired_model_gain.png", dpi=220)
fig.savefig(out / "paired_model_gain.svg")
plt.close(fig)
print("Saved figures/paired_model_gain.png and .svg")
