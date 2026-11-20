"""Convert Uzbek text between current Latin, Cyrillic and the reformed 2026 Latin.

- Cyrillic <-> current Latin: TurkicNLP's Transliterator (1995 tables). Its Latin
  output uses ASCII ' for oʻ/gʻ and for the tutuq belgisi; to_latin() maps these
  back to the project convention (oʻ/gʻ = U+02BB, tutuq = U+02BC).
- Reformed Latin: current Latin with oʻ→ö, gʻ→ğ, sh→ş, ch→ç, as given in the
  project brief. Nothing else is changed; other details of the reform (tutuq,
  capitalised digraphs in names, loanwords) are not verified.

Latin → Cyrillic is not fully rule-based (Russian loans such as sentabr →
сентябрь, sirk → цирк), so every converted sentence needs a human check. The loan
tables below cover the loans found in the benchmark, not Uzbek vocabulary in general.
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


# Fixes for TurkicNLP 0.4.0's Latin → Cyrillic (notes/turkicnlp.md):
_ZW = "⁠"  # word joiner: splits a digraph for TurkicNLP, removed afterwards
_C = "bcdfghjklmnpqrstvxzBCDFGHJKLMNPQRSTVXZ"
# 1. "ts" is ц only in loans (politsiya, revolyutsiya, litsey, word-initial tsex);
#    elsewhere it is t + s across a morpheme boundary (ketsa → кетса, ketsin → кетсин).
_TS_LOAN = re.compile(r"(?:(?<![^\W\d_])[Tt]s(?=[^\W\d_]))|(?:[Tt]s(?=i[aeiouy]|e))")
_TS_ANY = re.compile(r"([Tt])(?=s)")
# 2. A tutuq between s and h only keeps them apart (Isʼhoq → Исҳоқ, not Исъҳоқ).
_S_TUTUQ_H = re.compile(r"([sS])[ʼ'](?=[hH])")
# 3. ye after a consonant is a Russian loan: ъе after a prefix (obyekt → объект, inyeksiya →
#    инъекция), ье elsewhere (premyera → премьера, barelyef → барельеф).
_CONS_YE = re.compile(rf"(?<=[{_C}])(?=[yY][eE])")
_HARD_PREFIX = re.compile(r"(?<![^\W\d_])(?:ob|sub|ad|in|kon|dez|pod|raz)$", re.I)
_SOFT = ""  # placeholder for ь (TurkicNLP passes it through)
# 4. Month names: Russian loans with я / ь that no rule recovers.
_MONTHS = {"сентабр": "сентябрь", "октабр": "октябрь", "ноябр": "ноябрь", "декабр": "декабрь",
           "январ": "январь", "феврал": "февраль", "апрел": "апрель", "июн": "июнь", "июл": "июль"}
_MONTH_RE = re.compile(r"\b(" + "|".join(_MONTHS) + r")\b", re.I)
#    Loan stems with ь, any suffix after them (KN 2026-10-19: filmlarda → фильмларда).
_LOAN_STEMS = {"филм": "фильм", "компютер": "компьютер"}
_LOAN_RE = re.compile(r"\b(" + "|".join(_LOAN_STEMS) + r")", re.I)
#    Loans that Latin spells with s, ts or a plain consonant where Cyrillic keeps the Russian ц, ь
#    (audit of all 10,021 word types of benchmark v1.1, 2026-11-20: функсия → функция, консерт → концерт,
#    палто → пальто ...). Keys are the transliterator's output; they match at the start of a word, with
#    any suffix after them.
_LOAN_PREFIXES = {
    "аксия": "акция", "функси": "функци", "инфекси": "инфекци", "консепси": "концепци",
    "конструкси": "конструкци", "лексия": "лекция", "проекси": "проекци", "реакси": "реакци",
    "санкси": "санкци", "консерт": "концерт", "принсип": "принцип", "сирконий": "цирконий",
    "инсектитсид": "инсектицид", "ретсипиент": "реципиент", "нитсше": "ницше", "монатсит": "монацит",
    "асбосемент": "асбоцемент", "асфалт": "асфальт", "гелминт": "гельминт", "палто": "пальто",
    "релс": "рельс", "баталон": "батальон", "судя": "судья", "фючерс": "фьючерс",
}
_LOAN_PREFIX_RE = re.compile(r"\b(" + "|".join(sorted(_LOAN_PREFIXES, key=len, reverse=True)) + r")", re.I)
#    Loans ending in ь: only the bare word is respelled. With a suffix, usage varies (медални, моделлари),
#    so suffixed forms are left as converted.
_LOAN_WORDS = {"спектакл": "спектакль", "медал": "медаль", "детал": "деталь", "модел": "модель", "рол": "роль",
               "княз": "князь", "алфа": "альфа", "сех": "цех", "сехлар": "цехлар"}
_LOAN_WORD_RE = re.compile(r"\b(" + "|".join(sorted(_LOAN_WORDS, key=len, reverse=True)) + r")\b", re.I)
# 5. n + gʻ is н + ғ (qoʻngʻiroq → қўнғироқ); TurkicNLP reads "ng" as нг and ʻ as ъ.
_N_GH = re.compile(f"([nN])(?=[gG][{_APOS}])")
# 6. Roman numerals stay Latin (XV asr → XV аср, not ХВ). Two letters or more, or one
#    letter before asr/jahon, so that initials (V. Lenin) are still converted.
_ROMAN = re.compile(r"(?<![^\W\d_])(?:(?=[IVXLC]{2})C{0,3}(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})"
                    r"|[IVX](?=[\s-]+(?:asr|jahon)))(?![^\W\d_])")


def to_cyrillic(latin: str) -> str:
    """Latin → Cyrillic via TurkicNLP, with the fixes above. Still not fully rule-based
    (sirk → цирк, sirkoniy → цирконий), so converted sentences need a human check."""
    t = _S_TUTUQ_H.sub(rf"\1{_ZW}", latin)
    loans = {m.start() for m in _TS_LOAN.finditer(t)}
    t = "".join(ch + _ZW if ch in "tT" and i + 1 < len(t) and t[i + 1] == "s" and i not in loans else ch
                for i, ch in enumerate(t))
    t = _CONS_YE.sub(lambda m: TUTUQ if _HARD_PREFIX.search(t[:m.start()]) else _SOFT, t)
    t = _N_GH.sub(rf"\1{_ZW}", t)
    parts = _ROMAN.split(t)
    romans = _ROMAN.findall(t)
    out = "".join(_LAT2CYR.transliterate(p) + (romans[i] if i < len(romans) else "")
                  for i, p in enumerate(parts))
    out = out.replace(_ZW, "").replace(_SOFT, "ь")

    def fixed(table):
        def sub(m):
            w = table[m.group(1).lower()]
            return w[0].upper() + w[1:] if m.group(1)[0].isupper() else w
        return sub
    out = _LOAN_RE.sub(fixed(_LOAN_STEMS), _MONTH_RE.sub(fixed(_MONTHS), out))
    return _LOAN_WORD_RE.sub(fixed(_LOAN_WORDS), _LOAN_PREFIX_RE.sub(fixed(_LOAN_PREFIXES), out))


def to_latin(cyrillic: str) -> str:
    out = _CYR2LAT.transliterate(cyrillic)
    out = re.sub(r"([oOgG])'", rf"\1{OKINA}", out)
    return out.replace("'", TUTUQ)


def to_reformed(latin: str) -> str:
    for pattern, repl in _REFORMED:
        latin = pattern.sub(repl, latin)
    return latin
