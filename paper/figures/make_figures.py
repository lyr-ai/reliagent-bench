"""Figures 1 and 2, built from the frozen result artifacts.

Reads `results/phase2-0-*` (E2, effort low) and `results/phase2-1-*` (R1,
effort high) read-only. No model calls, no rescoring: every number plotted is
recomputed from the committed raw responses with the same rule the scorer used
(`action_correct`).

    python paper/figures/make_figures.py
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/reliagent_bench/memory/mode_b/results"
TASKS = ROOT / "src/reliagent_bench/memory/mode_b/tasks/phase2.json"
OUT = Path(__file__).resolve().parent

E2 = "phase2-0-SCR+SRC+b_typed+nomem.json"
R1 = "phase2-1-effort-high-SCR+SRC+b_typed+nomem.json"

LABEL = {"S>C>R": "S>C>R", "S>R>C": "S>R>C", "b_typed": "Typed", "nomem": "no memory"}
COLOR = {"S>C>R": "#c0392b", "S>R>C": "#2471a3", "b_typed": "#1e8449", "nomem": "#7f8c8d"}
MARKER = {"S>C>R": "o", "S>R>C": "s", "b_typed": "D", "nomem": "^"}


def load(fname):
    d = json.load(open(RES / fname))
    meta = json.loads(TASKS.read_text())["scenarios"]
    cls = {x["id"]: x["state_class"] for x in meta}
    fam = {x["id"]: x.get("family", "?") for x in meta}
    return d["scores"], cls, fam


def class_of(sid, cls, fam):
    return "controls" if fam[sid] == "control" else cls[sid]


def rates_by_class(scores, cls, fam):
    acc = collections.defaultdict(lambda: [0, 0])
    for s in scores:
        k = (s["variant"], class_of(s["scenario"], cls, fam))
        acc[k][0] += bool(s["action_correct"])
        acc[k][1] += 1
    return {k: v[0] / v[1] for k, v in acc.items()}, {k: v[1] for k, v in acc.items()}


def per_scenario(scores, variant, ids):
    acc = collections.defaultdict(lambda: [0, 0])
    for s in scores:
        if s["variant"] == variant and s["scenario"] in ids:
            acc[s["scenario"]][0] += bool(s["action_correct"])
            acc[s["scenario"]][1] += 1
    return {i: acc[i][0] / acc[i][1] for i in ids}


# ───────────────────────── Figure 1 ─────────────────────────
def figure1():
    scores, cls, fam = load(E2)
    rate, n = rates_by_class(scores, cls, fam)
    classes = ["epistemic", "declared", "controls"]
    x = range(len(classes))

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for v in ["S>C>R", "S>R>C", "b_typed", "nomem"]:
        ys = [rate[(v, c)] for c in classes]
        ax.plot(x, ys, marker=MARKER[v], color=COLOR[v], linewidth=2, markersize=7,
                label=LABEL[v], linestyle="--" if v == "nomem" else "-",
                alpha=0.65 if v == "nomem" else 1.0, zorder=2)
        dy = {"S>C>R": -14, "S>R>C": 9, "b_typed": 9, "nomem": -14}[v]
        dx = {"S>C>R": 0, "S>R>C": -16, "b_typed": 16, "nomem": 0}[v]
        for xi, y in zip(x, ys):
            ax.annotate(f"{y:.2f}", (xi, y), textcoords="offset points",
                        xytext=(dx, dy), ha="center", fontsize=7.5, color=COLOR[v])

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{c}\n(n={n[('S>C>R', c)]} runs)" for c in classes])
    ax.set_ylabel("task success")
    ax.set_ylim(-0.08, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.axhline(0, color="#bbb", linewidth=0.8, zorder=1)
    ax.set_title("Resolution policy × state class, agent task success\n"
                 "(effort low; 36 scenarios × 5 runs)", fontsize=10.5)
    ax.legend(frameon=False, fontsize=9, loc="center left", bbox_to_anchor=(1.01, 0.5))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "figure1-interaction.png", dpi=200, bbox_inches="tight")
    print("wrote figure1-interaction.png")


# ───────────────────────── Figure 2 ─────────────────────────
def figure2():
    s2, cls, fam = load(E2)
    s1, _, _ = load(R1)
    typed = [i for i in cls if fam[i] == "typed"]
    decl = sorted(i for i in typed if cls[i] == "declared")
    epis = sorted(i for i in typed if cls[i] == "epistemic")

    panels = [
        ("Declared revision suppressed\n(policy S>C>R, declared scenarios)", "S>C>R", decl),
        ("Epistemic evidence overridden\n(policy S>R>C, epistemic scenarios)", "S>R>C", epis),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3), sharey=True)
    for ax, (title, variant, ids) in zip(axes, panels):
        lo = per_scenario(s2, variant, ids)
        hi = per_scenario(s1, variant, ids)
        x = range(len(ids))
        w = 0.38
        ax.bar([i - w / 2 for i in x], [lo[i] for i in ids], w,
               color="#5d6d7e", label="effort low", zorder=2)
        ax.bar([i + w / 2 for i in x], [hi[i] for i in ids], w,
               color="#e67e22", label="effort high", zorder=2)
        agg_lo = sum(lo.values()) / len(ids)
        agg_hi = sum(hi.values()) / len(ids)
        ax.axhline(agg_lo, color="#5d6d7e", linestyle=":", linewidth=1.6, zorder=3)
        ax.axhline(agg_hi, color="#e67e22", linestyle=":", linewidth=1.6, zorder=3)
        if abs(agg_hi - agg_lo) < 0.01:
            ax.annotate(f"mean {agg_lo:.2f} (both)", (-0.45, agg_lo + 0.03),
                        fontsize=8.5, color="#34495e", va="bottom", ha="left")
        else:
            ax.annotate(f"mean {agg_hi:.2f}  high", (-0.45, agg_hi + 0.02),
                        fontsize=8.5, color="#e67e22", va="bottom", ha="left")
            ax.annotate(f"mean {agg_lo:.2f}  low", (-0.45, agg_lo - 0.02),
                        fontsize=8.5, color="#5d6d7e", va="top", ha="left")
        ax.set_xticks(list(x))
        ax.set_xticklabels([i.replace("P-", "") for i in ids], rotation=60,
                           ha="right", fontsize=7.5)
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 1.08)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25, linewidth=0.6)

    axes[0].set_ylabel("task success (correct runs / 5)")
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("Asymmetric downstream recoverability — per scenario, both effort conditions\n"
                 "12 scenarios × 5 runs = n=60 per effort condition per panel; "
                 "left panel is 0/60 observed recovery in both conditions",
                 fontsize=10.5, y=1.04)
    fig.tight_layout()
    fig.savefig(OUT / "figure2-asymmetry.png", dpi=200, bbox_inches="tight")
    print("wrote figure2-asymmetry.png")


if __name__ == "__main__":
    figure1()
    figure2()
