"""Inter-annotator agreement between KN (review.py) and the second annotator (hand-check sheet).

Pairs are matched on the grammatical sentence. Both judgments are reduced to
"usable" (accepted/edited; good_ok=Y and bad_is_wrong=Y, or a fixed_bad was given)
vs "not usable". Reports raw agreement and Cohen's kappa overall and per
phenomenon, and writes the disagreements for joint adjudication.

    python scripts/agreement.py handcheck/handcheck_iaa_562.csv --annotator JM
"""
import argparse
import csv
import glob
import sys
from collections import defaultdict
from pathlib import Path

from make_pairs import normalize

ROOT = Path(__file__).resolve().parent.parent
YES, NO = {"y", "yes", "ha", "1"}, {"n", "no", "yoʻq", "0"}


def sheet_label(r):
    """'usable' / 'not usable' / None (not filled in)."""
    g, b = r.get("good_ok", "").strip().lower(), r.get("bad_is_wrong", "").strip().lower()
    if g in NO:
        return "not usable"
    if g in YES and b in YES:
        return "usable"
    if g in YES and b in NO:
        return "usable" if r.get("fixed_bad", "").strip() else "not usable"
    return None


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    agree = sum(a == b for a, b in pairs) / n
    labels = {x for p in pairs for x in p}
    chance = sum((sum(a == lab for a, _ in pairs) / n) * (sum(b == lab for _, b in pairs) / n) for lab in labels)
    return agree, (agree - chance) / (1 - chance) if chance < 1 else 1.0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sheet")
    p.add_argument("--annotator", default="JM")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    kn = {}
    for f in glob.glob(str(ROOT / "data" / "pairs_v*.tsv")):
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                if r["status"] != "unchecked":
                    kn[normalize(r["grammatical"]).lower()] = (r, "usable" if r["status"] in ("accepted", "edited")
                                                               else "not usable")
    with open(args.sheet, encoding="utf-8-sig", newline="") as fh:
        sheet = list(csv.DictReader(fh))

    both, per, disagree, filled = [], defaultdict(list), [], 0
    for r in sheet:
        lab = sheet_label(r)
        filled += lab is not None
        key = normalize(r["good"]).lower()
        if lab is None or key not in kn:
            continue
        krow, klab = kn[key]
        both.append((klab, lab))
        per[krow["phenomenon"]].append((klab, lab))
        if klab != lab:
            disagree.append({"pair_id": krow["id"], "phenomenon": krow["phenomenon"], "good": r["good"],
                             "bad": r["bad"], "KN": f"{krow['status']} {krow.get('reason', '')}".strip(),
                             args.annotator: f"good_ok={r['good_ok']} bad_is_wrong={r['bad_is_wrong']} "
                                             f"fixed_bad={r['fixed_bad']} {r['comment']}".strip()})

    print(f"Sheet rows filled in: {filled}/{len(sheet)}. Judged by both KN and {args.annotator}: {len(both)}.")
    lines = [f"# Inter-annotator agreement: KN vs {args.annotator}", "",
             f"Sheet `{args.sheet}`: {filled}/{len(sheet)} rows filled in; {len(both)} pairs judged by both.", "",
             "| Phenomenon | Pairs | Agreement | Cohen's κ |", "|---|---|---|---|"]
    for ph, items in sorted(per.items()) + [("**All**", both)]:
        a, k = kappa(items)
        if a is not None:
            lines.append(f"| {ph} | {len(items)} | {100 * a:.1f}% | {k:.2f} |")
            print(f"  {ph:24} n={len(items):4}  agreement {100 * a:5.1f}%  kappa {k:.2f}")
    out = ROOT / "results" / f"agreement_KN_{args.annotator}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dis = ROOT / "handcheck" / f"disagreements_KN_{args.annotator}.csv"
    if disagree:
        with open(dis, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(disagree[0]))
            w.writeheader()
            w.writerows(disagree)
    print(f"Wrote {out}" + (f" and {dis} ({len(disagree)} disagreements)" if disagree else ""))


if __name__ == "__main__":
    main()
