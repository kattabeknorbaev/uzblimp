"""Tables for one benchmark version: accuracy by model × alphabet × phenomenon, paired tests,
reformed-Latin categories, and a reproducibility check against an earlier version.

Reads results/<model>_uzblimp_<version>[_cyrl|_reformed][_bos].csv (from score_pairs.py) and
prints Markdown; runs that don't exist yet are listed as pending.

    python scripts/eval_report.py --version v0.2 --previous v0.1
"""
import argparse
import csv
import math
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
# label, alphabet, file stem without the version prefix ({v} is replaced)
RUNS = [
    ("Goldfish-latn", "Latin", "uzn_latn_100mb_uzblimp_{v}"),
    ("Goldfish-cyrl", "Latin", "uzn_cyrl_100mb_uzblimp_{v}"),
    ("tahrirchi-bert", "Latin", "tahrirchi-bert-base_uzblimp_{v}"),
    ("Qwen2.5-0.5B", "Latin", "Qwen2.5-0.5B_uzblimp_{v}_bos"),
    ("Goldfish-latn", "Cyrillic", "uzn_latn_100mb_uzblimp_{v}_cyrl"),
    ("Goldfish-cyrl", "Cyrillic", "uzn_cyrl_100mb_uzblimp_{v}_cyrl"),
    ("tahrirchi-bert", "Cyrillic", "tahrirchi-bert-base_uzblimp_{v}_cyrl"),
    ("Qwen2.5-0.5B", "Cyrillic", "Qwen2.5-0.5B_uzblimp_{v}_cyrl_bos"),
    ("tahrirchi-bert", "Reformed", "tahrirchi-bert-base_uzblimp_{v}_reformed"),
    ("Qwen2.5-0.5B", "Reformed", "Qwen2.5-0.5B_uzblimp_{v}_reformed_bos"),
]
# (first, second, label): paired comparisons on the same pairs
TESTS = [
    (("Goldfish-latn", "Latin"), ("Goldfish-cyrl", "Cyrillic"), "Matched script: Goldfish-latn on Latin vs Goldfish-cyrl on Cyrillic"),
    (("Goldfish-latn", "Latin"), ("Goldfish-latn", "Cyrillic"), "Goldfish-latn: Latin vs Cyrillic text"),
    (("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Cyrillic"), "tahrirchi-bert: Latin vs Cyrillic text"),
    (("Qwen2.5-0.5B", "Latin"), ("Qwen2.5-0.5B", "Cyrillic"), "Qwen2.5-0.5B: Latin vs Cyrillic text"),
    (("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Reformed"), "tahrirchi-bert: current vs reformed Latin"),
    (("Qwen2.5-0.5B", "Latin"), ("Qwen2.5-0.5B", "Reformed"), "Qwen2.5-0.5B: current vs reformed Latin"),
]


