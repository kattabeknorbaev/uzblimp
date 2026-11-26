"""Score the returned sheets of the human validation study and write results/human/summary.md.

Put the filled-in sheets in archive/human_study/responses/ (any alphabet; the item numbers are the same):
    fc_<annotator>.csv                 forced choice: columns item, answer (A or B) [, unsure]
    ratings<1|2>_<annotator>.csv       ratings: columns item, rating (1-7); the digit is the list

The individual sheets stay private (archive/human_study/responses/ is not in the repository): the consent text
promises that answers are published only in aggregate. The forced-choice sheets are reduced to two released
files, results/human/forced_choice_judgments.csv (per pair: annotators, how many chose the grammatical
sentence, how many marked the pair as unsure, and how many of these chose the ungrammatical one) and results/human/forced_choice_annotators.csv (per annotator
code: answered, correct, unsure), and every forced-choice statistic is computed from these, so the report
can be reproduced without the sheets.

Forced choice: accuracy per annotator and per phenomenon, majority-vote accuracy, mean pairwise agreement
and Krippendorff's alpha (nominal, on the choices of A or B), and the accuracy of every scored model, each
on the script of its Uzbek training data, on the same pairs. Ratings: z-scores per participant, mean rating
of acceptable and unacceptable sentences per phenomenon, the number of participants who rate acceptable
sentences higher, and Pearson's r between the human and the model differences across phenomena (as in
TurBLiMP).

    python scripts/human_study_report.py
    python scripts/human_study_report.py --selftest
"""
import argparse
import csv
import itertools
import math
import random
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import RELEASE_PHENOMENA  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# Accepted spellings of an answer: Latin A/B, the Cyrillic letters that look or sound the same, or 1/2.
ANSWER = {"A": "A", "B": "B", "\u0410": "A", "\u0411": "B", "\u0412": "B", "1": "A", "2": "B"}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") else ","  # Excel in some locales saves semicolons
        return list(csv.DictReader(f, delimiter=delim))


def krippendorff_nominal(units):
    """Krippendorff's alpha for nominal data; units = list of lists of labels (one list per item)."""
    units = [u for u in units if len(u) >= 2]
    n = sum(len(u) for u in units)
    if not units or n < 2:
        return float("nan")
    coincidence = Counter()
    for u in units:
        for a, b in itertools.permutations(range(len(u)), 2):
            coincidence[(u[a], u[b])] += 1 / (len(u) - 1)
    totals = Counter()
    for (a, _), v in coincidence.items():
        totals[a] += v
    observed = sum(v for (a, b), v in coincidence.items() if a != b)
    expected = sum(totals[a] * totals[b] for a in totals for b in totals if a != b) / (n - 1)
    return 1 - observed / expected if expected else 1.0


