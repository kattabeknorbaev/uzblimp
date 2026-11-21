"""Markdown report for one benchmark version, from the per-pair result files of the model registry.

Sections: accuracy by model and alphabet, accuracy per phenomenon (own script, other script, reformed
Latin), paired tests (own against other script, current against reformed Latin, script-matched Goldfish
models), reformed Latin by where the new letters fall, the length effect, and a reproducibility check
against an earlier version on the pairs whose text is unchanged. Only complete runs are reported.

    python scripts/eval_report.py --previous v1.1 > results/eval_v1.2_tables.md
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from analysis import PHENOMENA, SLUGS, benchmark, holm, paired, wilson  # noqa: E402
from models import ALPHABETS, MODELS, VERSION, csv_path, load_runs  # noqa: E402

SHORT = {p[0]: p[2] for p in PHENOMENA}
SIZES = ["5MB", "10MB", "100MB", "full"]
REFORM_GROUPS = ["critical word: both", "critical word: grammatical only", "only other words changed", "unchanged"]


def ok(df):
    return df.correct.astype(str).eq("True")


def acc(df, col="correct"):
    return 100 * df[col].astype(str).eq("True").mean()


def own(m):
    return "Cyrillic" if m["trained"] == "cyrl" else "Latin"


def other(m):
    return "Latin" if own(m) == "Cyrillic" else "Cyrillic"


def fmt_p(p):
    return f"{p:.1e}" if p < 0.001 else f"{p:.3f}"


def table(header, rows):
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for r in rows:
        print("| " + " | ".join(str(c) for c in r) + " |")
    print()


def per_phenomenon(runs, pick, title):
    rows = []
    for m in MODELS:
        df = runs.get((m["key"], pick(m)))
        if df is not None:
            rows.append([m["key"], pick(m)] + [f"{acc(df[df.phenomenon == ph]):.1f}" for ph in SLUGS] + [f"**{acc(df):.1f}**"])
    if rows:
        print(f"## {title}\n")
        table(["Model", "Text"] + [SHORT[ph] for ph in SLUGS] + ["All"], rows)


def tests(title, comparisons, note=""):
    """comparisons: (label, correct-series a, correct-series b); p-values are Holm-adjusted within the family."""
    if not comparisons:
        return
    results = [paired(a, b) for _, a, b in comparisons]
    adjusted = holm([r[3] for r in results])
    print(f"## {title}\n")
    if note:
        print(note + "\n")
    table(["Comparison", "Δ (points)", "95% CI", "only first right", "only second right", "p (McNemar)", "p (Holm)"],
          [[label, f"{d:+.1f}", f"{lo:+.1f} .. {hi:+.1f}", n10, n01, fmt_p(p), fmt_p(pa)]
           for (label, _, _), (d, lo, hi, p, _, n10, n01), pa in zip(comparisons, results, adjusted)])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default=VERSION)
    p.add_argument("--previous", help="earlier version for the reproducibility check, e.g. v1.1")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    runs = load_runs(args.version)
    bench = benchmark()
    models = [m for m in MODELS if any((m["key"], a) in runs for a in ALPHABETS)]

    print(f"## Accuracy (%) by model and alphabet ({len(bench)} pairs, {len(SLUGS)} phenomena; chance 50)\n")
    print("Byte-normalised accuracy (log-probability per UTF-8 byte) in parentheses; 95% Wilson intervals are at most ±2 points.\n")
    rows = []
    for m in models:
        cells = []
        for a in ALPHABETS:
            df = runs.get((m["key"], a))
            cells.append("–" if df is None else f"{acc(df):.1f} ({acc(df, 'correct_norm'):.1f})")
        rows.append([m["key"], m["hf"], m["trained"]] + cells)
    table(["Model", "Hugging Face id", "Uzbek data", "Latin", "Cyrillic", "Reformed"], rows)

    per_phenomenon(runs, own, "Accuracy per phenomenon, own script (multilingual models: Latin)")
    per_phenomenon(runs, other, "Accuracy per phenomenon, other script")
    per_phenomenon(runs, lambda m: "Reformed", "Accuracy per phenomenon, reformed Latin")

    tests("Own script against other script (same pairs)",
          [(f"{m['key']}: {own(m)} vs {other(m)}", ok(runs[(m["key"], own(m))]), ok(runs[(m["key"], other(m))]))
           for m in models if (m["key"], own(m)) in runs and (m["key"], other(m)) in runs],
          "Exact McNemar test and percentile bootstrap (2,000 resamples) over pairs.")
    tests("Current against reformed Latin",
          [(f"{m['key']}: Latin vs Reformed", ok(runs[(m["key"], "Latin")]), ok(runs[(m["key"], "Reformed")]))
           for m in models if (m["key"], "Latin") in runs and (m["key"], "Reformed") in runs])
    tests("Script-matched Goldfish models (Latin model on Latin vs Cyrillic model on Cyrillic)",
          [(size, ok(runs[(f"GF-L {size}", "Latin")]), ok(runs[(f"GF-C {size}", "Cyrillic")]))
           for size in SIZES if (f"GF-L {size}", "Latin") in runs and (f"GF-C {size}", "Cyrillic") in runs])

    rows = []
    for m in models:
        cur, ref = runs.get((m["key"], "Latin")), runs.get((m["key"], "Reformed"))
        if cur is None or ref is None:
            continue
        cells = []
        for g in REFORM_GROUPS:
            ids = bench.index[bench.reform_group == g]
            cells.append(f"{acc(cur.loc[ids]):.1f} → {acc(ref.loc[ids]):.1f}")
        rows.append([m["key"]] + cells)
    if rows:
        print("## Reformed Latin by where the new letters fall (current → reformed, %)\n")
        table(["Model"] + [f"{g} (n={int((bench.reform_group == g).sum())})" for g in REFORM_GROUPS], rows)

    print("## Length effect: accuracy by token count of the ungrammatical member\n")
    print("Tokens counted with each model's own tokenizer; Δ = accuracy where the ungrammatical member has more tokens minus "
          "where it has fewer.\n")
    rows = []
    for m in models:
        for a in ALPHABETS:
            df = runs.get((m["key"], a))
            if df is None:
                continue
            d = df.bad_ntok - df.good_ntok
            parts = [(d < 0), (d == 0), (d > 0)]
            cells = [f"{acc(df[mask]):.1f} (n={int(mask.sum())})" if mask.sum() else "–" for mask in parts]
            gap = f"{acc(df[parts[2]]) - acc(df[parts[0]]):+.1f}" if parts[0].sum() and parts[2].sum() else "–"
            rows.append([m["key"], a] + cells + [gap])
    table(["Model", "Text", "fewer", "same", "more", "Δ"], rows)

    if args.previous:
        rows = []
        for m in models:
            for a in ALPHABETS:
                new, old_file = runs.get((m["key"], a)), csv_path(m, a, args.previous)
                if new is None or not old_file.exists():
                    continue
                old = pd.read_csv(old_file).set_index("id")
                ids = [i for i in new.index.intersection(old.index)
                       if new.good[i] == old.good[i] and new.bad[i] == old.bad[i]]
                same = int((ok(new.loc[ids]) == ok(old.loc[ids])).sum())
                col = "good_logprob" if "good_logprob" in new.columns else new.columns[new.columns.str.startswith("good_")][0]
                worst = float((new.loc[ids, col] - old.loc[ids, col]).abs().max()) if ids else float("nan")
                rows.append([m["key"], a, len(ids), same, f"{worst:.1e}", f"{acc(old):.1f}", f"{acc(new):.1f}"])
        if rows:
            print(f"## Reproducibility: {args.version} against {args.previous} on pairs with unchanged text\n")
            table(["Model", "Text", "shared pairs", "same verdict", "largest score difference",
                   f"accuracy {args.previous}", f"accuracy {args.version}"], rows)

    lo, hi = wilson(75, 150)
    print(f"Runs reported: {len(runs)} ({len(models)} models). With 150 pairs, a per-phenomenon accuracy has a 95% Wilson "
          f"interval of at most ±{(hi - lo) / 2:.0f} points.")


if __name__ == "__main__":
    main()
