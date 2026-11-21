"""Shared statistics and benchmark annotations for the report, the paper tables and the figures.

Nothing here loads a model: everything is computed from data/benchmark/*.tsv and the per-pair result
files (results/*.csv). Only pandas and numpy are needed.
"""
import csv
import difflib
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF_LETTERS = set("öÖğĞşŞçÇ")
# The 16 phenomena in the order of the paper's tables: (slug, table name, short column label, layer);
# layer: category shared with TurBLiMP, or added outside its inventory
PHENOMENA = [
    ("anaphor_agreement", "Anaphor agreement", "Ana", "TurBLiMP"),
    ("lexical_case", "Lexical case", "LexC", "TurBLiMP"),
    ("ditransitive_dative", "Ditransitive dative", "Ditr", "TurBLiMP"),
    ("binding", "Binding", "Bind", "TurBLiMP"),
    ("stem_alternation", "Stem alternation (q/k)", "Stem", "TurBLiMP"),
    ("npi_hech", "NPI \\textit{hech}", "NPI", "TurBLiMP"),
    ("suspended_affixation", "Suspended affixation", "Susp", "TurBLiMP"),
    ("nominalization", "Nominalisation", "Nmlz", "TurBLiMP"),
    ("person_agreement", "Subject agreement", "Subj", "TurBLiMP"),
    ("passives", "Passives", "Pass", "TurBLiMP"),
    ("relative_clauses", "Relative clauses", "Rel", "TurBLiMP"),
    ("quantifiers", "Quantifiers (\\textit{har bir})", "Quan", "TurBLiMP"),
    ("numeral_no_plural", "Numeral + singular", "Num", "added"),
    ("postposition_case", "Postposition case", "Post", "added"),
    ("possessive_agreement", "Possessive agreement", "Poss", "added"),
    ("dative_allomorphy", "Dative allomorphy", "Dat", "added"),
]
SLUGS = [p[0] for p in PHENOMENA]


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def changed_words(good, bad):
    """(words of the grammatical sentence, words of the ungrammatical one) at the edited place."""
    tg, tb = good.split(), bad.split()
    ops = [o for o in difflib.SequenceMatcher(a=tg, b=tb, autojunk=False).get_opcodes() if o[0] != "equal"]
    return [w for _, i1, i2, _, _ in ops for w in tg[i1:i2]], [w for _, _, _, j1, j2 in ops for w in tb[j1:j2]]


def new_letter_side(good, bad):
    """Which member's changed word contains a letter of the reformed alphabet:
    'both', 'grammatical only', 'ungrammatical only' or 'neither'."""
    g, b = changed_words(good, bad)
    g, b = any(set(w) & REF_LETTERS for w in g), any(set(w) & REF_LETTERS for w in b)
    return {(True, True): "both", (True, False): "grammatical only", (False, True): "ungrammatical only"}.get((g, b), "neither")


def benchmark():
    """One row per pair (index: pair id) with the Latin sentences and the annotations the analyses use."""
    b = pd.DataFrame(read_tsv(ROOT / "data/benchmark/uzblimp.tsv")).set_index("id")
    # Pair ids from the uz-books collection are numbered from 2000 (scripts/import_v11.py).
    b["source"] = ["books" if i.split("-")[-1].startswith("2") else "corpus" for i in b.index]
    b["words"] = b.grammatical.str.split().str.len()
    b["dbytes"] = [len(u.encode()) - len(g.encode()) for g, u in zip(b.grammatical, b.ungrammatical)]
    b["dchars"] = b.ungrammatical.str.len() - b.grammatical.str.len()
    ref = pd.DataFrame(read_tsv(ROOT / "data/benchmark/uzblimp_reformed.tsv")).set_index("id")
    b["reform_category"] = ref.reform_category
    b["reform_side"] = [new_letter_side(g, u) for g, u in zip(ref.grammatical, ref.ungrammatical)]
    b["reform_group"] = np.where(b.reform_category == "critical word changed", "critical word: " + b.reform_side,
                                 b.reform_category)
    return b


def wilson(k, n, z=1.959964):
    """Wilson score interval for a proportion, in percent."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (centre - half), 100 * (centre + half)


def mcnemar_exact(n10, n01):
    """Two-sided exact (binomial) McNemar test on the discordant pairs."""
    n = n10 + n01
    if n == 0:
        return 1.0
    k = min(n10, n01)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


def paired(a, b, seed=0, resamples=2000):
    """Accuracy difference a − b on the same pairs: (difference in points, CI low, CI high, exact McNemar p,
    number of pairs, pairs only a gets right, pairs only b gets right). The interval is a percentile
    bootstrap over pairs."""
    a, b = a.align(b, join="inner")
    a, b = a.astype(bool), b.astype(bool)
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    diffs = a.astype(int).values - b.astype(int).values
    rng = np.random.default_rng(seed)
    boots = np.sort(diffs[rng.integers(0, len(diffs), size=(resamples, len(diffs)))].mean(axis=1))
    lo, hi = boots[int(0.025 * resamples)], boots[int(0.975 * resamples) - 1]
    return 100 * diffs.mean(), 100 * lo, 100 * hi, mcnemar_exact(n10, n01), len(a), n10, n01


def holm(pvalues):
    """Holm-adjusted p-values, in the order given."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def selftest():
    fails = 0

    def check(name, ok):
        nonlocal fails
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} {name}")

    lo, hi = wilson(144, 150)
    check("Wilson interval of 144/150 is about 91.5-98.2", abs(lo - 91.5) < 0.2 and abs(hi - 98.2) < 0.2)
    check("exact McNemar 10 vs 2 is about 0.039", abs(mcnemar_exact(10, 2) - 0.0386) < 0.001)
    check("exact McNemar with no discordant pairs is 1", mcnemar_exact(0, 0) == 1.0)
    check("Holm keeps the smallest p times m", holm([0.01, 0.04, 0.03])[0] == 0.03 and holm([0.01, 0.04, 0.03])[1] == 0.06)
    a = pd.Series([True] * 90 + [False] * 10)
    b = pd.Series([True] * 80 + [False] * 20)
    d, lo, hi, p, n, n10, n01 = paired(a, b)
    check("paired difference of 90% vs 80% on nested errors is +10 with 10 discordant pairs",
          abs(d - 10) < 1e-9 and (n10, n01) == (10, 0) and lo > 0 and p < 0.01)
    check("new_letter_side finds the reformed letter on one side",
          new_letter_side("Men özimni kördim.", "Men meni kördim.") == "grammatical only")
    bench = benchmark()
    check("benchmark has 2,400 pairs, 150 per phenomenon",
          len(bench) == 2400 and set(bench.phenomenon.value_counts()) == {150} and set(bench.phenomenon) == set(SLUGS))
    print(f"\n{fails} failure(s)")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if selftest() else 0)
