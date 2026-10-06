"""Convert Uzbek text between current Latin, Cyrillic and the reformed 2026 Latin.

- Cyrillic <-> current Latin: TurkicNLP's Transliterator (1995 tables). Its Latin
  output uses ASCII ' for oʻ/gʻ and for the tutuq belgisi; to_latin() maps these
  back to the project convention (oʻ/gʻ = U+02BB, tutuq = U+02BC).
- Reformed Latin: current Latin with oʻ→ö, gʻ→ğ, sh→ş, ch→ç, as given in the
  project brief. Nothing else is changed; other details of the reform (tutuq,
  capitalised digraphs in names, loanwords) are not verified.

Latin → Cyrillic is not fully rule-based (Russian loans such as sentabr →
сентябрь, sirk → цирк), so every converted sentence needs a human check.
"""
import re

from turkicnlp.scripts import Script
from turkicnlp.scripts.transliterator import Transliterator

_LAT2CYR = Transliterator("uzb", Script.LATIN, Script.CYRILLIC)
_CYR2LAT = Transliterator("uzb", Script.CYRILLIC, Script.LATIN)

OKINA = "ʻ"  # ʻ in oʻ, gʻ
TUTUQ = "ʼ"  # ʼ tutuq belgisi
_APOS = "ʻ'’‘`"

_REFORMED = [
    (re.compile(f"O[{_APOS}]"), "Ö"), (re.compile(f"o[{_APOS}]"), "ö"),
    (re.compile(f"G[{_APOS}]"), "Ğ"), (re.compile(f"g[{_APOS}]"), "ğ"),
    (re.compile("S[Hh]"), "Ş"), (re.compile("sh"), "ş"),
    (re.compile("C[Hh]"), "Ç"), (re.compile("ch"), "ç"),
]


def to_cyrillic(latin: str) -> str:
    return _LAT2CYR.transliterate(latin)


def to_latin(cyrillic: str) -> str:
    out = _CYR2LAT.transliterate(cyrillic)
    out = re.sub(r"([oOgG])'", rf"\1{OKINA}", out)
    return out.replace("'", TUTUQ)


def to_reformed(latin: str) -> str:
    for pattern, repl in _REFORMED:
        latin = pattern.sub(repl, latin)
    return latin
