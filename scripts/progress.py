"""Write results/progress.md: per-phenomenon progress toward 150 accepted pairs.

Reads every data/pairs_v*.tsv. "Usable" = accepted + edited. At most 150 usable
pairs per phenomenon count toward the benchmark; the rest are reserve
(notes/decisions.md #15). Run it after every review session.

    python scripts/progress.py
"""
import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from schema import PHENOMENA

ROOT = Path(__file__).resolve().parent.parent
TARGET = 150
CHECKPOINT_DATE, CHECKPOINT_MIN, CHECKPOINT_GOAL = date(2026, 11, 1), 600, 1000


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    counts = defaultdict(Counter)
    files = sorted((ROOT / "data").glob("pairs_v*.tsv"))
    for f in files:
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                counts[r["phenomenon"]][r["status"]] += 1
    rows, tot = [], Counter()
    for ph in PHENOMENA:
        c = counts.get(ph, Counter())
        usable = c["accepted"] + c["edited"]
        generated = sum(c.values())
        reviewed = usable + c["rejected"]
        bench, reserve = min(usable, TARGET), max(usable - TARGET, 0)
        rate = f"{100 * usable / reviewed:.0f}%" if reviewed else "–"
        done = "✅" if usable >= TARGET else ("🟡" if usable else "⬜")
        rows.append(f"| {done} {ph} | {TARGET} | {generated} | {reviewed} | {usable} | {rate} | {bench} | {reserve} |")
        tot.update(generated=generated, reviewed=reviewed, usable=usable, bench=bench, reserve=reserve)

    days_left = (CHECKPOINT_DATE - date.today()).days
    complete = sum(1 for ph in PHENOMENA if counts[ph]["accepted"] + counts[ph]["edited"] >= TARGET)
    md = [
        "# UzBLiMP progress",
        "",
        f"**Checkpoint {CHECKPOINT_DATE:%d %B %Y}: at least {CHECKPOINT_MIN} accepted pairs (goal ~{CHECKPOINT_GOAL:,})** "
        f"in the benchmark, {days_left} days from {date.today():%d %B %Y}. "
        f"Full set: {len(PHENOMENA)} × {TARGET} = {len(PHENOMENA) * TARGET:,}.",
        "",
        f"- Benchmark pairs so far: **{tot['bench']} / {len(PHENOMENA) * TARGET:,}** "
        f"({100 * tot['bench'] / (len(PHENOMENA) * TARGET):.0f}%); checkpoint minimum: {tot['bench']} / {CHECKPOINT_MIN}.",
        f"- Phenomena complete: {complete} / {len(PHENOMENA)}. Reserve pairs: {tot['reserve']}.",
        "",
        "| Phenomenon | Target | Generated | Reviewed | Accepted | Acceptance | In benchmark | Reserve |",
        "|---|---|---|---|---|---|---|---|",
        *rows,
        f"| **Total** | **{len(PHENOMENA) * TARGET:,}** | **{tot['generated']}** | **{tot['reviewed']}** | "
        f"**{tot['usable']}** | | **{tot['bench']}** | **{tot['reserve']}** |",
        "",
        "✅ complete · 🟡 started · ⬜ not started. *Accepted* includes edited pairs. "
        f"*In benchmark* = min(accepted, {TARGET}); the final 150 are picked at random (seeded) when the "
        "benchmark is built. Generated through `scripts/progress.py` from: "
        + ", ".join(f"`{f.name}`" for f in files) + ".",
        "",
    ]
    out = ROOT / "results" / "progress.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:6]))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
