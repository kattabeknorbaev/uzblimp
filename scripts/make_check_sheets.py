"""Write the two sheets the authors still have to fill in before submission (see handcheck/README.md):

- handcheck/exclusions_to_confirm.csv: the excluded pairs of data/benchmark/excluded.tsv with their sentences, so
  that each exclusion can be confirmed (keep_excluded = y) or reversed (n).
- handcheck/cyrillic_check_v1.2_remaining.csv: the Cyrillic spot check for the eight phenomena that were not yet
  checked, on the current (v1.2) text. It keeps the pairs sampled for handcheck/cyrillic_check_60.csv that are still
  in the benchmark and replaces the others by pairs drawn with a fixed seed from the same phenomenon.

    python scripts/make_check_sheets.py
"""
import csv
import glob
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = {  # observations from the readiness audit of 2026-11-22, for the authors' decision
    "relative_clauses-2066": "the first half of the reason does not fit (kirgan modifies joy, so it is a relative participle); "
                             "the second half (the ungrammatical member has a grammatical reading: 'Tok kirdi, va chiqqan joyda ...') may still justify the exclusion",
}
LOANWORD_NOTE = "Latin spelling of Russian ц: ts after a vowel (operatsiya, ofitsiant), s after a consonant (stansiya, differensial)"
LOANWORD_IDS = {"npi_hech-1167", "passives-2039", "postposition_case-1157", "suspended_affixation-1029"}  # ts against s


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:  # byte-order mark: Excel then reads the Uzbek letters correctly
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def exclusions():
    pairs = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "pairs_v*.tsv"))):
        for r in read_tsv(f):
            pairs.setdefault(r["id"], r)
    rows = []
    for r in read_tsv(ROOT / "data" / "benchmark" / "excluded.tsv"):
        p = pairs[r["id"]]
        note = NOTES.get(r["id"], LOANWORD_NOTE if r["id"] in LOANWORD_IDS else "")
        confirmed = "y" if "confirmed by the first author" in r["flagged_by"] else ""
        rows.append([r["id"], r["phenomenon"], r["reason"], r["flagged_by"], p["grammatical"], p["ungrammatical"], note, confirmed, ""])
    write_csv(ROOT / "handcheck" / "exclusions_to_confirm.csv",
              ["id", "phenomenon", "reason", "flagged_by", "grammatical", "ungrammatical", "note", "keep_excluded", "comment"], rows)
    return len(rows)


def cyrillic():
    latn = {r["id"]: r for r in read_tsv(ROOT / "data" / "benchmark" / "uzblimp.tsv")}
    cyrl = {r["id"]: r for r in read_tsv(ROOT / "data" / "benchmark" / "uzblimp_cyrl.tsv")}
    with open(ROOT / "handcheck" / "cyrillic_check_60.csv", encoding="utf-8-sig", newline="") as f:
        old = list(csv.DictReader(f))
    todo = [r for r in old if not (r["cyrillic_ok"] or "").strip()]
    sampled = {r["id"] for r in old}
    rng = random.Random(2026)
    done_file = ROOT / "handcheck" / "cyrillic_check_v1.2_remaining.csv"
    done = {}
    if done_file.exists():  # keep the answers already given when the sheet is rebuilt
        with open(done_file, encoding="utf-8-sig", newline="") as f:
            done = {r["id"]: (r["cyrillic_ok"], r["comment"]) for r in csv.DictReader(f)}
    rows, replaced = [], 0
    for ph in dict.fromkeys(r["phenomenon"] for r in todo):
        keep = [r["id"] for r in todo if r["phenomenon"] == ph and r["id"] in cyrl]
        need = sum(r["phenomenon"] == ph for r in todo) - len(keep)
        pool = sorted(i for i, r in cyrl.items() if r["phenomenon"] == ph and i not in sampled)
        new = rng.sample(pool, need)
        replaced += need
        for i in keep + new:
            ok, comment = done.get(i, ("", ""))
            rows.append([i, ph, latn[i]["grammatical"], cyrl[i]["grammatical"], latn[i]["ungrammatical"], cyrl[i]["ungrammatical"], ok, comment])
    write_csv(ROOT / "handcheck" / "cyrillic_check_v1.2_remaining.csv",
              ["id", "phenomenon", "latin_grammatical", "grammatical", "latin_ungrammatical", "ungrammatical", "cyrillic_ok", "comment"], rows)
    return len(rows), replaced


if __name__ == "__main__":
    n = exclusions()
    m, replaced = cyrillic()
    print(f"handcheck/exclusions_to_confirm.csv: {n} exclusions")
    print(f"handcheck/cyrillic_check_v1.2_remaining.csv: {m} pairs ({replaced} drawn anew because their pair left the benchmark)")
