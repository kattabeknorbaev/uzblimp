"""Convert the Latin benchmark to Cyrillic and run the automatic checks.

Writes data/benchmark/uzblimp_cyrl.tsv (Cyrillic pairs + the Latin originals) and
handcheck/cyrillic_check_60.csv (10 pairs per phenomenon for the native check;
fixed seeds, so the same ids are drawn as long as the benchmark doesn't change).

Checks: Latin letters left (Roman numerals allowed), pairs that no longer differ
in one place, and Cyrillic → Latin round trips that don't give back the original.

    python scripts/convert_cyrillic.py              # keeps checked rows, samples new phenomena
    python scripts/convert_cyrillic.py --resample   # redraws the sheet (erases the check)
"""
import collections
import csv
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from alphabets import to_cyrillic, to_latin  # noqa: E402
from validate_pairs import check_pair  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/benchmark/uzblimp.tsv"
OUT = ROOT / "data/benchmark/uzblimp_cyrl.tsv"
SHEET = ROOT / "handcheck/cyrillic_check_60.csv"
LEFTOVER = re.compile(r"[A-Za-z⁠]")
ROMAN = re.compile(r"\b[IVXLC]+\b")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    out, bad_rt, multi, latin = [], [], 0, 0
    for r in rows:
        g, b = to_cyrillic(r["grammatical"]), to_cyrillic(r["ungrammatical"])
        latin += bool(LEFTOVER.search(ROMAN.sub("", g + " " + b)))
        e, _ = check_pair({"id": r["id"], "phenomenon": r["phenomenon"], "grammatical": g, "ungrammatical": b,
                           "method": "corpus-edit", "source_id": "", "status": "accepted", "notes": ""})
        multi += bool([m for m in e if "place" in m or "adjacent" in m])
        for lat, cyr in ((r["grammatical"], g), (r["ungrammatical"], b)):
            if to_latin(cyr) != lat:
                bad_rt.append((lat, to_latin(cyr)))
        out.append({"id": r["id"], "phenomenon": r["phenomenon"], "grammatical": g, "ungrammatical": b,
                    "latin_grammatical": r["grammatical"], "latin_ungrammatical": r["ungrammatical"]})

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} pairs → {OUT.relative_to(ROOT)}")
    print(f"leftover Latin letters: {latin} | no longer one change: {multi} | round-trip diffs: {len(bad_rt)}")
    for a, c in bad_rt:
        print("   ", [(x, y) for x, y in zip(a.split(), c.split()) if x != y])

    kept = []
    if SHEET.exists() and "--resample" not in sys.argv:  # keep the checked rows, add new phenomena only
        kept = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    have = {r["phenomenon"] for r in kept}
    by = collections.defaultdict(list)
    for o in out:
        by[o["phenomenon"]].append(o)
    added = [x for ph in sorted(by) if ph not in have for x in random.Random(f"cyr-{ph}").sample(by[ph], 10)]
    if not added:
        print(f"{SHEET.relative_to(ROOT)}: every phenomenon already sampled; unchanged (--resample to redraw)")
        return
    sample = kept + added
    with open(SHEET, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "phenomenon", "latin_grammatical", "grammatical",
                                          "latin_ungrammatical", "ungrammatical", "cyrillic_ok", "comment"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(sample)
    print(f"{len(sample)} pairs → {SHEET.relative_to(ROOT)} ({len(added)} new to check)")


if __name__ == "__main__":
    main()
