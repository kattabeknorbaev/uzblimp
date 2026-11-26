"""Generate candidate minimal pairs from corpus sentences.

1. scan:  stream the corpus once, count every word form (the lexicon) and keep a
          seeded random sample of eligible sentences per phenomenon. Cached in
          data/cache/, so changing a rule doesn't need a new scan.
2. edit:  one function per phenomenon changes exactly one word of a grammatical
          sentence, or skips it with a reason.
3. write: data/pairs_v1_<phenomenon>.tsv (status "unchecked"), skip counts in
          results/make_pairs_summary.json, skipped sentences in data/cache/.

Every edit must pass:
- plausibility (as in TatBLiMP): the new word form occurs in the corpus ≥ --min-count times;
- TurkicNLP agrees on the changed morpheme (segmenter ABL/NEG; UPOS NOUN after numerals);
- scripts/validate_pairs.py (one place, apostrophes, length, ...).

    python scripts/make_pairs.py --corpus path/to/corpus.zip
"""
import argparse
import csv
import json
import pickle
import random
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from corpus_stats import A, L, NEG_VERB_RE, NUM_LAT, WORD_RE, Reservoir, iter_documents, split_sentences
from schema import COLUMNS, CYR_RE, OG_BAD_APOS_RE, OPTIONAL_COLUMNS, n_words
from validate_pairs import check_pair

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"


@dataclass
class Edit:
    bad: str | None  # ungrammatical sentence, or None when skipped
    why: str  # breaking operation if bad is set, else the skip reason


def skip(reason):
    return Edit(None, reason)


# ---------------------------------------------------------------- eligibility
CAPS_INSIDE = re.compile(r"\s(?!Siz)[^\W\d_a-zʻʼ]")  # a capitalised word after the first: names, places (polite Siz is fine)
BAD_CHARS = re.compile(r"[\d@«»\"“”„()\[\]{}:;/\\|<>…—–']|http|www|\s-\s|^-|-[\s.!?,]")


# Rules added 2026-10-08 after the first review round (results/review_round1.md):
NON_UZBEK = re.compile(r"[^\sA-Za-zʻʼ,.!?-]|[wW]|[cC](?!h)")  # R1: foreign letters (Candida, Kawamata)
CAP_IN_WORD = re.compile(r"(?<=[^\W\d_]|-)[A-Z]")  # R2: OCR/case errors (tiQ, MOgʻidan, al-Mustaʼin)
SPACES = re.compile(r"\s+")


def normalize(s):
    """R4: collapse runs of whitespace (they change model tokenization)."""
    return SPACES.sub(" ", s).strip()


def eligible(s):
    """Short, single, plain sentence without names, digits, quotes or dialogue dashes."""
    if not s or not s[0].isupper() or s[-1] not in ".!?":
        return False
    if sum(s.count(c) for c in ".!?") > 1:
        return False
    if CAPS_INSIDE.search(s) or BAD_CHARS.search(s) or OG_BAD_APOS_RE.search(s) or CYR_RE.search(s):
        return False
    if NON_UZBEK.search(s) or CAP_IN_WORD.search(s):
        return False
    return 4 <= n_words(s) <= 15


# ------------------------------------------------------- numeral_no_plural
NUM_TA_WORD_RE = re.compile(rf"\b(?:{NUM_LAT})ta\s+([^\W\d_]+(?:{A}[^\W\d_]+)*)", re.I)
CASE_SUFFIXES = ["ning", "dan", "ni", "ga", "ka", "qa", "da"]


