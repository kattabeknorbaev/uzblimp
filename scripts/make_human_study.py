"""Build the sheets for a human validation study of UzBLiMP (see human_study/README.md).

Two designs, both drawn from the benchmark with a fixed seed and written in current Latin and Cyrillic:

- Forced choice (as in BLiMP's human validation): N pairs per phenomenon; the annotator sees the two
  sentences as A and B, in random order, and picks the correct one. Gives a human accuracy that can be
  set beside the models' and an agreement figure between independent annotators.
- Ratings (as in TurBLiMP and BLiMP-NL): M pairs per phenomenon in two lists. Each list shows one
  sentence of every pair, half of them the grammatical member, and the other list shows the other
  member, so nobody sees both sentences of a pair. Sentences are rated from 1 to 7.

The sheets carry no phenomenon labels and no pair ids; the key files stay with the organiser.

    python scripts/make_human_study.py
    python scripts/make_human_study.py --forced-choice 30 --ratings 6 --seed 2026
"""
import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import RELEASE_PHENOMENA  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILES = {"latn": "uzblimp.tsv", "cyrl": "uzblimp_cyrl.tsv"}


def read(name):
    with open(ROOT / "data" / "benchmark" / name, encoding="utf-8", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)}


def write(path, header, rows, sheet=False):
    # Sheets for annotators get a byte-order mark so that Excel opens the Uzbek letters correctly.
    with open(path, "w", encoding="utf-8-sig" if sheet else "utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--forced-choice", type=int, default=20, help="pairs per phenomenon in the forced-choice sheet")
    p.add_argument("--ratings", type=int, default=6, help="pairs per phenomenon in the rating lists (even number)")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--out", default=str(ROOT / "human_study"))
    args = p.parse_args()
    if args.ratings % 2:
        p.error("--ratings must be even (half of each phenomenon's pairs show the grammatical member in a list)")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data = {script: read(name) for script, name in FILES.items()}
    rng = random.Random(args.seed)

    # Disjoint samples per phenomenon: first the forced-choice pairs, then the rating pairs.
    fc, likert = [], []
    for ph in RELEASE_PHENOMENA:
        ids = sorted(i for i, r in data["latn"].items() if r["phenomenon"] == ph)
        picked = rng.sample(ids, args.forced_choice + args.ratings)
        fc += picked[:args.forced_choice]
        likert += [(i, k < args.ratings // 2) for k, i in enumerate(picked[args.forced_choice:])]

    # Forced choice: one order of items and one A/B assignment for both alphabets.
    rng.shuffle(fc)
    sides = [rng.choice("AB") for _ in fc]
    for script in FILES:
        rows = []
        for n, (pid, side) in enumerate(zip(fc, sides), 1):
            r = data[script][pid]
            a, b = (r["grammatical"], r["ungrammatical"]) if side == "A" else (r["ungrammatical"], r["grammatical"])
            rows.append([n, a, b, "", ""])
        write(out / f"forced_choice_{script}.csv", ["item", "sentence_A", "sentence_B", "answer", "unsure"], rows, sheet=True)
    write(out / "forced_choice_key.csv", ["item", "pair_id", "phenomenon", "grammatical"],
          [[n, pid, data["latn"][pid]["phenomenon"], side] for n, (pid, side) in enumerate(zip(fc, sides), 1)])

    # Ratings: list 1 shows the grammatical member of the pairs flagged True, list 2 the other member.
    key = []
    for lst in (1, 2):
        items = [(pid, "grammatical" if first == (lst == 1) else "ungrammatical") for pid, first in likert]
        rng.shuffle(items)
        for script in FILES:
            write(out / f"ratings_list{lst}_{script}.csv", ["item", "sentence", "rating"],
                  [[n, data[script][pid][shown], ""] for n, (pid, shown) in enumerate(items, 1)], sheet=True)
        key += [[lst, n, pid, data["latn"][pid]["phenomenon"], shown] for n, (pid, shown) in enumerate(items, 1)]
    write(out / "ratings_key.csv", ["list", "item", "pair_id", "phenomenon", "shown"], key)

    print(f"forced choice: {len(fc)} pairs ({args.forced_choice} per phenomenon), Latin and Cyrillic sheets")
    print(f"ratings: 2 lists of {len(likert)} sentences ({args.ratings} pairs per phenomenon), Latin and Cyrillic sheets")
    print(f"written to {out}")


if __name__ == "__main__":
    main()
