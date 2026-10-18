"""Check data/explanations.tsv before a grammar-prompting run (decision 19).

Errors: a benchmark phenomenon without an explanation; an explanation containing a whole
benchmark or reserve sentence.
Warnings: an explanation using a word form that a benchmark or reserve pair changes (the
model would see part of the answer); length far from the median (explanation and control
should be comparable).

    python scripts/check_explanations.py [--col explanation_uz]
"""
import argparse
import csv
import difflib
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import tokens  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def changed_words(g, b):
    tg, tb = tokens(g), tokens(b)
    ops = difflib.SequenceMatcher(a=tg, b=tb, autojunk=False).get_opcodes()
    return {w.lower() for op, i1, i2, j1, j2 in ops if op != "equal" for w in tg[i1:i2] + tb[j1:j2]}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--explanations", default=str(ROOT / "data/explanations.tsv"))
    p.add_argument("--col", default="explanation")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    pairs = read(ROOT / "data/benchmark/uzblimp.tsv") + read(ROOT / "data/benchmark/reserve.tsv")
    needed = {r["phenomenon"] for r in read(ROOT / "data/benchmark/uzblimp.tsv")}
    critical = defaultdict(set)  # word form -> phenomena whose pairs change it
    for r in pairs:
        for w in changed_words(r["grammatical"], r["ungrammatical"]):
            critical[w].add(r["phenomenon"])
    sentences = {s for r in pairs for s in (r["grammatical"], r["ungrammatical"])}

    ex = {r["phenomenon"]: r[args.col].strip() for r in read(args.explanations)}
    errors, warnings = [], []
    for ph in sorted(needed):
        if not ex.get(ph):
            errors.append(f"{ph}: no {args.col} (it's in the benchmark)")
    lengths = {ph: len(t.split()) for ph, t in ex.items() if t}
    median = statistics.median(lengths.values()) if lengths else 0
    for ph, text in sorted(ex.items()):
        if not text:
            continue
        for s in sentences:
            if s in text:
                errors.append(f"{ph}: contains a benchmark/reserve sentence: {s[:60]}")
        hits = sorted({w for w in map(str.lower, tokens(text)) if w in critical})
        for w in hits:
            warnings.append(f"{ph}: uses '{w}', a word changed in {', '.join(sorted(critical[w]))} pairs")
        if median and not 0.67 * median <= lengths[ph] <= 1.5 * median:
            warnings.append(f"{ph}: {lengths[ph]} words (median {median:g})")

    print(f"{len(lengths)} explanations in column {args.col!r}; benchmark needs {len(needed)}; median {median:g} words")
    for kind, msgs in (("ERRORS", errors), ("WARNINGS", warnings)):
        if msgs:
            print(f"\n{kind} ({len(msgs)})")
            for m in msgs:
                print("  " + m)
    print("\nCLEAN" if not errors else f"\n{len(errors)} error(s)", f"{len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