def numeral_no_plural(s, ctx):
    ms = list(NUM_TA_WORD_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one numeral+ta")
    m = ms[0]
    if m.start() > 0 and s[m.start() - 1] == "-":
        return skip("hyphenated numeral (bitta-bitta, bir-ikkita)")
    if re.search(r"\bhar\s+$", s[:m.start()], re.I):
        return skip("quantifier har + numeral")
    noun = m.group(1)
    low = noun.lower()
    if "lar" in low:
        return skip("noun already contains -lar")
    # bare noun → noun+lar; noun+CASE → noun+lar+CASE (dative after -lar is always -ga)
    forms = [low + "lar"] + [low[:-len(sf)] + "lar" + ("ga" if sf in ("ka", "qa") else sf)
                             for sf in CASE_SUFFIXES if low.endswith(sf) and len(low) - len(sf) >= 2]
    form = next((f for f in forms if ctx.lex[f] >= ctx.min_count), None)
    if form is None:
        return skip("plural form not attested in corpus")
    if ctx.an.upos_of(s, noun) != "NOUN":
        return skip("word after numeral is not NOUN (TurkicNLP)")
    return Edit(s[:m.start(1)] + form + s[m.end(1):], f"{noun} → {form}")


# --------------------------------------------------------------- npi_hech
VOWELS = "aeiou"
NEG_RULES = [  # (negative verb ending, affirmative builder)
    (re.compile(rf"^({L}{{2,}}?)ma(di(?:m|ng|k|ngiz|lar)?)$"), lambda st, r: st + r),  # kelmadi → keldi
    (re.compile(rf"^({L}{{2,}}?)ma(gan{L}*)$"), lambda st, r: st + r),  # kelmagan(dim) → kelgan(dim)
    (re.compile(rf"^({L}{{2,}}?)ma(yapti{L}*)$"), lambda st, r: st + r),  # kelmayapti → kelyapti
    (re.compile(rf"^({L}{{2,}}?)ma(yotgan{L}*)$"), lambda st, r: st + r),  # kelmayotgan → kelyotgan
    (re.compile(rf"^({L}{{2,}}?)may(di|man|san|miz|siz|dilar)$"),  # kelmaydi → keladi, oʻqimaydi → oʻqiydi
     lambda st, r: st + ("y" if st[-1] in VOWELS or st.endswith("oʻ") else "a") + r),
]
TOKEN_RE = re.compile(rf"{L}+")


def _affirmative(word):
    low = word.lower()
    for rule, build in NEG_RULES:
        m = rule.match(low)
        if m:
            aff = build(m.group(1), m.group(2))
            return aff[0].upper() + aff[1:] if word[0].isupper() else aff
    return None


def npi_hech(s, ctx):
    low = s.lower()
    if s.endswith("?"):
        return skip("question (questions license hech)")
    hm = re.search(r"\bhech\b", low)
    if not hm:
        return skip("no hech")
    if re.search(rf"\bhech\s+bo{A}lmasa\b", low):
        return skip("idiom hech boʻlmasa")
    if re.search(rf"\b(?:emas|yo{A}q)\b", low):
        return skip("copula negation (emas/yoʻq)")
    neg = [w for w in TOKEN_RE.finditer(s, hm.end()) if _affirmative(w.group())]
    if not neg:
        return skip("no supported negated verb after hech")
    if len(neg) > 1 or len(NEG_VERB_RE.findall(s)) > 1:
        return skip("more than one negated word")
    w = neg[0]
    aff = _affirmative(w.group())
    if ctx.lex[aff.lower()] < ctx.min_count:
        return skip("affirmative form not attested in corpus")
    if "NEG" not in " ".join(ctx.an.labels(w.group().lower())):
        return skip("TurkicNLP doesn't label NEG")
    return Edit(s[:w.start()] + aff + s[w.end():], f"{w.group()} → {aff}")


# ------------------------------------------------------- postposition_case
POSTP_RE = re.compile(rf"\b({L}{{2,}}?)dan(\s+)(keyin|beri)\b", re.I)
# Dative pronouns are often arguments of the verb, which makes "X-ga keyin" grammatical
# ("unga keyin alam qilmasdi" = it wouldn't hurt him later), so skip them.
DATIVE_PRONOUNS = {"unga", "bunga", "shunga", "menga", "senga", "bizga", "sizga", "ularga", "bularga",
                   "shularga", "hammaga", "oʻshanga", "kimga", "nimaga", "oʻzimga", "oʻzingga", "oʻziga",
                   "oʻzimizga", "oʻzingizga", "oʻzlariga"}


def postposition_case(s, ctx):
    ms = list(POSTP_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one -dan keyin/beri")
    m = ms[0]
    if re.match(rf"\s+bo{A}l", s[m.end():], re.I):  # R3: "beri boʻlmoq" = be on the verge of
        return skip("idiom beri boʻl- (not the postposition)")
    base = m.group(1)
    if base.lower().endswith(("g", "gʻ")):
        return skip("g/gʻ-final stem: dative form unclear (toqqa?)")
    new = base + ("qa" if base.lower().endswith("q") else "ka" if base.lower().endswith("k") else "ga")
    old = base + "dan"
    if new.lower() in DATIVE_PRONOUNS:
        return skip("pronoun: dative reading likely grammatical (unga keyin …)")
    if ctx.lex[new.lower()] < ctx.min_count:
        return skip("dative form not attested in corpus")
    if "ABL" not in ctx.an.labels(old.lower()):
        return skip("TurkicNLP doesn't label ABL")
    return Edit(s[:m.start(1)] + new + s[m.start(2):], f"{old} → {new} ({m.group(3).lower()})")


# ------------------------------------------------------------ lexical_case
# Verbs with a lexical case on their object: qoʻrqmoq + ABL, ishonmoq + DAT. The object
# directly before the verb is put in the accusative (itdan qoʻrqadi → *itni qoʻrqadi).
LEXICAL_VERBS = {
    "ABL": re.compile(rf"^qo{A}rq(?:a|d|ib|m|q|y|s)", re.I),  # not qoʻrqit-, qoʻrquv, qoʻrqoq, qoʻrqinch
    "DAT": re.compile(r"^ishon(?:a|d|ib|m|g|y|s)", re.I),  # not ishonch
}
# Pronoun accusatives are irregular (undan/unga → uni, not *unni).
PRONOUN_ACC = {"men": "meni", "sen": "seni", "un": "uni", "bun": "buni", "shun": "shuni",
               "biz": "bizni", "siz": "sizni", "ular": "ularni", "bular": "bularni", "shular": "shularni"}


def lexical_case(s, ctx):
    toks = list(TOKEN_RE.finditer(s))
    hits = []
    for k in range(1, len(toks)):
        verb, obj = toks[k].group(), toks[k - 1].group()
        if s[toks[k - 1].end():toks[k].start()].strip():  # punctuation between them
            continue
        for case, vre in LEXICAL_VERBS.items():
            low = obj.lower()
            if not vre.match(verb):
                continue
            if case == "ABL" and low.endswith("dan"):
                base = low[:-3]
            elif case == "DAT" and low.endswith(("ga", "ka", "qa")):
                base = low[:-2] if low.endswith("ga") else low[:-1]  # qishloqqa → qishloq
            else:
                continue
            hits.append((toks[k - 1], base, case, verb))
    if len(hits) != 1:
        return skip("not exactly one object + qoʻrq-/ishon-")
    tok, base, case, verb = hits[0]
    if len(base) < 2:
        return skip("stem too short")
    acc = PRONOUN_ACC.get(base, base + "ni")
    if ctx.lex[acc] < ctx.min_count:
        return skip("accusative form not attested in corpus")
    # TurkicNLP labels ABL reliably but not DAT after q/k or on pronouns (senga → '?'),
    # so the dative object is checked through the lexicon only.
    if case == "ABL" and "ABL" not in " ".join(ctx.an.labels(tok.group().lower())):
        return skip("TurkicNLP doesn't label ABL")
    new = acc[0].upper() + acc[1:] if tok.group()[0].isupper() else acc
    return Edit(s[:tok.start()] + new + s[tok.end():], f"{tok.group()} → {new} ({verb}: {case} → ACC)")


# ------------------------------------------------------- dative_allomorphy
# Dative is -qa after q and -ka after k (qishloqqa, eshikka); the bad form uses -ga.
# The bad form is a spelling error, not a real word: this is the morphophonology layer
# TatBLiMP leaves out (its §8), so only the good form has to be attested.
DATIVE_QK = re.compile(rf"\b({L}{{2,}}?(?:q|k))(qa|ka)\b", re.I)


def dative_allomorphy(s, ctx):
    ms = [m for m in DATIVE_QK.finditer(s) if m.group(1)[-1].lower() == m.group(2)[0].lower()]
    if len(ms) != 1:
        return skip("not exactly one -qqa/-kka dative")
    m = ms[0]
    word, stem = m.group(0), m.group(1)
    if ctx.lex[stem.lower()] < 5:
        return skip("stem not a frequent word (chekka, yakka are not datives)")
    # No TurkicNLP check: its segmenter leaves -qa/-ka unlabelled (qishloqqa → '?').
    # A real dative has common sister case forms (eshikka 2083 vs eshikda 3972); a word that
    # only looks like one doesn't (chekka 1101 vs chekda/chekni ≤ 17; yakka, tikka the same).
    sisters = max(ctx.lex[stem.lower() + c] for c in ("da", "ni", "dan", "ning"))
    if ctx.lex[word.lower()] > 3 * sisters:
        return skip("looks like a lexical word, not a dative (chekka, yakka)")
    bad = stem + "ga"
    return Edit(s[:m.start()] + bad + s[m.end():], f"{word} → {bad} (non-word: morphophonology)")


# -------------------------------------------------------- stem_alternation
# Stem-final q/k becomes gʻ/g before a vowel-initial possessive (oʻrtoq → oʻrtogʻim,
# yurak → yuragi). The bad form keeps q/k. Only stems that really alternate: the q/k form
# is a frequent word and at least 20× more frequent than the gʻ/g form (rules out togʻ, barg).
POSS_V = r"(?:i|im|ing|imiz|ingiz)(?:ni|ga|da|dan|ning)?"
STEM_ALT = re.compile(rf"\b({L}+?[aeiou]{A}?)(g{A}|g)({POSS_V})\b", re.I)


def stem_alternation(s, ctx):
    hits = []
    for m in STEM_ALT.finditer(s):
        pre, g, suf = m.group(1), m.group(2), m.group(3)
        if g == "g" and pre.lower().endswith(("da", "ta")):  # -dagi/-tagi (uydagi), not a stem
            continue
        alt = "q" if len(g) > 1 else "k"
        stem_g, stem_q = (pre + g).lower(), (pre + alt).lower()
        # alternating stem: the q/k form dominates (oʻrtoq 4407 vs oʻrtogʻ 9; but togʻ 11392 vs toq 786)
        if ctx.lex[stem_q] >= 5 and ctx.lex[stem_q] >= 20 * ctx.lex[stem_g]:
            hits.append((m, pre, alt, suf))
    if len(hits) != 1:
        return skip("not exactly one alternating q/k stem + possessive")
    m, pre, alt, suf = hits[0]
    if not any(lab.startswith("POSS") for lab in ctx.an.labels(m.group(0).lower())):
        return skip("TurkicNLP doesn't label a possessive")
    bad = pre + alt + suf
    return Edit(s[:m.start()] + bad + s[m.end():], f"{m.group(0)} → {bad} (non-word: morphophonology)")


# ---------------------------------------------------- suspended_affixation
# Coordinated finite past verbs keep their person suffix on the first conjunct:
# bordik va … boʻldik → *borgan va … boʻldik (KN, phenomena.md row 16). Only 1st/2nd
# person: for the 3rd person, -gan is itself a finite perfect (U kelgan = he has come).
SUSP_RE = re.compile(rf"\b({L}{{2,}}?)(dim|ding|dik|dingiz)(\s+(?:va|hamda)\s+)", re.I)
SUSP_SECOND = re.compile(rf"{L}+(?:dim|ding|dik|dingiz)\b", re.I)


def suspended_affixation(s, ctx):
    ms = list(SUSP_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one 1st/2nd-person past verb + va")
    m = ms[0]
    stem, pers = m.group(1), m.group(2).lower()
    later = [w.group().lower() for w in SUSP_SECOND.finditer(s, m.end())]
    if not any(w.endswith(pers) for w in later):  # the second conjunct must carry the same person
        return skip("no parallel second verb with the same person")
    # -gan assimilates after q/k (chiq → chiqqan, ek → ekkan), like the dative.
    low_stem = stem.lower()
    new = stem + ("qan" if low_stem.endswith("q") else "kan" if low_stem.endswith("k") else "gan")
    if ctx.lex[(stem + pers).lower()] < ctx.min_count or ctx.lex[new.lower()] < ctx.min_count:
        return skip("verb or -gan form not attested in corpus")
    return Edit(s[:m.start(1)] + new + s[m.start(3):], f"{stem + pers} → {new} (first conjunct)")


# ---------------------------------------------------- possessive_agreement
# The possessive suffix agrees with an overt genitive pronoun: mening akam → *mening akang.
# Persons are swapped 1SG↔2SG, 1PL↔2PL, 3→1SG; allomorphs after vowel / consonant.
POSS = {"1sg": ("m", "im"), "2sg": ("ng", "ing"), "3": ("si", "i"), "1pl": ("miz", "imiz"), "2pl": ("ngiz", "ingiz")}
GEN_PRON = {"mening": "1sg", "sening": "2sg", "uning": "3", "bizning": "1pl", "sizning": "2pl", "ularning": "3"}
SWAP = {"1sg": "2sg", "2sg": "1sg", "1pl": "2pl", "2pl": "1pl", "3": "1sg"}
CASES = ("", "ni", "ga", "da", "dan", "ning", "dek")
GEN_RE = re.compile(rf"\b(mening|sening|uning|bizning|sizning|ularning)\s+({L}+)", re.I)
VOWEL_END = re.compile(rf"(?:[aeiou]|o{A})$", re.I)
# Words that only look possessed (2026-10-16: mening ham → *hang ×9, ularning ikki koʻzini →
# *ikkim, ularning buni bajarmasliklari → *bunim): particles, bare numerals, pronoun case forms.
NOT_POSSESSED = {"ham", "kim", "hali", "ikki", "olti", "yetti", "ming", "keng", "teng",
                 "buni", "shuni", "uni", "meni", "seni", "bizni", "sizni", "ularni", "bularni", "shularni"}
NOT_POSSESSED_UPOS = {"ADV", "PART", "CCONJ", "SCONJ", "DET", "AUX", "INTJ"}


def possessive_agreement(s, ctx):
    ms = list(GEN_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one genitive pronoun + word")
    m = ms[0]
    pers, word = GEN_PRON[m.group(1).lower()], m.group(2)
    low = word.lower()
    if low in NOT_POSSESSED:
        return skip("word after the pronoun is a function word")
    for case in CASES:
        for after_vowel, suf in enumerate(POSS[pers][::-1]):  # try consonant (im) before vowel (m) forms
            ending = suf + case
            if not low.endswith(ending) or len(low) - len(ending) < 2:
                continue
            stem = low[:-len(ending)]
            if bool(VOWEL_END.search(stem)) != (suf == POSS[pers][0]):  # allomorph must fit the stem
                continue
            if ctx.lex[stem] < 5:
                continue
            new_suf = POSS[SWAP[pers]][0 if VOWEL_END.search(stem) else 1]
            new = stem + new_suf + case
            if ctx.lex[new] < ctx.min_count:
                return skip("swapped possessive form not attested in corpus")
            if ctx.an.upos_of(s, word) in NOT_POSSESSED_UPOS:
                return skip("word after the pronoun is not a noun (TurkicNLP UPOS)")
            new = new[0].upper() + new[1:] if word[0].isupper() else new
            return Edit(s[:m.start(2)] + new + s[m.end(2):], f"{m.group(1)} {word} → {new}")
    return skip("word after the pronoun has no matching possessive suffix")


# Top-up generators (2026-10-22) for phenomena whose v11 pairs (JM) fall short of 150. They
# re-implement JM's rules on our corpus, with extra guards. OK = the oʻ/gʻ apostrophe (U+02BB),
# the only one eligible sentences contain.
OK = "ʻ"
TOKEN = re.compile(rf"{L}+(?:-{L}+)*|[^\w\s]")


def _tokens(s):
    return [(m.group(), m.start(), m.end()) for m in TOKEN.finditer(s)]


# ---------------------------------------------------- ditransitive_dative
# The recipient of a give/tell/show verb is dative; the bad sentence makes it accusative, so the
# clause has two accusatives: unga kalitni berdi → *uni kalitni berdi (JM v11 rule 8).
DAT_ACC = {"menga": "meni", "senga": "seni", "unga": "uni", "bizga": "bizni", "sizga": "sizni", "ularga": "ularni"}
DAT_POSS = {"menga": "imni", "senga": "ingni", "unga": "ini", "bizga": "imizni", "sizga": "ingizni", "ularga": "ini"}
DITRANSITIVE = ("ber", "ayt", f"ko{OK}rsat", "yubor", "uzat", "tushuntir", f"o{OK}rgat", "topshir", "sot",
                f"bag{OK}ishla", "qaytar", "yetkaz", "uqtir")
NOT_RECIPIENT_NEXT = {"qaramay", f"ko{OK}ra", "nisbatan", "qarab", "qadar", "tomon", "binoan", f"o{OK}xshab",
                      "yarasha", "qarshi", f"bog{OK}liq", "yaqin", "tegishli", "aloqador", "loyiq", "xos", "teng"}


def ditransitive_dative(s, ctx):
    toks = _tokens(s)
    hits = [i for i, (w, _, _) in enumerate(toks) if w.lower() in DAT_ACC]
    if len(hits) != 1:
        return skip("not exactly one dative pronoun")
    i = hits[0]
    pron = toks[i][0]
    if i + 1 < len(toks) and toks[i + 1][0].lower() in NOT_RECIPIENT_NEXT:
        return skip("dative pronoun is the complement of a postposition/adjective (unga qaramay)")
    obj = verb = None
    for j in range(i + 1, min(i + 6, len(toks))):  # accusative object, then the verb, same clause
        w = toks[j][0].lower()
        if not w[0].isalpha():
            break
        if obj is None and w.endswith("ni") and len(w) > 3:
            obj = j
        elif obj is not None and w.startswith(DITRANSITIVE) and not re.match(
                rf"(?:{'|'.join(DITRANSITIVE)})(?:il|in)", w):  # not the passive (berildi)
            verb = j
            break
    if obj is None or verb is None or verb - obj > 3:
        return skip("no accusative object + give/tell/show verb after the pronoun")
    # The accusative pronoun could become the object of a verb form in between or of a verbal
    # noun object: sizga eshitganimni aytaman → sizni eshitganimni ("that I heard you") is fine.
    if any(re.search(r"(?:gan|kan|qan|digan|yotgan)$", toks[k][0].lower()) for k in range(i + 1, obj)) or \
            re.search(r"(?:gan|kan|qan|ish|sh|moq|maslik)\w*ni$", toks[obj][0].lower()):
        return skip("pronoun could be the object of a participle or verbal noun (sizni eshitganimni)")
    if obj == i + 1 and toks[obj][0].lower().endswith(DAT_POSS[pron.lower()]):
        return skip("uni kitobini could read as colloquial 'his book' (-ni = -ning)")
    acc = DAT_ACC[pron.lower()]
    acc = acc[0].upper() + acc[1:] if pron[0].isupper() else acc
    return Edit(s[:toks[i][1]] + acc + s[toks[i][2]:], f"{pron} → {acc}")


# ---------------------------------------------------------------- passives
# An agent phrase with tomonidan needs a passive verb: vazir tomonidan tayinlangan →
# *tayinlagan. Passive allomorphs (stem → passive): l-final consonant stem -in (ol → olin),
# other consonant -il (yoz → yozil), stem in -la -n (ishla → ishlan), other vowel -l (o'qi → o'qil).
# Not -ib converbs: in oʻt qoʻyilib oʻldirilgan the main verb stays passive, so qoʻyib may be fine.
PASSIVE_END = re.compile(rf"^(?:gan|di|adi|ayotgan|moqda|ish|ar|ajak){L}*$")


def _passive_splits(w):
    """Every (stem, passive morpheme, ending) split of w, shortest stem first (oʻldir+il+gan)."""
    for k in range(2, len(w)):
        for morph in ("il", "in", "l", "n"):
            if w.startswith(morph, k) and PASSIVE_END.match(w[k + len(morph):]):
                yield w[:k], morph, w[k + len(morph):]


def _passive_fits(stem, morph):
    last = stem[-1]
    if last in "aeiou" or stem.endswith(f"o{OK}"):
        return morph == ("n" if stem.endswith("la") else "l")
    return morph == ("in" if last == "l" else "il")


def passives(s, ctx):
    toks = _tokens(s)
    hits = [i for i, (w, _, _) in enumerate(toks) if w.lower() == "tomonidan"]
    if len(hits) != 1:
        return skip("not exactly one tomonidan")
    for j in range(hits[0] + 1, min(hits[0] + 6, len(toks))):
        w = toks[j][0]
        if not w[0].isalpha():
            break
        active = None
        for stem, morph, rest in _passive_splits(w.lower()):
            if not _passive_fits(stem, morph):
                continue
            if rest.startswith("gan") and stem[-1] in "qk":  # chiq + gan → chiqqan, like the dative
                rest = stem[-1] + "an" + rest[3:]
            if ctx.lex[stem + rest] < 5:
                continue
            if ctx.lex[stem + "moq"] < 2 and ctx.lex[stem + ("sh" if stem[-1] in "aeiou" else "ish")] < 5:
                continue  # the active stem must be a verb (boʻlgan is not boʻ + passive -l)
            active = stem + rest
            break
        if active is None:
            continue
        if ctx.an.upos_of(s, w) not in ("VERB", "AUX", "ADJ"):
            continue
        active = active[0].upper() + active[1:] if w[0].isupper() else active
        return Edit(s[:toks[j][1]] + active + s[toks[j][2]:], f"{w} → {active} (tomonidan + active)")
    return skip("no passive verb in the clause after tomonidan")


# -------------------------------------------------------- relative_clauses
# A relative clause before its noun uses the participle -gan, not the finite past -di:
# obod qilgan joy → *obod qildi joy (JM v11 rule 8). -kan/-qan after k/q (ekkan → ekdi).
PART_RE = re.compile(rf"^({L}+?)(gan|kan|qan)$")


def relative_clauses(s, ctx):
    toks = _tokens(s)
    cands = []
    for j in range(1, len(toks) - 1):  # a word before (the clause) and a word after (the noun)
        w, nxt = toks[j][0], toks[j + 1][0]
        m = PART_RE.match(w.lower())
        if not m or not nxt[0].isalpha():
            continue
        stem = m.group(1)
        if m.group(2) != "gan" and not stem.endswith(m.group(2)[0]):
            continue  # -kan/-qan only after k/q
        root = stem[:-2] if stem.endswith("ma") else stem  # kelmagan → kel
        infinitive = root + "moq"
        if ctx.lex[infinitive] < 2 and ctx.lex[root + ("sh" if root[-1] in "aeiou" else "ish")] < 5:
            continue  # not a verb (organ, vagon)
        finite = stem + "di"
        if ctx.lex[finite] < ctx.min_count:
            continue
        cands.append((j, w, finite))
    if len(cands) != 1:
        return skip("not exactly one -gan participle + word")
    j, w, finite = cands[0]
    if ctx.an.upos_of(s, toks[j + 1][0]) != "NOUN":
        return skip("word after the participle is not NOUN (TurkicNLP)")
    return Edit(s[:toks[j][1]] + finite + s[toks[j][2]:], f"{w} → {finite} (participle → finite before noun)")


# -------------------------------------------------------------- quantifiers
# har bir takes a singular noun: har bir sinf → *har bir sinflar (JM v11 rule 8).
HAR_BIR_RE = re.compile(rf"\bhar\s+bir\s+({L}+)", re.I)


def quantifiers(s, ctx):
    ms = list(HAR_BIR_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one har bir + word")
    m = ms[0]
    noun = m.group(1)
    low = noun.lower()
    if "lar" in low or low.startswith("bir"):
        return skip("word already plural, or har birimiz")
    # -lar goes before a case suffix or -dagi (uyda → uylarda, guruhdagi → guruhlardagi, not
    # uydalar / guruhdagilar), so try those splits first
    forms = [low[:-len(sf)] + "lar" + ("ga" if sf in ("ka", "qa") else sf)
             for sf in ["dagi"] + CASE_SUFFIXES if low.endswith(sf) and ctx.lex[low[:-len(sf)]] >= 5]
    forms = forms or [low + "lar"]
    form = next((f for f in forms if ctx.lex[f] >= ctx.min_count), None)
    if form is None:
        return skip("plural form not attested in corpus")
    if ctx.an.upos_of(s, noun) != "NOUN":
        return skip("word after har bir is not NOUN (TurkicNLP)")
    return Edit(s[:m.start(1)] + form + s[m.end(1):], f"har bir {noun} → {form}")


# ------------------------------------------------------------ nominalization
# Modal predicates take the -ish verbal noun, not the -gan participle: murojaat etish kerak →
# *murojaat etgan kerak (JM v11 rule 8). Only a bare -ish/-sh directly before the modal.
MODALS = ("kerak", "lozim", "mumkin", "zarur", "shart")


def nominalization(s, ctx):
    toks = _tokens(s)
    cands = []
    for j in range(1, len(toks) - 1):
        if toks[j + 1][0].lower() not in MODALS:
            continue
        w = toks[j][0].lower()
        for suf in ("ish", "sh"):  # try both splits: oʻq+ish fails, oʻqi+sh (oʻqimoq) works
            stem = w[:-len(suf)]
            if not w.endswith(suf) or len(stem) < 2:
                continue
            vowel_end = stem[-1] in "aeiou" or stem.endswith(f"o{OK}")
            if (suf == "sh") != vowel_end or ctx.lex[stem + "moq"] < 2:
                continue  # -sh after vowels, -ish after consonants; the stem must be a verb
            gan = stem + ("qan" if stem[-1] == "q" else "kan" if stem[-1] == "k" else "gan")
            if ctx.lex[gan] >= ctx.min_count:
                cands.append((j, gan))
                break
    if len(cands) != 1:
        return skip("not exactly one -ish verbal noun + modal")
    j, gan = cands[0]
    w = toks[j][0]
    gan = gan[0].upper() + gan[1:] if w[0].isupper() else gan
    return Edit(s[:toks[j][1]] + gan + s[toks[j][2]:], f"{w} {toks[j + 1][0]} → {gan} (-ish → -gan before a modal)")


GENERATORS = {  # phenomenon: (prefilter on the lowercased sentence, edit function)
    "numeral_no_plural": (re.compile(rf"\b(?:{NUM_LAT})ta\s"), numeral_no_plural),
    "npi_hech": (re.compile(r"\bhech\b"), npi_hech),
    "postposition_case": (re.compile(r"dan\s+(?:keyin|beri)\b"), postposition_case),
    "lexical_case": (re.compile(rf"(?:dan\s+qo{A}rq|(?:ga|ka|qa)\s+ishon)"), lexical_case),
    "dative_allomorphy": (re.compile(r"\w(?:qqa|kka)\b"), dative_allomorphy),
    "stem_alternation": (re.compile(rf"[aeiou]{A}?g{A}?(?:i|im|ing|imiz|ingiz)\b"), stem_alternation),
    "suspended_affixation": (re.compile(r"(?:dim|ding|dik|dingiz)\s+(?:va|hamda)\s"), suspended_affixation),
    "possessive_agreement": (re.compile(r"\b(?:mening|sening|uning|bizning|sizning|ularning)\s"), possessive_agreement),
    "ditransitive_dative": (re.compile(r"\b(?:menga|senga|unga|bizga|sizga|ularga)\s.*\wni\b"), ditransitive_dative),
    "passives": (re.compile(r"\btomonidan\b"), passives),
    "relative_clauses": (re.compile(rf"\w(?:gan|kan|qan)\s+{L}"), relative_clauses),
    "quantifiers": (re.compile(r"\bhar\s+bir\s"), quantifiers),
    "nominalization": (re.compile(r"\w(?:ish|sh)\s+(?:kerak|lozim|mumkin|zarur|shart)\b"), nominalization),
}
# Balance: (key from the edit note, max share of --n per key). Without it 65% of
# possessive pairs used "uning" and 5% "bizning".
STRATA = {"possessive_agreement": (lambda note: note.split()[0].lower(), 0.25)}

# Cheap substring test before sentence splitting: a line without any of these can't match.
KEYWORDS = ("ta ", "hech", "keyin", "beri", "qoʻrq", "ishon", "qqa", "kka", "gi", "gʻi",
            " va ", " hamda ", "ning ", "nga ", "zga ", "larga ", "tomonidan", "gan ", "kan ", "qan ", "har bir",
            "kerak", "lozim", "mumkin", "zarur", "shart")


# ------------------------------------------------------------------- scan
def scan(corpus, phenomena, pool_size, seed, limit_docs):
    t0 = time.time()
    lex = Counter()
    pools = {ph: Reservoir(pool_size, f"{seed}-{ph}") for ph in phenomena}
    eligible_n = Counter()
    seen = set()
    skipped = Counter()
    for n_docs, (part, doc, lines) in enumerate(iter_documents(corpus, skipped), 1):
        for ln, line in enumerate(lines, 1):
            low = line.lower()
            lex.update(WORD_RE.findall(low))
            if not any(k in low for k in KEYWORDS):
                continue
            for si, s in enumerate(split_sentences(line)):
                s = normalize(s)
                key = s.lower()
                if key in seen or not eligible(s):
                    continue
                for ph in phenomena:
                    if GENERATORS[ph][0].search(key):
                        seen.add(key)
                        eligible_n[ph] += 1
                        pools[ph].add((s, f"{doc}:{ln}:{si}"))
        if limit_docs and n_docs >= limit_docs:
            break
        if n_docs % 20000 == 0:
            print(f"  ... {n_docs:,} documents, {time.time() - t0:.0f}s", flush=True)
    lex = Counter({w: c for w, c in lex.items() if c >= 2})
    meta = {"corpus": str(corpus), "limit_docs": limit_docs, "pool_size": pool_size, "seed": seed,
            "eligible": dict(eligible_n), "scan_seconds": round(time.time() - t0)}
    return lex, {ph: r.items for ph, r in pools.items()}, meta


def load_or_scan(args):
    CACHE.mkdir(parents=True, exist_ok=True)
    meta_path, lex_path, pools_path = CACHE / "scan_meta.json", CACHE / "lexicon.pkl", CACHE / "pools.json"
    want = {"corpus": str(args.corpus), "limit_docs": args.limit_docs, "pool_size": args.pool, "seed": args.seed}
    if not args.rescan and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pools = json.loads(pools_path.read_text(encoding="utf-8"))
        if all(meta.get(k) == v for k, v in want.items()) and all(ph in pools for ph in args.phenomena):
            print(f"Using cached scan ({meta['scan_seconds']}s originally).")
            with open(lex_path, "rb") as f:
                return pickle.load(f), pools, meta
    print("Scanning corpus (lexicon + candidate pools) ...", flush=True)
    lex, pools, meta = scan(args.corpus, list(GENERATORS), args.pool, args.seed, args.limit_docs)
    with open(lex_path, "wb") as f:
        pickle.dump(lex, f)
    pools_path.write_text(json.dumps(pools, ensure_ascii=False), encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return lex, pools, meta


# ------------------------------------------------------------------- main
class Ctx:
    def __init__(self, lex, min_count):
        from tnlp import Analyzer  # loads TurkicNLP only when edits run
        self.lex, self.min_count, self.an = lex, min_count, Analyzer()


def generate(ph, pool, ctx, n, seed, used=frozenset()):
    rows, reasons, skipped, strata = [], Counter(), [], Counter()
    items = list(pool)
    random.Random(f"{seed}-{ph}-order").shuffle(items)
    for s, src in items:
        if len(rows) >= n:
            break
        s = normalize(s)
        if not eligible(s):  # re-check cached pools against rules added since the scan
            reasons["not eligible under current rules"] += 1
            continue
        if s.lower() in used:
            reasons["sentence already in another pair file (e.g. JM's v2)"] += 1
            continue
        e = GENERATORS[ph][1](s, ctx)
        if e.bad:
            first = ctx.an.upos(s)[:1]
            if first and first[0][1] == "PROPN":  # names at sentence start pass the capitals filter
                e = skip("starts with a proper noun (TurkicNLP)")
        if e.bad:
            row = {"id": f"{ph}-0000", "phenomenon": ph, "grammatical": s, "ungrammatical": e.bad,
                   "method": "corpus-edit", "source_id": src, "status": "unchecked", "notes": e.why}
            errs, _ = check_pair(row)
            if errs:
                e = skip("validator: " + errs[0])
        if e.bad and ph in STRATA:
            key_fn, share = STRATA[ph]
            key = key_fn(e.why)
            if strata[key] >= share * n:
                e = skip(f"balance: enough pairs with '{key}'")
            else:
                strata[key] += 1
        if e.bad:
            reasons["ok"] += 1
            rows.append(row)
        else:
            reasons[e.why] += 1
            skipped.append((e.why, s, src))
    return rows, reasons, skipped


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", required=True, help="the corpus zip (books/, legal/, wiki/)")
    p.add_argument("--phenomena", nargs="+", default=list(GENERATORS), choices=list(GENERATORS))
    p.add_argument("--n", type=int, default=250, help="pairs to write per phenomenon")
    p.add_argument("--pool", type=int, default=5000, help="sampled sentences per phenomenon")
    p.add_argument("--min-count", type=int, default=2, help="corpus count needed for a new word form")
    p.add_argument("--id-start", type=int, default=1001)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--limit-docs", type=int, help="scan only the first N documents (tests)")
    p.add_argument("--rescan", action="store_true")
    p.add_argument("--force", action="store_true", help="overwrite pair files that already have reviews")
    p.add_argument("--out-dir", default=str(ROOT / "data"))
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lex, pools, meta = load_or_scan(args)
    print(f"Lexicon: {len(lex):,} word forms (count ≥ 2). Eligible sentences: {meta['eligible']}")
    ctx = Ctx(lex, args.min_count)
    summary_path = ROOT / "results" / "make_pairs_summary.json"
    old = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary = {"meta": meta, "min_count": args.min_count, "phenomena": old.get("phenomena", {})}  # keep other runs
    for ph in args.phenomena:
        out = Path(args.out_dir) / f"pairs_v1_{ph}.tsv"
        if out.exists() and not args.force:
            with open(out, encoding="utf-8", newline="") as f:
                reviewed = sum(r["status"] != "unchecked"
                               for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
            if reviewed:
                print(f"\n{ph}: {out.name} already has {reviewed} reviewed pairs; not overwritten (--force to override).")
                continue
        used = set()  # grammatical sentences of this phenomenon in the other pair files
        for f in Path(args.out_dir).glob("pairs_v*.tsv"):
            if f.resolve() != out.resolve():
                with open(f, encoding="utf-8", newline="") as fh:
                    used |= {normalize(r["grammatical"]).lower() for r in csv.DictReader(
                        fh, delimiter="\t", quoting=csv.QUOTE_NONE) if r["phenomenon"] == ph}
        rows, reasons, skipped = generate(ph, pools[ph], ctx, args.n, args.seed, frozenset(used))
        for k, row in enumerate(rows):
            row["id"] = f"{ph}-{args.id_start + k:04d}"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS + OPTIONAL_COLUMNS, delimiter="\t",
                               lineterminator="\n", quoting=csv.QUOTE_NONE, extrasaction="ignore", restval="")
            w.writeheader()
            w.writerows(rows)
        with open(CACHE / f"skips_{ph}.tsv", "w", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="\t", lineterminator="\n").writerows([("reason", "sentence", "source")] + skipped)
        tried = sum(reasons.values())
        summary["phenomena"][ph] = {"pool": len(pools[ph]), "tried": tried, "generated": len(rows),
                                    "reasons": dict(reasons.most_common())}
        print(f"\n{ph}: {len(rows)} pairs → {out.name} (tried {tried} of {len(pools[ph])} sampled)")
        for r, c in reasons.most_common():
            print(f"   {c:5}  {r}")
    summary_path.parent.mkdir(exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