def paired(a, b):
    """Difference in accuracy (a − b) with a bootstrap 95% CI and McNemar's p (continuity-corrected)."""
    a, b = a.align(b, join="inner")
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    chi = (abs(n10 - n01) - 1) ** 2 / (n10 + n01) if n10 + n01 else 0.0
    p = math.erfc(math.sqrt(chi / 2)) if n10 + n01 else 1.0
    diffs = (a.astype(int) - b.astype(int)).values
    rng = random.Random(0)
    boots = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(2000))
    return 100 * (a.mean() - b.mean()), 100 * boots[50], 100 * boots[1949], p, len(a)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default="v0.2")
    p.add_argument("--previous", help="earlier version to compare shared pairs with, e.g. v0.1")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    runs, pending = {}, []
    for label, alpha, stem in RUNS:
        f = ROOT / "results" / f"{stem.format(v=args.version)}.csv"
        if f.exists():
            runs[(label, alpha)] = pd.read_csv(f).set_index("id")
        else:
            pending.append(f.name)
    if not runs:
        sys.exit("no result files for " + args.version)

    # 1. Accuracy by phenomenon
    cols = list(runs)
    phen = sorted(next(iter(runs.values())).phenomenon.unique())
    n = len(next(iter(runs.values())))
    print(f"## Accuracy (%) by model × alphabet ({n} pairs, {len(phen)} phenomena)\n")
    print("| Phenomenon | " + " | ".join(f"{m} ({a})" for m, a in cols) + " |")
    print("|---|" + "---|" * len(cols))
    for ph in phen:
        print(f"| {ph} | " + " | ".join(f"{100 * d[d.phenomenon == ph].correct.mean():.1f}" for d in runs.values()) + " |")
    print(f"| **All ({n})** | " + " | ".join(f"**{100 * d.correct.mean():.1f}**" for d in runs.values()) + " |")
    print("| acc_norm (per byte) | " + " | ".join(f"{100 * d.correct_norm.mean():.1f}" for d in runs.values()) + " |")
    if pending:
        print(f"\nPending: {', '.join(pending)}")

    # 2. Paired tests
    print("\n## Paired tests (same pairs; McNemar, bootstrap 95% CI)\n")
    print("| Comparison | Difference | 95% CI | p |\n|---|---|---|---|")
    for x, y, label in TESTS:
        if x in runs and y in runs:
            d, lo, hi, pv, _ = paired(runs[x].correct, runs[y].correct)
            print(f"| {label} | {d:+.1f} | {lo:+.1f}, {hi:+.1f} | {pv:.2g} |")
    x, y = ("Goldfish-latn", "Latin"), ("Goldfish-cyrl", "Cyrillic")
    if x in runs and y in runs:
        print(f"\nMatched script per phenomenon (Bonferroni threshold {0.05 / len(phen):.4f}):\n")
        print("| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Cyrillic) | Difference | p |\n|---|---|---|---|---|")
        for ph in phen:
            a, b = runs[x], runs[y]
            ids = a.index[a.phenomenon == ph]
            d, lo, hi, pv, _ = paired(a.loc[ids].correct, b.loc[ids].correct)
            print(f"| {ph} | {100 * a.loc[ids].correct.mean():.1f} | {100 * b.loc[ids].correct.mean():.1f} | {d:+.1f} | {pv:.2g} |")

    # 3. Reformed Latin by category
    ref_file = ROOT / "data/benchmark/uzblimp_reformed.tsv"
    if ref_file.exists() and any(a == "Reformed" for _, a in runs):
        cat = pd.read_csv(ref_file, sep="\t", dtype=str, quoting=csv.QUOTE_NONE).set_index("id").reform_category
        print("\n## Reformed Latin by where the new letters fall\n")
        print("| Model | Category | n | Current | Reformed | Difference [95% CI] | p |\n|---|---|---|---|---|---|---|")
        for m in ("tahrirchi-bert", "Qwen2.5-0.5B"):
            if (m, "Latin") not in runs or (m, "Reformed") not in runs:
                continue
            cur, ref = runs[(m, "Latin")].correct, runs[(m, "Reformed")].correct
            for c in ("critical word changed", "only other words changed", "unchanged"):
                ids = cat.index[cat == c]
                d, lo, hi, pv, k = paired(cur.loc[ids], ref.loc[ids])
                print(f"| {m} | {c} | {k} | {100 * cur.loc[ids].mean():.1f} | {100 * ref.loc[ids].mean():.1f} | "
                      f"{d:+.1f} [{lo:+.1f}, {hi:+.1f}] | {pv:.2g} |")

    # 4. Reproducibility on pairs shared with the previous version
    if args.previous:
        print(f"\n## Pairs shared with {args.previous}: same result?\n")
        print("| Run | Shared pairs (same text) | Same correct/incorrect | Max abs. log-prob difference |\n|---|---|---|---|")
        for label, alpha, stem in RUNS:
            f_old = ROOT / "results" / f"{stem.format(v=args.previous)}.csv"
            if (label, alpha) not in runs or not f_old.exists():
                continue
            old, new = pd.read_csv(f_old).set_index("id"), runs[(label, alpha)]
            ids = old.index.intersection(new.index)
            ids = ids[(old.loc[ids].good == new.loc[ids].good) & (old.loc[ids].bad == new.loc[ids].bad)]  # same text
            same = int((old.loc[ids].correct == new.loc[ids].correct).sum())
            dmax = max((old.loc[ids].good_logprob - new.loc[ids].good_logprob).abs().max(),
                       (old.loc[ids].bad_logprob - new.loc[ids].bad_logprob).abs().max())
            print(f"| {label} ({alpha}) | {len(ids)} | {same} | {dmax:.2g} |")


if __name__ == "__main__":
    main()
