"""Freeze the benchmark: exactly 150 usable pairs per complete phenomenon (decision 15).

Reads every data/pairs_v*.tsv; usable = accepted or edited. For each core phenomenon
with at least --per usable pairs, picks --per of them at random with a seed derived
from the phenomenon name, so adding phenomena or reserve pairs later never changes
the pairs already chosen for another phenomenon. The rest goes to the reserve file.
Phenomena below --per are listed as incomplete and left out.

    python scripts/build_benchmark.py            # → data/benchmark/uzblimp.tsv + reserve.tsv
"""
import argparse
import csv
import glob
import random
import sys
from collections import defaultdict
from pathlib import Path

from schema import PHENOMENA

ROOT = Path(__file__).resolve().parent.parent
OUT_COLS = ["id", "phenomenon", "grammatical", "ungrammatical", "method", "source_id", "reviewer"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--per", type=int, default=150)
    p.add_argument("--seed", default="uzblimp-2026")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    usable = defaultdict(list)
    for f in sorted(glob.glob(str(ROOT / "data" / "pairs_v*.tsv"))):
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                if r["status"] in ("accepted", "edited") and r["phenomenon"] in PHENOMENA:
                    usable[r["phenomenon"]].append(r)

    bench, reserve, incomplete = [], [], []
    for ph in PHENOMENA:
        rows = sorted(usable[ph], key=lambda r: r["id"])  # deterministic before shuffling
        if len(rows) < args.per:
            incomplete.append(f"{ph} ({len(rows)})")
            continue
        random.Random(f"{args.seed}-{ph}").shuffle(rows)
        # Corpus sentences only (2026-10-27): the hand-written seed pairs of pairs_v0.tsv are
        # skipped after shuffling, so every other pair keeps its place and only their slots change.
        rows = [r for r in rows if r.get("method") != "hand-written"]
        bench += rows[:args.per]
        reserve += rows[args.per:]

    out_dir = ROOT / "data" / "benchmark"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("uzblimp.tsv", bench), ("reserve.tsv", reserve)):
        with open(out_dir / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=OUT_COLS, delimiter="\t", lineterminator="\n",
                               quoting=csv.QUOTE_NONE, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    done = len(bench) // args.per
    print(f"Benchmark: {len(bench)} pairs, {done} phenomena × {args.per} → {out_dir / 'uzblimp.tsv'}")
    print(f"Reserve: {len(reserve)} pairs → {out_dir / 'reserve.tsv'}")
    print(f"Incomplete (left out): {', '.join(incomplete) or 'none'}")


if __name__ == "__main__":
    main()
