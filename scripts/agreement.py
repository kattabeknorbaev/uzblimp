"""Inter-annotator agreement between KN (review.py) and a second annotator.

Second-annotator input can be:
- the hand-check CSV sheet (handcheck/handcheck_iaa_562.csv), matched on the grammatical sentence;
- blind review.py copies (handcheck/blind/*_JM.tsv), matched on pair id.
Both judgments are reduced to "usable" (accepted/edited; good_ok=Y and bad_is_wrong=Y,
or a fixed_bad was given) vs "not usable". Reports raw agreement and Cohen's kappa
overall and per phenomenon, and writes the disagreements for joint adjudication.

    python scripts/agreement.py handcheck/handcheck_iaa_562.csv handcheck/blind/*_JM.tsv --annotator JM
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
    """Hand-check sheet row → 'usable' / 'not usable' / None (not filled in)."""
    g, b = r.get("good_ok", "").strip().lower(), r.get("bad_is_wrong", "").strip().lower()
    if g in NO:
        return "not usable"
    if g in YES and b in YES:
        return "usable"
    if g in YES and b in NO:
        return "usable" if r.get("fixed_bad", "").strip() else "not usable"
    return None


def status_label(status):
    if status == "unchecked":
        return None
    return "usable" if status in ("accepted", "edited") else "not usable"


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    agree = sum(a == b for a, b in pairs) / n
    labels = {x for p in pairs for x in p}
    chance = sum((sum(a == lab for a, _ in pairs) / n) * (sum(b == lab for _, b in pairs) / n) for lab in labels)
    return agree, (agree - chance) / (1 - chance) if chance < 1 else 1.0


def load_kn():
    by_sent, by_id = {}, {}
    for f in glob.glob(str(ROOT / "data" / "pairs_v*.tsv")):
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                lab = status_label(r["status"])
                if lab:
                    by_sent[normalize(r["grammatical"]).lower()] = (r, lab)
                    by_id[r["id"]] = (r, lab)
    return by_sent, by_id


def load_second(paths, kn_sent, kn_id):
    """[{good, bad, label, kn, detail}] from CSV sheets and blind TSV copies."""
    items = []
    for path in paths:
        if path.endswith(".tsv"):
            with open(path, encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                    items.append({"good": r["grammatical"], "bad": r["ungrammatical"],
                                  "label": status_label(r["status"]), "kn": kn_id.get(r["id"]),
                                  "detail": f"{r['status']} {r.get('reason', '')}".strip()})
        else:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    items.append({"good": r["good"], "bad": r["bad"], "label": sheet_label(r),
                                  "kn": kn_sent.get(normalize(r["good"]).lower()),
                                  "detail": f"good_ok={r['good_ok']} bad_is_wrong={r['bad_is_wrong']} "
                                            f"fixed_bad={r['fixed_bad']} {r['comment']}".strip()})
    return items


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="+", help="hand-check CSV and/or blind review.py TSV files")
    p.add_argument("--annotator", default="JM")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    kn_sent, kn_id = load_kn()
    items = load_second(args.inputs, kn_sent, kn_id)
    both, per, disagree = [], defaultdict(list), []
    judged = sum(it["label"] is not None for it in items)
    for it in items:
        if it["label"] is None or it["kn"] is None:
            continue
        krow, klab = it["kn"]
        both.append((klab, it["label"]))
        per[krow["phenomenon"]].append((klab, it["label"]))
        if klab != it["label"]:
            disagree.append({"pair_id": krow["id"], "phenomenon": krow["phenomenon"], "good": it["good"],
                             "bad": it["bad"], "KN": f"{krow['status']} {krow.get('reason', '')}".strip(),
                             args.annotator: it["detail"]})

    print(f"{args.annotator} judged {judged}/{len(items)} rows; judged by both KN and {args.annotator}: {len(both)}.")
    lines = [f"# Inter-annotator agreement: KN vs {args.annotator}", "",
             f"Inputs: {', '.join(f'`{s}`' for s in args.inputs)}. {judged}/{len(items)} rows judged by "
             f"{args.annotator}; {len(both)} pairs judged by both.", "",
             "Labels: usable (accepted/edited) vs not usable. Because most pairs are usable, κ is low "
             "even at high agreement (the kappa paradox), so read both columns.", "",
             "| Phenomenon | Pairs | Agreement | Cohen's κ |", "|---|---|---|---|"]
    for ph, pairs in sorted(per.items()) + [("**All**", both)]:
        a, k = kappa(pairs)
        if a is not None:
            lines.append(f"| {ph} | {len(pairs)} | {100 * a:.1f}% | {k:.2f} |")
            print(f"  {ph:24} n={len(pairs):4}  agreement {100 * a:5.1f}%  kappa {k:.2f}")
    out = ROOT / "results" / f"agreement_KN_{args.annotator}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    msg = f"Wrote {out}"
    if disagree:
        dis = ROOT / "handcheck" / f"disagreements_KN_{args.annotator}.csv"
        with open(dis, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(disagree[0]))
            w.writeheader()
            w.writerows(disagree)
        msg += f" and {dis} ({len(disagree)} disagreements)"
    print(msg)


if __name__ == "__main__":
    main()
