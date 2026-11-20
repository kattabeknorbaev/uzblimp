"""Convert the Latin benchmark to the reformed 2026 Latin and label each pair.

Writes data/benchmark/uzblimp_reformed.tsv with a reform_category per pair:
- critical word changed:    the word(s) that make the pair differ contain ö/ğ/ş/ç
- only other words changed: new letters only in the rest of the sentence
- unchanged:                no oʻ/gʻ/sh/ch at all (identical to current Latin)
Then screens the tokenizers for <unk> (decision 8: only 0-<unk> models are scored).

    python scripts/convert_reformed.py
"""
import collections
import csv
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from alphabets import to_reformed  # noqa: E402
from schema import tokens  # noqa: E402
from validate_pairs import check_pair  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/benchmark/uzblimp.tsv"
OUT = ROOT / "data/benchmark/uzblimp_reformed.tsv"
REF = set("öÖğĞşŞçÇ")

def critical_words(g, b):
    tg, tb = tokens(g), tokens(b)
    ops = [op for op in difflib.SequenceMatcher(a=tg, b=tb, autojunk=False).get_opcodes() if op[0] != "equal"]
    return [w for _, i1, i2, j1, j2 in ops for w in tg[i1:i2] + tb[j1:j2]]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    out, cats, broken = [], collections.Counter(), 0
    for r in rows:
        g, b = to_reformed(r["grammatical"]), to_reformed(r["ungrammatical"])
        e, _ = check_pair({"id": r["id"], "phenomenon": r["phenomenon"], "grammatical": g, "ungrammatical": b,
                           "method": "corpus-edit", "source_id": "", "status": "accepted", "notes": ""})
        broken += bool([m for m in e if "place" in m or "adjacent" in m])
        if g == r["grammatical"] and b == r["ungrammatical"]:
            cat = "unchanged"
        elif any(set(w) & REF for w in critical_words(g, b)):
            cat = "critical word changed"
        else:
            cat = "only other words changed"
        cats[(r["phenomenon"], cat)] += 1
        cats[("ALL", cat)] += 1
        out.append({"id": r["id"], "phenomenon": r["phenomenon"], "grammatical": g, "ungrammatical": b,
                    "reform_category": cat})
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} pairs → {OUT.relative_to(ROOT)} | no longer one change: {broken}")
    print(f"{'phenomenon':22} {'critical word changed':>22} {'only other words':>17} {'unchanged':>10}")
    for p in sorted({p for p, _ in cats if p != "ALL"}) + ["ALL"]:
        print(f"{p:22} {cats[(p, 'critical word changed')]:>22} {cats[(p, 'only other words changed')]:>17} "
              f"{cats[(p, 'unchanged')]:>10}")
    print("\nTokenizer screening for unknown tokens: python scripts/run_models.py --stats-only")


if __name__ == "__main__":
    main()
