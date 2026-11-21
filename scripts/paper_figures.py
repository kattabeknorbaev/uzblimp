"""Figures for the paper, drawn from the per-pair result files (paper/figures/*.pdf).

    python scripts/paper_figures.py

ladder.pdf   accuracy of the Goldfish models by training-data size, own and other script
length.pdf   accuracy by token-count category, own against other script, four monolingual models
reform.pdf   current against reformed Latin by where the new letters fall
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from analysis import benchmark  # noqa: E402
from models import ALPHABETS, MODELS, VERSION, load_runs  # noqa: E402
from models import label as model_label  # noqa: E402
from paper_tables import REFORM_GROUPS, SIZES, acc, ok, own  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "figures"
# Three categorical hues that stay apart for colour-blind readers (checked with a palette validator on a
# white surface, all pairs); identity is never carried by colour alone: line style, marker or label repeat it.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
COLUMN, FULL = 3.03, 6.3  # ACL column and text width in inches

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "pdf.fonttype": 42,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False,
})


def ladder(runs):
    series = [("GF-L", "Latin", BLUE, "-", "o", True, "Latin model, Latin text"),
              ("GF-C", "Cyrillic", ORANGE, "-", "s", True, "Cyrillic model, Cyrillic text"),
              ("GF-L", "Cyrillic", BLUE, "--", "o", False, "Latin model, Cyrillic text"),
              ("GF-C", "Latin", ORANGE, "--", "s", False, "Cyrillic model, Latin text")]
    fig, ax = plt.subplots(figsize=(COLUMN, 1.95))
    ax.axhline(50, color=AXIS, linewidth=0.6)
    ax.text(len(SIZES) - 0.55, 50.8, "chance", color=MUTED, fontsize=7, ha="right", va="bottom")
    for family, alphabet, color, style, marker, filled, label in series:
        pts = [(i, acc(runs[(f"{family} {s}", alphabet)])) for i, s in enumerate(SIZES) if (f"{family} {s}", alphabet) in runs]
        if not pts:
            continue
        ax.plot([x for x, _ in pts], [y for _, y in pts], style, color=color, linewidth=1.6, marker=marker, markersize=5,
                markerfacecolor=color if filled else "white", markeredgecolor=color, markeredgewidth=1.2, label=label,
                solid_capstyle="round")
    ax.set_xticks(range(len(SIZES)), SIZES)
    ax.set_xlim(-0.25, len(SIZES) - 0.75)
    ax.set_ylim(35, 100)
    ax.set_xlabel("Training data of the Goldfish model")
    ax.set_ylabel("Accuracy (%)")
    ax.xaxis.grid(False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, handlelength=2.6, columnspacing=1.2, labelspacing=0.3,
               borderaxespad=0.0)
    fig.tight_layout(pad=0.3, rect=(0, 0.185, 1, 1))
    fig.savefig(OUT / "ladder.pdf")
    plt.close(fig)


def length(runs):
    """Accuracy by token-count category for four monolingual models, own script against other script."""
    panels = [m for key in ("tahrirchi-bert", "UzBERT", "GF-L full", "GF-C full") for m in MODELS if m["key"] == key]
    panels = [m for m in panels if (m["key"], own(m)) in runs]
    if not panels:
        return
    fig, axes = plt.subplots(2, 2, figsize=(COLUMN, 2.3), sharex=True, sharey=True)
    for ax, m in zip(axes.flat, panels):
        ax.axhline(50, color=AXIS, linewidth=0.6)
        for alphabet, color, style, marker, filled, label in (
                (own(m), BLUE, "-", "o", True, "own script"),
                ("Latin" if own(m) == "Cyrillic" else "Cyrillic", ORANGE, "--", "s", False, "other script")):
            df = runs.get((m["key"], alphabet))
            if df is None:
                continue
            dtok = df.bad_ntok - df.good_ntok
            ys = [acc(df[mask]) for mask in (dtok < 0, dtok == 0, dtok > 0)]
            ax.plot(range(3), ys, style, color=color, linewidth=1.6, marker=marker, markersize=4.5,
                    markerfacecolor=color if filled else "white", markeredgecolor=color, markeredgewidth=1.1, label=label)
        ax.set_title(model_label(m), fontsize=7.5, color=INK, pad=2)
        ax.set_xticks(range(3), ["fewer", "same", "more"])
        ax.set_xlim(-0.3, 2.3)
        ax.set_ylim(0, 104)
        ax.set_yticks([0, 50, 100])
        ax.xaxis.grid(False)
    for ax in axes.flat[len(panels):]:
        ax.set_visible(False)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, handlelength=2.6, columnspacing=1.5, borderaxespad=0.0)
    fig.supylabel("Accuracy (%)", fontsize=8, x=0.02)
    fig.supxlabel("Tokens in the ungrammatical member", fontsize=8, y=0.085)
    fig.tight_layout(pad=0.3, h_pad=0.7, w_pad=0.6, rect=(0.03, 0.155, 1, 1))
    fig.savefig(OUT / "length.pdf")
    plt.close(fig)


def reform(runs, bench):
    models = [m for m in MODELS if (m["key"], "Latin") in runs and (m["key"], "Reformed") in runs]
    if not models:
        return
    titles = {"critical word: both": "Edited word:\nboth members", "critical word: grammatical only": "Edited word:\ngrammatical member only",
              "only other words changed": "Other words\nonly", "unchanged": "No new\nletter"}
    fig, axes = plt.subplots(1, 4, figsize=(FULL, 1.05 + 0.2 * len(models)), sharey=True)
    for ax, (group, title) in zip(axes, REFORM_GROUPS):
        ids = bench.index[bench.reform_group == group]
        ax.axvline(50, color=AXIS, linewidth=0.6)
        for i, m in enumerate(models):
            cur, ref = acc(runs[(m["key"], "Latin")].loc[ids]), acc(runs[(m["key"], "Reformed")].loc[ids])
            y = len(models) - 1 - i
            ax.plot([cur, ref], [y, y], color=AXIS, linewidth=1.4, solid_capstyle="round", zorder=2)
            ax.scatter([cur], [y], s=20, color="white", edgecolors=BLUE, linewidths=1.2, zorder=3,
                       label="Current Latin" if i == 0 else None)
            ax.scatter([ref], [y], s=20, color=BLUE, edgecolors=BLUE, linewidths=1.2, zorder=4,
                       label="Reformed Latin" if i == 0 else None)
        ax.set_title(f"{titles[group]} (n = {len(ids):,})", fontsize=7.5, color=INK, linespacing=1.15)
        ax.set_xlim(0, 103)
        ax.set_xticks([0, 50, 100])
        ax.yaxis.grid(False)
        ax.set_ylim(-0.6, len(models) - 0.4)
    axes[0].set_yticks(range(len(models)), [model_label(m) for m in reversed(models)])
    axes[0].tick_params(axis="y", labelcolor=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", ncol=2, handletextpad=0.1, columnspacing=1.2, borderaxespad=0.1)
    fig.supxlabel("Accuracy (%)", fontsize=8, x=0.42, y=0.01)
    fig.tight_layout(pad=0.3, w_pad=0.6, rect=(0, 0.09, 1, 1))
    fig.savefig(OUT / "reform.pdf")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runs = load_runs(VERSION)
    both = {k for k, a in runs if a == "Latin"} & {k for k, a in runs if a == "Cyrillic"}
    runs = {key: df for key, df in runs.items() if key[0] in both}  # as in paper_tables.py
    ladder(runs)
    length(runs)
    reform(runs, benchmark())
    print(f"wrote paper/figures/ladder.pdf, length.pdf, reform.pdf from {len(runs)} runs")


if __name__ == "__main__":
    main()