def pearson(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def model_runs():
    """{label: per-pair DataFrame}: every scored model on the script of its Uzbek training data (Cyrillic for
    models trained on Cyrillic, current Latin for the others), as in the paper; empty without pandas."""
    try:
        from models import MODELS, load_runs
    except ImportError:
        return {}
    runs = load_runs()
    out = {}
    for m in MODELS:
        if m.get("setup") == "gpu":  # the models scored on CPU, as in the paper's comparison
            continue
        alphabet = "Cyrillic" if m["trained"] == "cyrl" else "Latin"
        if (m["key"], alphabet) in runs:
            out[f"{m['key']} ({alphabet[0]})"] = runs[(m["key"], alphabet)]
    return out


JUDGMENTS = "forced_choice_judgments.csv"
ANNOTATORS = "forced_choice_annotators.csv"


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def aggregate(folder, key, out_dir):
    """Reduce the individual forced-choice sheets to per-pair and per-annotator counts and write both files."""
    sheets = {}
    for f in sorted(folder.glob("fc_*.csv")):
        rows = {}
        for r in read_csv(f):
            if not (r.get("item") or "").strip():
                continue
            i, a = int(r["item"]), ANSWER.get((r.get("answer") or "").strip().upper()[:1])
            if a and i in key:
                rows[i] = (a, bool((r.get("unsure") or "").strip()))
        sheets[f.stem[3:]] = rows
    if not sheets:
        return False
    write_csv(out_dir / JUDGMENTS,
              ["item", "pair_id", "phenomenon", "grammatical", "annotators", "correct", "unsure", "unsure_wrong"],
              [[i, key[i]["pair_id"], key[i]["phenomenon"], key[i]["grammatical"],
                sum(i in rows for rows in sheets.values()),
                sum(rows[i][0] == key[i]["grammatical"] for rows in sheets.values() if i in rows),
                sum(rows[i][1] for rows in sheets.values() if i in rows),
                sum(rows[i][1] and rows[i][0] != key[i]["grammatical"] for rows in sheets.values() if i in rows)]
               for i in sorted(key)])
    write_csv(out_dir / ANNOTATORS, ["annotator", "answered", "correct", "unsure"],
              [[name, len(rows), sum(a == key[i]["grammatical"] for i, (a, _) in rows.items()),
                sum(u for _, u in rows.values())] for name, rows in sheets.items()])
    return True


def forced_choice(folder, key_file, agg_dir, lines):
    """folder: individual sheets (if present, they are aggregated into agg_dir first); agg_dir: released counts."""
    key = {int(r["item"]): r for r in read_csv(key_file)}
    aggregate(folder, key, agg_dir)
    if not (agg_dir / JUDGMENTS).exists():
        lines.append("No forced-choice sheets found (archive/human_study/responses/fc_<annotator>.csv).\n")
        return
    judg = {int(r["item"]): {k: int(r[k]) for k in ("annotators", "correct", "unsure", "unsure_wrong")}
            for r in read_csv(agg_dir / JUDGMENTS)}
    ann = read_csv(agg_dir / ANNOTATORS)
    lines += ["## Forced choice\n", f"{len(ann)} annotators, {len(key)} pairs, 20 per phenomenon. Each annotator chose "
              "the Latin or the Cyrillic version of the sheet.\n",
              "| Annotator | Answered | Accuracy (%) | Marked unsure |", "|---|---:|---:|---:|"]
    for r in ann:
        lines.append(f"| {r['annotator']} | {r['answered']} | {100 * int(r['correct']) / int(r['answered']):.1f} | {r['unsure']} |")
    # Every statistic below needs only the counts: the labels of a pair are `correct` choices of its grammatical
    # sentence and `annotators - correct` choices of the other one (A or B as shown to the annotators).
    other = {"A": "B", "B": "A"}
    units = {i: [key[i]["grammatical"]] * j["correct"] + [other[key[i]["grammatical"]]] * (j["annotators"] - j["correct"])
             for i, j in judg.items()}
    answered = sum(j["annotators"] for j in judg.values())
    correct = sum(j["correct"] for j in judg.values())
    agree = [a == b for u in units.values() for a, b in itertools.combinations(u, 2)]
    wins = {i for i, j in judg.items() if 2 * j["correct"] > j["annotators"]}
    ties = {i for i, j in judg.items() if j["annotators"] and 2 * j["correct"] == j["annotators"]}
    lines += ["", f"- Accuracy over all {answered} judgments: {100 * correct / max(answered, 1):.1f}%.",
              f"- Majority vote agrees with the benchmark on {len(wins)} of {len(judg) - len(ties)} pairs "
              f"({100 * len(wins) / max(len(judg) - len(ties), 1):.1f}%; {len(ties)} ties left out)."]
    if agree:
        lines.append(f"- Mean pairwise agreement {100 * sum(agree) / len(agree):.1f}%; "
                     f"Krippendorff's alpha {krippendorff_nominal(list(units.values())):.2f}.")
    wrong = Counter(j["annotators"] - j["correct"] for j in judg.values())
    lines.append("- Pairs by number of annotators who chose the ungrammatical sentence: "
                 + ", ".join(f"{k}: {v}" for k, v in sorted(wrong.items())) + ".")
    lines.append(f"- Answers marked as unsure: {sum(j['unsure'] for j in judg.values())}, on "
                 f"{sum(j['unsure'] > 0 for j in judg.values())} pairs; "
                 f"{sum(j['unsure_wrong'] for j in judg.values())} of them chose the ungrammatical sentence.")
    runs = model_runs()
    head = "| Phenomenon | Pairs | Human mean | Majority |" + "".join(f" {k} |" for k in runs)
    lines += ["", "Accuracy (%) on these pairs; models on the script of their Uzbek training data (L: current Latin, "
              "C: Cyrillic; multilingual models on Latin).", "", head, "|---|---:|---:|---:|" + "---:|" * len(runs)]
    for ph in list(RELEASE_PHENOMENA) + ["All"]:
        items = [i for i, r in key.items() if ph == "All" or r["phenomenon"] == ph]
        n = sum(judg[i]["annotators"] for i in items)
        decided = [i for i in items if i not in ties and judg[i]["annotators"]]
        cells = [f"{100 * sum(judg[i]['correct'] for i in items) / n:.1f}" if n else "–",
                 f"{100 * sum(i in wins for i in decided) / len(decided):.1f}" if decided else "–"]
        for df in runs.values():
            sel = df.loc[[key[i]["pair_id"] for i in items if key[i]["pair_id"] in df.index]]
            cells.append(f"{100 * sel.correct.astype(str).eq('True').mean():.1f}" if len(sel) else "–")
        lines.append(f"| {ph} | {len(items)} | " + " | ".join(cells) + " |")
    missed = sorted(i for i, j in judg.items() if j["correct"] < j["annotators"])
    if missed:
        lines += ["", "Pairs on which at least one annotator chose the ungrammatical sentence (item: pair, wrong/annotators): "
                  + "; ".join(f"{i}: {key[i]['pair_id']}, {judg[i]['annotators'] - judg[i]['correct']}/{judg[i]['annotators']}"
                              for i in missed) + "."]
    disputed = sorted(i for i in judg if i not in wins and judg[i]["annotators"])
    lines += ["", "Pairs to re-examine (the majority disagrees with the benchmark, or the vote is tied): "
              + (", ".join(key[i]["pair_id"] for i in disputed) if disputed else "none") + "."]
    lines.append("")


def ratings(folder, key_file, lines):
    key = {(int(r["list"]), int(r["item"])): r for r in read_csv(key_file)}
    z = defaultdict(dict)  # participant -> (list, item) -> z-score
    for f in sorted(folder.glob("ratings[12]_*.csv")):
        lst = int(f.stem[7])
        raw = {}
        for r in read_csv(f):
            try:
                raw[(lst, int(r["item"]))] = float(r["rating"])
            except (KeyError, ValueError, TypeError):
                continue
        raw = {k: v for k, v in raw.items() if k in key}
        if len(raw) < 2 or statistics.pstdev(raw.values()) == 0:
            continue  # a participant who gave every sentence the same rating carries no information
        m, s = statistics.fmean(raw.values()), statistics.pstdev(raw.values())
        z[f.stem] = {k: (v - m) / s for k, v in raw.items()}
    if not z:
        lines.append("No rating sheets found (archive/human_study/responses/ratings<1|2>_<participant>.csv).\n")
        return
    runs = model_runs()
    lines += ["## Ratings (1–7, z-scored per participant)\n", f"{len(z)} participants.\n",
              "| Phenomenon | Acceptable (z) | Unacceptable (z) | Difference | Participants rating acceptable higher |",
              "|---|---:|---:|---:|---:|"]
    human_diff = {}
    for ph in RELEASE_PHENOMENA:
        acc = [v for zs in z.values() for k, v in zs.items() if key[k]["phenomenon"] == ph and key[k]["shown"] == "grammatical"]
        una = [v for zs in z.values() for k, v in zs.items() if key[k]["phenomenon"] == ph and key[k]["shown"] == "ungrammatical"]
        higher = total = 0
        for zs in z.values():
            a = [v for k, v in zs.items() if key[k]["phenomenon"] == ph and key[k]["shown"] == "grammatical"]
            u = [v for k, v in zs.items() if key[k]["phenomenon"] == ph and key[k]["shown"] == "ungrammatical"]
            if a and u:
                total += 1
                higher += statistics.fmean(a) > statistics.fmean(u)
        if acc and una:
            human_diff[ph] = statistics.fmean(acc) - statistics.fmean(una)
            lines.append(f"| {ph} | {statistics.fmean(acc):+.2f} | {statistics.fmean(una):+.2f} | "
                         f"{human_diff[ph]:+.2f} | {higher}/{total} |")
    if runs and len(human_diff) > 2:
        pair_ids = defaultdict(set)
        for r in key.values():
            pair_ids[r["phenomenon"]].add(r["pair_id"])
        lines += ["", "Pearson's r between the human difference and each model's mean score difference "
                  "(grammatical − ungrammatical) on the rated pairs, across phenomena:", "",
                  "| Model | r |", "|---|---:|"]
        for name, df in runs.items():
            phs = [ph for ph in human_diff if any(i in df.index for i in pair_ids[ph])]
            model = [df.loc[[i for i in pair_ids[ph] if i in df.index], "diff"].mean() for ph in phs]
            lines.append(f"| {name} | {pearson([human_diff[ph] for ph in phs], model):+.2f} |")
    lines.append("")


def selftest():
    """Simulated annotators on the real sheets: checks parsing and the statistics."""
    study = ROOT / "archive" / "human_study"
    if not (study / "forced_choice_key.csv").exists():
        print("run archive/scripts/make_human_study.py first")
        return 1
    rng = random.Random(0)
    fails = 0

    def check(name, ok):
        nonlocal fails
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} {name}")

    check("alpha is 1 for perfect agreement", abs(krippendorff_nominal([["A", "A"], ["B", "B"], ["A", "A"]]) - 1) < 1e-9)
    check("alpha is about 0 for chance agreement",
          abs(krippendorff_nominal([[rng.choice("AB"), rng.choice("AB")] for _ in range(4000)])) < 0.05)
    check("pearson of a line is 1", abs(pearson([1, 2, 3], [2, 4, 6]) - 1) < 1e-9)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        key = read_csv(study / "forced_choice_key.csv")
        for who, p_right in (("a1", 1.0), ("a2", 0.9), ("a3", 0.9)):
            with open(tmp / f"fc_{who}.csv", "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["item", "answer"])
                for r in key:
                    right = r["grammatical"]
                    w.writerow([r["item"], right if rng.random() < p_right else "AB".replace(right, "")])
        rkey = read_csv(study / "ratings_key.csv")
        for lst in (1, 2):
            for who in ("p1", "p2", "p3"):
                with open(tmp / f"ratings{lst}_{who}.csv", "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["item", "rating"])
                    for r in rkey:
                        if int(r["list"]) == lst:
                            base = 6 if r["shown"] == "grammatical" else 2
                            w.writerow([r["item"], min(7, max(1, base + rng.choice([-1, 0, 0, 1])))])
        lines = []
        forced_choice(tmp, study / "forced_choice_key.csv", tmp, lines)
        ratings(tmp, study / "ratings_key.csv", lines)
        text = "\n".join(lines)
        check("forced-choice table has a perfect annotator", "| a1 | 320 | 100.0 |" in text)
        judg = read_csv(tmp / JUDGMENTS)
        check("per-pair counts cover every pair with three annotators", len(judg) == len(key) and all(r["annotators"] == "3" for r in judg))
        check("the counts reproduce the annotators' accuracy",
              sum(int(r["correct"]) for r in judg) == sum(int(r["correct"]) for r in read_csv(tmp / ANNOTATORS)))
        check("ratings table lists all phenomena", all(ph in text for ph in RELEASE_PHENOMENA))
        check("all six simulated participants (three per list) rate acceptable higher", "6/6" in text)
    print(f"\n{fails} failure(s)")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--study", default=str(ROOT / "archive" / "human_study"),
                   help="materials and keys of the study, with the private sheets in responses/")
    p.add_argument("--counts", default=str(ROOT / "results" / "human"), help="folder of the released counts")
    p.add_argument("--out", default=str(ROOT / "results" / "human" / "summary.md"))
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    study = Path(args.study)
    lines = ["# Human validation of UzBLiMP\n",
             "Written by `scripts/human_study_report.py`. Forced choice: from the per-pair and per-annotator counts in "
             f"`results/human/{JUDGMENTS}` and `results/human/{ANNOTATORS}` (the individual sheets are private).\n"]
    forced_choice(study / "responses", study / "forced_choice_key.csv", Path(args.counts), lines)
    ratings(study / "responses", study / "ratings_key.csv", lines)
    Path(args.out).write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
