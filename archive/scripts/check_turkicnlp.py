"""Check TurkicNLP's Uzbek transliteration against hand-written expectations.

Expected outputs are drafts by Claude (2026-10-06) and need a native-speaker check.
Prints one line per case: ok / FAIL, input, expected, got.

    python scripts/check_turkicnlp.py
"""
import sys

from turkicnlp.scripts import Script
from turkicnlp.scripts.transliterator import Transliterator

from alphabets import to_latin, to_reformed

LAT2CYR = Transliterator("uzb", Script.LATIN, Script.CYRILLIC)
CYR2LAT = Transliterator("uzb", Script.CYRILLIC, Script.LATIN)
LAT2CTS = Transliterator("uzb", Script.LATIN, Script.COMMON_TURKIC)

TEST_SENTENCES = [  # the three sanity pairs, current Latin
    ("Darsdan keyin uchrashamiz.", "Дарсдан кейин учрашамиз."),
    ("Darsga keyin uchrashamiz.", "Дарсга кейин учрашамиз."),
    ("Hech kim kelmadi.", "Ҳеч ким келмади."),
    ("Hech kim keldi.", "Ҳеч ким келди."),
    ("Uchta kitob oldim.", "Учта китоб олдим."),
    ("Uchta kitoblar oldim.", "Учта китоблар олдим."),
]

PROBES = [  # (Latin, expected Cyrillic, what it tests)
    ("Oʻzbekiston", "Ўзбекистон", "oʻ with U+02BB"),
    ("O'zbekiston", "Ўзбекистон", "oʻ with ASCII '"),
    ("O‘zbekiston", "Ўзбекистон", "oʻ with U+2018"),
    ("togʻ", "тоғ", "word-final gʻ"),
    ("yoʻq", "йўқ", "yoʻ is й+ў, not ё"),
    ("oʻqituvchi", "ўқитувчи", "oʻ + q"),
    ("shahar", "шаҳар", "sh, h→ҳ"),
    ("SHAHAR", "ШАҲАР", "all caps digraph"),
    ("mashhur", "машҳур", "sh + h"),
    ("Isʼhoq", "Исҳоқ", "tutuq separating s|h (no ъ in Cyrillic)"),
    ("taʼlim", "таълим", "tutuq → ъ"),
    ("sheʼr", "шеър", "tutuq after e"),
    ("ekin", "экин", "word-initial e → э"),
    ("kecha", "кеча", "e after consonant → е"),
    ("yer", "ер", "word-initial ye → е"),
    ("poyezd", "поезд", "ye after vowel → е"),
    ("obyekt", "объект", "ye after consonant → ъе"),
    ("yoz", "ёз", "yo → ё"),
    ("ketsa", "кетса", "t + -sa conditional (not ц)"),
    ("aytsa", "айтса", "t + -sa conditional (not ц)"),
    ("litsey", "лицей", "ts → ц in a loan"),
    ("sirk", "цирк", "Russian loan: s → ц"),
    ("sentabr", "сентябрь", "Russian loan: я, ь"),
    ("kompyuter", "компьютер", "Russian loan: ь"),
]

CYR_PROBES = [  # (Cyrillic, expected Latin in project convention, what it tests)
    ("Ўзбекистон", "Oʻzbekiston", "ў → oʻ"),
    ("тоғ", "togʻ", "ғ → gʻ"),
    ("ер", "yer", "word-initial е → ye"),
    ("поезд", "poyezd", "е after vowel → ye"),
    ("экин", "ekin", "э → e"),
    ("таълим", "taʼlim", "ъ → ʼ"),
    ("объект", "obyekt", "ъе → ye"),
    ("Исҳоқ", "Isʼhoq", "с+ҳ needs tutuq in Latin"),
    ("кетса", "ketsa", "plain t+s"),
    ("лицей", "litsey", "ц after vowel → ts"),
    ("цирк", "sirk", "word-initial ц → s"),
    ("сентябрь", "sentabr", "Russian loan"),
    ("компьютер", "kompyuter", "ь dropped"),
]

REFORMED_PROBES = [  # (current Latin, expected reformed Latin)
    ("Oʻzbekiston", "Özbekiston"),
    ("togʻ", "toğ"),
    ("Shahar", "Şahar"),
    ("uchrashamiz", "uçraşamiz"),
    ("mashhur", "maşhur"),
    ("Isʼhoq", "Isʼhoq"),  # tutuq-separated s|h must not become ş (assumption, unverified)
]


def row(ok, *cols):
    print(("ok  " if ok else "FAIL") + "  " + "  |  ".join(cols))
    return ok


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    n = fails = 0

    print("== Test sentences: Latin → Cyrillic → Latin ==")
    for lat, cyr in TEST_SENTENCES:
        got_cyr = LAT2CYR.transliterate(lat)
        back_raw = CYR2LAT.transliterate(got_cyr)
        n += 2
        fails += not row(got_cyr == cyr, lat, f"expected {cyr}", f"got {got_cyr}")
        fails += not row(back_raw == lat, f"round trip {got_cyr}", f"got {back_raw}")

    print("\n== Probe words: Latin → Cyrillic ==")
    for lat, cyr, note in PROBES:
        got = LAT2CYR.transliterate(lat)
        n += 1
        fails += not row(got == cyr, f"{lat} → {got}", f"expected {cyr}", note)

    print("\n== Probe words: Cyrillic → Latin (raw TurkicNLP output, then our convention) ==")
    for cyr, lat, note in CYR_PROBES:
        raw = CYR2LAT.transliterate(cyr)
        conv = to_latin(cyr)
        n += 1
        fails += not row(conv == lat, f"{cyr} → raw {raw!r} → {conv}", f"expected {lat}", note)

    print("\n== Reformed Latin (our rules) vs TurkicNLP Common Turkic (CTS) ==")
    for lat, ref in REFORMED_PROBES:
        got = to_reformed(lat)
        n += 1
        fails += not row(got == ref, f"{lat} → {got}", f"expected {ref}", f"CTS would give {LAT2CTS.transliterate(lat)}")
    for lat, _ in TEST_SENTENCES[:1] + TEST_SENTENCES[4:5]:
        print(f"info  {lat}  →  reformed {to_reformed(lat)}  |  CTS {LAT2CTS.transliterate(lat)}")

    print(f"\n{n - fails}/{n} as expected")


if __name__ == "__main__":
    main()
