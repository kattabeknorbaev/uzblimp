"""Build data/pilot_3alphabets.tsv: 13 minimal pairs in three Uzbek alphabets.

3 sanity pairs + one example pair per top-10 phenomenon (notes/phenomena.md,
ranking of 2026-10-06). All Uzbek sentences are drafts pending Kattabek's check.
Cyrillic comes from TurkicNLP (scripts/alphabets.py), reformed Latin from our
4-rule converter; both must be checked by hand.

    python scripts/make_pilot.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from alphabets import to_cyrillic, to_reformed  # noqa: E402

# (id, phenomenon, source, good, bad) in current Latin (oʻ/gʻ = U+02BB)
PAIRS = [
    ("s1", "postposition_case_keyin", "sanity", "Darsdan keyin uchrashamiz.", "Darsga keyin uchrashamiz."),
    ("s2", "hech_negation_polarity", "sanity", "Hech kim kelmadi.", "Hech kim keldi."),
    ("s3", "numeral_no_plural", "sanity", "Uchta kitob oldim.", "Uchta kitoblar oldim."),
    ("t01", "numeral_no_plural", "rank 1 (row 17)", "Ikkita bola oʻynayapti.", "Ikkita bolalar oʻynayapti."),
    ("t02", "person_agreement", "rank 2 (row 21)", "Men ertaga kelaman.", "Men ertaga kelasan."),
    ("t03", "possessive_agreement", "rank 3 (row 22)", "Mening akam shifokor.", "Mening akang shifokor."),
    ("t04", "hech_npi_insertion", "rank 4 (row 10)", "Koʻpchilik oldida qoʻshiq aytdim.",
     "Koʻpchilik oldida hech qachon qoʻshiq aytdim."),
    ("t05", "lexical_case", "rank 5 (row 2)", "Ukam itdan qoʻrqadi.", "Ukam itni qoʻrqadi."),
    ("t06", "anaphor_agreement", "rank 6 (row 1)", "Biz uyni oʻzimiz tozaladik.", "Biz uyni oʻzingiz tozaladik."),
    ("t07", "binding", "rank 7 (row 4)", "Men oʻzimni oynada koʻrdim.", "Men meni oynada koʻrdim."),
    ("t08", "postposition_case_beri", "rank 8 (row 18)", "Ertalabdan beri yomgʻir yogʻyapti.",
     "Ertalabga beri yomgʻir yogʻyapti."),
    ("t09", "ditransitive_dative", "rank 9 (row 3)", "Oʻqituvchi oʻquvchilarga yangi mavzuni tushuntirdi.",
     "Oʻqituvchi oʻquvchilarni yangi mavzuni tushuntirdi."),
    ("t10", "stem_q_to_gh", "rank 10 (row 7)", "Bu mening oʻrtogʻim.", "Bu mening oʻrtoqim."),
]

COLUMNS = ["id", "phenomenon", "source", "good_latn", "bad_latn", "good_cyrl", "bad_cyrl",
           "good_reformed", "bad_reformed"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(__file__).parent.parent / "data" / "pilot_3alphabets.tsv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for pid, phen, src, good, bad in PAIRS:
            w.writerow([pid, phen, src, good, bad, to_cyrillic(good), to_cyrillic(bad),
                        to_reformed(good), to_reformed(bad)])
    print(f"Wrote {out} ({len(PAIRS)} pairs)")


if __name__ == "__main__":
    main()
