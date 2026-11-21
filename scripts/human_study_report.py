"""Score the returned sheets of the human validation study and write results/human_study.md.

Put the filled-in sheets in human_study/responses/ (any alphabet; the item numbers are the same):
    fc_<annotator>.csv                 forced choice: columns item, answer (A or B) [, unsure]
    ratings<1|2>_<annotator>.csv       ratings: columns item, rating (1-7); the digit is the list

Forced choice: accuracy per annotator and per phenomenon, majority-vote accuracy, mean pairwise agreement
and Krippendorff's alpha (nominal; it allows missing answers), and the accuracy of every scored model on
the same pairs. Ratings: z-scores per participant, mean rating of acceptable and unacceptable sentences
per phenomenon, the number of participants who rate acceptable sentences higher, and Pearson's r between
the human and the model differences across phenomena (as in TurBLiMP).

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
    """{key: per-pair DataFrame} for the current-Latin run of every scored model, if pandas is available."""
    try:
        from models import load_runs
    except ImportError:
        return {}
    return {key: df for (key, alphabet), df in load_runs().items() if alphabet == "Latin"}


def forced_choice(folder, key_file, lines):
    key = {int(r["item"]): r for r in read_csv(key_file)}
    answers = {}
    for f in sorted(folder.glob("fc_*.csv")):
        rows = {int(r["item"]): ANSWER.get((r.get("answer") or "").strip().upper()[:1]) for r in read_csv(f) if r.get("item")}
        answers[f.stem[3:]] = {i: a for i, a in rows.items() if a and i in key}
    if not answers:
        lines.append("No forced-choice sheets found (human_study/responses/fc_<annotator>.csv).\n")
        return
    lines += ["## Forced choice\n", f"{len(answers)} annotators, {len(key)} pairs.\n",
              "| Annotator | Answered | Accuracy (%) |", "|---|---:|---:|"]
    for name, ans in answers.items():
        ok = sum(a == key[i]["grammatical"] for i, a in ans.items())
        lines.append(f"| {name} | {len(ans)} | {100 * ok / len(ans):.1f} |")
    per_item = {i: [ans[i] for ans in answers.values() if i in ans] for i in key}
    majority = {i: Counter(v).most_common() for i, v in per_item.items() if v}
    clear = {i: m[0][0] for i, m in majority.items() if len(m) == 1 or m[0][1] > m[1][1]}  # ties are left out
    maj_ok = sum(lab == key[i]["grammatical"] for i, lab in clear.items())
    pairs_agree = [a == b for v in per_item.values() for a, b in itertools.combinations(v, 2)]
    lines += ["", f"- Majority vote agrees with the benchmark on {maj_ok} of {len(clear)} pairs "
              f"({100 * maj_ok / max(len(clear), 1):.1f}%; {len(majority) - len(clear)} ties left out)."]
    if pairs_agree:
        lines.append(f"- Mean pairwise agreement {100 * sum(pairs_agree) / len(pairs_agree):.1f}%; "
                     f"Krippendorff's alpha {krippendorff_nominal(list(per_item.values())):.2f}.")
    runs = model_runs()
    head = "| Phenomenon | Pairs | Human mean | Majority |" + "".join(f" {k} |" for k in runs)
    lines += ["", head, "|---|---:|---:|---:|" + "---:|" * len(runs)]
    for ph in list(RELEASE_PHENOMENA) + ["All"]:
        items = [i for i, r in key.items() if ph == "All" or r["phenomenon"] == ph]
        ind = [a == key[i]["grammatical"] for i in items for a in per_item[i]]
        maj = [clear[i] == key[i]["grammatical"] for i in items if i in clear]
        cells = [f"{100 * sum(ind) / len(ind):.1f}" if ind else "–", f"{100 * sum(maj) / len(maj):.1f}" if maj else "–"]
        for df in runs.values():
            sel = df.loc[[key[i]["pair_id"] for i in items if key[i]["pair_id"] in df.index]]
            cells.append(f"{100 * sel.correct.mean():.1f}" if len(sel) else "–")
        lines.append(f"| {ph} | {len(items)} | " + " | ".join(cells) + " |")
    disputed = [i for i, lab in clear.items() if lab != key[i]["grammatical"]] + [i for i in majority if i not in clear]
    if disputed:
        lines += ["", "Pairs to re-examine (the majority disagrees with the benchmark, or the vote is tied): "
                  + ", ".join(sorted(key[i]["pair_id"] for i in disputed)) + "."]
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
        lines.append("No rating sheets found (human_study/responses/ratings<1|2>_<participant>.csv).\n")
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
    study = ROOT / "human_study"
    if not (study / "forced_choice_key.csv").exists():
        print("run scripts/make_human_study.py first")
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
        forced_choice(tmp, study / "forced_choice_key.csv", lines)
        ratings(tmp, study / "ratings_key.csv", lines)
        text = "\n".join(lines)
        check("forced-choice table has a perfect annotator", "| a1 | " in text and "| 100.0 |" in text)
        check("ratings table lists all phenomena", all(ph in text for ph in RELEASE_PHENOMENA))
        check("all six simulated participants (three per list) rate acceptable higher", "6/6" in text)
    print(f"\n{fails} failure(s)")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--study", default=str(ROOT / "human_study"))
    p.add_argument("--out", default=str(ROOT / "results" / "human_study.md"))
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    study = Path(args.study)
    lines = ["# Human validation of UzBLiMP\n",
             "Written by `scripts/human_study_report.py` from the sheets in `human_study/responses/`.\n"]
    forced_choice(study / "responses", study / "forced_choice_key.csv", lines)
    ratings(study / "responses", study / "ratings_key.csv", lines)
    Path(args.out).write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
