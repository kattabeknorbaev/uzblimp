"""Write the release files: one JSON Lines file per phenomenon and alphabet.

Reads data/benchmark/ (the source of truth) and writes data/jsonl/<script>/<phenomenon>.jsonl for
script = latn (current Latin), cyrl (Cyrillic) and latn_reformed (2026 reform), one pair per line.
Fields are listed in the README ("Data format"). oʻ/gʻ written with any other apostrophe are
normalized to U+02BB on the way out. Rerun after changing the benchmark, then run validate.py.

    python scripts/export_jsonl.py
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from schema import OG_BAD_APOS_RE, RELEASE_PHENOMENA, SCRIPT_FILES, tokens

ROOT = Path(__file__).resolve().parent.parent


def normalize_apostrophes(text):
    """oʻ/gʻ followed by ', ’, ‘, `, ʼ or ´ → U+02BB (the glottal-stop ʼ after other letters stays)."""
    return OG_BAD_APOS_RE.sub(lambda m: m.group(0)[0] + "ʻ", text)


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def records(rows, script, meta):
    """Release records for one alphabet; method, source and reviewer come from the Latin file."""
    for row in rows:
        m = meta[row["id"]]
        good, bad = row["grammatical"], row["ungrammatical"]
        if script == "latn":
            good, bad = normalize_apostrophes(good), normalize_apostrophes(bad)
        name, field = RELEASE_PHENOMENA[row["phenomenon"]]
        # A pair counts as verified only when a linguist has checked it (a `verifier` column in
        # the benchmark TSV, none yet); `reviewer` is the native speaker who reviewed it.
        verifier = (m.get("verifier") or "").strip() or None
        rec = {
            "pair_id": row["id"],
            "paradigm": row["phenomenon"],
            "phenomenon": name,
            "field": field,
            "sentence_good": good,
            "sentence_bad": bad,
            "lexically_identical": sorted(tokens(good)) == sorted(tokens(bad)),
            "script": script,
            "source": m["method"],
            "source_id": m["source_id"],
            "verified": verifier is not None,
            "verifier_id": verifier,
            "reviewer": m["reviewer"],
        }
        if script != "latn":
            rec["converted_from"] = "latn"
        if script == "latn_reformed":
            rec["reform_category"] = row["reform_category"]
        yield rec


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--benchmark", default=str(ROOT / "data" / "benchmark"), help="folder with the benchmark TSVs")
    p.add_argument("--out", default=str(ROOT / "data" / "jsonl"), help="output folder")
    args = p.parse_args()

    latn = read_tsv(Path(args.benchmark) / SCRIPT_FILES["latn"])
    meta = {row["id"]: row for row in latn}
    for script, name in SCRIPT_FILES.items():
        rows = latn if script == "latn" else read_tsv(Path(args.benchmark) / name)
        by_phenomenon = defaultdict(list)
        for rec in records(rows, script, meta):
            by_phenomenon[rec["paradigm"]].append(rec)
        out = Path(args.out) / script
        out.mkdir(parents=True, exist_ok=True)
        for phenomenon, recs in sorted(by_phenomenon.items()):
            with open(out / f"{phenomenon}.jsonl", "w", encoding="utf-8", newline="\n") as f:
                for rec in recs:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{script}: {sum(map(len, by_phenomenon.values()))} pairs in {len(by_phenomenon)} files → {out}")


if __name__ == "__main__":
    main()
