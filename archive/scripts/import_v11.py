"""Import Javokhir Matniyazov's rule-generated pairs (data/external/uzblimp_v11.json).

Maps his phenomenon names to our slugs (notes/decisions.md #16–17), applies the same
filters as scripts/make_pairs.py (eligible sentence: 4–15 words, no names, quotes,
digits or dialogue; whitespace normalized) plus the validator and a duplicate check
against our pair files, and writes up to --n pairs per phenomenon to
data/pairs_v2_<slug>.tsv with status "unchecked". High-confidence pairs come first.

    python scripts/import_v11.py
"""
import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from make_pairs import eligible, normalize
from schema import ALL_PHENOMENA, COLUMNS, OPTIONAL_COLUMNS
from validate_pairs import check_pair

ROOT = Path(__file__).resolve().parent.parent
# v11 name → our slug. Not imported: npi_licensing, numeral_noun_number and
# argument_structure_transitive (already complete in our data), quantifiers
# ("bir necha", low confidence) and suspended_affixation (changes two places).
MAPPING = {
    "anaphor_agreement": "anaphor_agreement",
    "binding": "binding",
    "argument_structure_ditransitive": "ditransitive_dative",
    "nominalization": "nominalization",
    "subject_verb_agreement": "person_agreement",
    "passives": "passives",
    "relative_clauses": "relative_clauses",
    "determiners": "quantifiers",  # his rule is "har bir + N + lar"
    "vowel_glide_y": "vowel_glide",
    "postposition_order": "postposition_order",
}
CONF_ORDER = {"high": 0, "medium": 1, "low": 2}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", default=str(ROOT / "data" / "external" / "uzblimp_v11.json"))
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--id-start", type=int, default=2001)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    data = json.load(open(args.src, encoding="utf-8"))
    ours = set()
    for f in (ROOT / "data").glob("pairs_v[01]*.tsv"):
        with open(f, encoding="utf-8", newline="") as fh:
            ours |= {r["grammatical"].strip().lower() for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)}

    kept, reasons = defaultdict(list), defaultdict(Counter)
    for r in data:
        slug = MAPPING.get(r["phenomenon"])
        if slug is None:
            continue
        assert slug in ALL_PHENOMENA, slug
        good, bad = normalize(r["good"]), normalize(r["bad"])
        if not eligible(good):
            reasons[slug]["not eligible (length, names, quotes, dialogue …)"] += 1
            continue
        if good.lower() in ours:
            reasons[slug]["already in our pair files"] += 1
            continue
        row = {"id": f"{slug}-0000", "phenomenon": slug, "grammatical": good, "ungrammatical": bad,
               "method": "corpus-edit", "source_id": r["source"], "status": "unchecked",
               "notes": f"{r['good_cue']} → {r['bad_cue']}; JM v11 {r['id']} ({r['confidence']}); {r['method']}"}
        errs, _ = check_pair(row)
        if errs:
            reasons[slug]["validator: " + errs[0].split(":")[0][:40]] += 1
            continue
        kept[slug].append((CONF_ORDER.get(r["confidence"], 3), row))

    rng = random.Random(args.seed)
    print(f"{'phenomenon':22} {'eligible':>9} {'written':>8}   dropped")
    for slug, items in sorted(kept.items()):
        rng.shuffle(items)
        items.sort(key=lambda x: x[0])  # stable: shuffled within each confidence level
        rows = [row for _, row in items[:args.n]]
        for k, row in enumerate(rows):
            row["id"] = f"{slug}-{args.id_start + k:04d}"
        out = ROOT / "data" / f"pairs_v2_{slug}.tsv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS + OPTIONAL_COLUMNS, delimiter="\t", lineterminator="\n",
                               quoting=csv.QUOTE_NONE, extrasaction="ignore", restval="")
            w.writeheader()
            w.writerows(rows)
        print(f"{slug:22} {len(items):>9} {len(rows):>8}   " + "; ".join(f"{k}: {v}" for k, v in reasons[slug].most_common()))


if __name__ == "__main__":
    main()
