"""
build_figures.py
Generates all OSF supplement figures from the aggregate CSVs.
Writes to osf_supplement/figures/.

Figures:
  fig1_demographics.png      — participant demographics by condition
  fig2_accuracy_heatmap.png  — per-clip accuracy heatmap (condition × attribute)
  fig3_confidence_heatmap.png— per-clip mean confidence heatmap
"""

import csv, json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, "figures")
os.makedirs(OUT, exist_ok=True)

# ── shared palette ────────────────────────────────────────────────────────────
C_UB = "#4e79a7"   # upper_body
C_FB = "#f28e2b"   # full_body
COND_LABELS = {"upper_body": "Upper body", "full_body": "Full body"}
ATTR_ORDER   = ["gender", "age", "height", "weight", "ethnicity"]
ATTR_LABELS  = {"gender": "Gender", "age": "Age", "height": "Height",
                "weight": "Weight", "ethnicity": "Ethnicity"}
# chance baselines (from the full Nymeria demographic distribution; see paper)
CHANCE       = {"gender": 0.50, "age": 0.17, "height": 0.22,
                "weight": 0.18, "ethnicity": 0.28}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: read csv
# ─────────────────────────────────────────────────────────────────────────────
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ═════════════════════════════════════════════════════════════════════════════
# Figure 1 — Demographics
# ═════════════════════════════════════════════════════════════════════════════
def fig_demographics():
    rows = read_csv(os.path.join(BASE, "demographics_aggregate.csv"))

    attrs = ["age", "gender", "ethnicity", "mocap_experience"]
    attr_titles = {
        "age": "Age",
        "gender": "Gender",
        "ethnicity": "Ethnicity",
        "mocap_experience": "Mocap experience",
    }

    conditions = ["upper_body", "full_body"]
    colors     = [C_UB, C_FB]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for ax, attr in zip(axes, attrs):
        # collect all categories in order of first appearance
        cats = []
        for r in rows:
            if r["attribute"] == attr and r["category"] not in cats:
                cats.append(r["category"])

        x = np.arange(len(cats))
        width = 0.35
        ymax = 0.0

        for i, (cond, col) in enumerate(zip(conditions, colors)):
            heights = []
            for cat in cats:
                match = [r for r in rows if r["attribute"] == attr
                         and r["condition"] == cond and r["category"] == cat]
                heights.append(float(match[0]["percent"]) if match else 0.0)
            ax.bar(x + (i - 0.5) * width, heights, width,
                   color=col, alpha=0.85, edgecolor="white")
            ymax = max(ymax, max(heights))

        ax.set_title(attr_titles[attr], fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("% of participants", fontsize=9)
        ax.set_ylim(0, max(10, math.ceil(ymax * 1.1 / 10) * 10))
        ax.spines[["top", "right"]].set_visible(False)

    handles = [
        mpatches.Patch(facecolor=C_UB, alpha=0.85, label=COND_LABELS["upper_body"]),
        mpatches.Patch(facecolor=C_FB, alpha=0.85, label=COND_LABELS["full_body"]),
    ]
    fig.legend(handles=handles, loc="upper right", fontsize=8, ncol=2,
               bbox_to_anchor=(0.99, 1.0))

    fig.suptitle("Participant Demographics by Condition", fontsize=13, fontweight="bold",
                 x=0.02, ha="left", y=1.01)
    fig.tight_layout()
    path = os.path.join(OUT, "fig1_demographics.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 2 — Accuracy heatmap per clip × attribute, side by side by condition
# ═════════════════════════════════════════════════════════════════════════════
def fig_accuracy_heatmap():
    rows = read_csv(os.path.join(BASE, "ratings_per_clip.csv"))

    clips = sorted(set(r["clip_id"] for r in rows))
    # short label: first word of nymeria_id
    clip_labels = [c.replace(".mp4", "").rsplit("_", 2)[0].replace("_", " ") for c in clips]

    cond_order = ["upper_body", "full_body"]
    cmap = LinearSegmentedColormap.from_list("acc", ["#f7fbff", "#08306b"], N=256)

    fig, axes = plt.subplots(1, 2, figsize=(13, 7), sharey=True)

    for ax, cond in zip(axes, cond_order):
        matrix = np.full((len(clips), len(ATTR_ORDER)), np.nan)
        for i, clip in enumerate(clips):
            for j, attr in enumerate(ATTR_ORDER):
                match = [r for r in rows
                         if r["clip_id"] == clip and r["condition"] == cond
                         and r["attribute"] == attr]
                if match:
                    try:
                        matrix[i, j] = float(match[0]["accuracy"])
                    except ValueError:
                        pass

        im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(ATTR_ORDER)))
        ax.set_xticklabels([f"{ATTR_LABELS[a]}\n(chance {CHANCE[a]:.2f})" for a in ATTR_ORDER],
                           fontsize=8)
        ax.set_yticks(range(len(clips)))
        ax.set_yticklabels(clip_labels, fontsize=7)
        ax.set_title(COND_LABELS[cond], fontsize=11, fontweight="bold")

        # annotate cells
        for i in range(len(clips)):
            for j in range(len(ATTR_ORDER)):
                val = matrix[i, j]
                if not np.isnan(val):
                    txt = f"{val:.2f}"
                    color = "white" if val > 0.6 else "black"
                    ax.text(j, i, txt, ha="center", va="center",
                            fontsize=6, color=color)

        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02).set_label("Accuracy", fontsize=8)

    axes[1].set_ylabel("")
    fig.suptitle("Observer Accuracy per Clip and Attribute", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    path = os.path.join(OUT, "fig2_accuracy_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 3 — Mean confidence heatmap
# ═════════════════════════════════════════════════════════════════════════════
def fig_confidence_heatmap():
    rows = read_csv(os.path.join(BASE, "ratings_per_clip.csv"))

    clips = sorted(set(r["clip_id"] for r in rows))
    clip_labels = [c.replace(".mp4", "").rsplit("_", 2)[0].replace("_", " ") for c in clips]
    cond_order = ["upper_body", "full_body"]
    cmap = LinearSegmentedColormap.from_list("conf", ["#fff5eb", "#7f2704"], N=256)

    fig, axes = plt.subplots(1, 2, figsize=(13, 7), sharey=True)

    for ax, cond in zip(axes, cond_order):
        matrix = np.full((len(clips), len(ATTR_ORDER)), np.nan)
        for i, clip in enumerate(clips):
            for j, attr in enumerate(ATTR_ORDER):
                match = [r for r in rows
                         if r["clip_id"] == clip and r["condition"] == cond
                         and r["attribute"] == attr]
                if match and match[0]["mean_confidence"] != "":
                    try:
                        matrix[i, j] = float(match[0]["mean_confidence"])
                    except ValueError:
                        pass

        im = ax.imshow(matrix, cmap=cmap, vmin=1, vmax=5, aspect="auto")
        ax.set_xticks(range(len(ATTR_ORDER)))
        ax.set_xticklabels([ATTR_LABELS[a] for a in ATTR_ORDER], rotation=30,
                           ha="right", fontsize=9)
        ax.set_yticks(range(len(clips)))
        ax.set_yticklabels(clip_labels, fontsize=7)
        ax.set_title(COND_LABELS[cond], fontsize=11, fontweight="bold")

        for i in range(len(clips)):
            for j in range(len(ATTR_ORDER)):
                val = matrix[i, j]
                if not np.isnan(val):
                    color = "white" if val > 3.5 else "black"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=6, color=color)

        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02).set_label(
            "Mean confidence (1–5)", fontsize=8)

    fig.suptitle("Mean Observer Confidence per Clip and Attribute", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    path = os.path.join(OUT, "fig3_confidence_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig_demographics()
    fig_accuracy_heatmap()
    fig_confidence_heatmap()
    print("All figures done.")
