"""Shared definitions for UzBLiMP pair files (see data/README.md)."""
import re

COLUMNS = ["id", "phenomenon", "grammatical", "ungrammatical", "method", "source_id", "status", "notes"]
OPTIONAL_COLUMNS = ["reviewer", "reviewed_at", "reason"]
METHODS = {"corpus-edit", "template", "hand-written"}
STATUSES = {"unchecked", "accepted", "rejected", "edited"}

# The 16 core phenomena (notes/decisions.md, revised 2026-10-15). Value: short description.
PHENOMENA = {
    "anaphor_agreement": "reflexive oʻz- agrees with the subject in person/number",
    "lexical_case": "verb assigns a lexical case to its object (qoʻrqmoq + ABL)",
    "ditransitive_dative": "indirect object takes dative, not a second accusative",
    "binding": "reflexive, not a pronoun, inside its binding domain",
    "stem_alternation": "stem-final q/k becomes gʻ/g before a vowel-initial suffix",
    "npi_hech": "hech- words need a negated predicate",
    "suspended_affixation": "first conjunct keeps its finite person/tense suffix",
    "nominalization": "verb selects -ish/-moq or -gan complement",
    "person_agreement": "verb agrees in person with an overt pronoun subject",
    "passives": "an agent phrase (tomonidan) needs a passive verb",
    "relative_clauses": "a relative clause verb is a participle (-gan), not a finite verb",
    "quantifiers": "noun after har bir stays singular",
    "numeral_no_plural": "noun after a numeral (+ta) stays singular",
    "postposition_case": "postposition governs a fixed case (-dan keyin, -dan beri)",
    "possessive_agreement": "possessive suffix agrees with the genitive possessor",
    "dative_allomorphy": "dative is -qa after q, -ka after k, -ga elsewhere",
}
# Optional extras, reported separately from the 16.
EXTRA_PHENOMENA = {
    "vowel_glide": "vowel-final verb stems take -y- before -a- (ishlayman, not ishlaaman)",
    "postposition_order": "a postposition follows its noun (jamiyat haqida)",
}
# Dropped on 2026-10-15; their seed pairs stay in pairs_v0.tsv but aren't counted.
DROPPED_PHENOMENA = {
    "ellipsis": "backward gapping keeps parallel order in both conjuncts",
    "scrambling": "no postverbal scrambling out of an embedded clause",
    "impersonal_passive": "impersonal passive of an intransitive takes an agent phrase",
}
ALL_PHENOMENA = {**PHENOMENA, **EXTRA_PHENOMENA, **DROPPED_PHENOMENA}
# Phenomena whose pairs differ by word order: same words, different order.
WORD_ORDER = {"ellipsis", "scrambling", "postposition_order"}

# Release files (data/jsonl/<script>/<phenomenon>.jsonl, from export_jsonl.py, checked by validate.py).
# Readable name and BLiMP-style field of each core phenomenon. The field follows BLiMP where it has
# the same contrast (agreement and irregular forms: morphology; argument structure: syntax; NPI
# licensing: semantics); the other assignments are ours.
RELEASE_PHENOMENA = {
    "anaphor_agreement": ("Anaphor agreement", "morphology"),
    "binding": ("Binding", "syntax"),
    "dative_allomorphy": ("Dative allomorphy (-ga/-qa/-ka)", "morphology"),
    "ditransitive_dative": ("Ditransitive dative", "syntax"),
    "lexical_case": ("Lexical case", "syntax"),
    "nominalization": ("Nominalization", "syntax"),
    "npi_hech": ("NPI licensing (hech + negation)", "semantics"),
    "numeral_no_plural": ("No plural after numerals", "morphology"),
    "passives": ("Passives", "syntax"),
    "person_agreement": ("Subject agreement", "morphology"),
    "possessive_agreement": ("Possessive agreement", "morphology"),
    "postposition_case": ("Case after postpositions", "syntax"),
    "quantifiers": ("Quantifiers (har bir + singular)", "morphology"),
    "relative_clauses": ("Relative clauses", "syntax"),
    "stem_alternation": ("Stem alternation (q/k → gʻ/g)", "morphology"),
    "suspended_affixation": ("Suspended affixation", "morphology"),
}
FIELDS = {"morphology", "syntax", "semantics"}
RELEASE_VERSION = "v1.2"
# Release alphabet → benchmark TSV. Cyrillic and reformed Latin are converted from current Latin.
SCRIPT_FILES = {"latn": "uzblimp.tsv", "cyrl": "uzblimp_cyrl.tsv", "latn_reformed": "uzblimp_reformed.tsv"}

APOS_BAD = "'’‘`ʼ´"  # anything but U+02BB after o/g
OG_BAD_APOS_RE = re.compile(f"[oOgG][{APOS_BAD}]")
LAT_RE = re.compile(r"[A-Za-zÀ-ɏ]")
CYR_RE = re.compile(r"[Ѐ-ӿ]")
# Words keep internal ʻ/ʼ and hyphens; punctuation marks are separate tokens.
TOKEN_RE = re.compile(r"\w+(?:[ʻʼ'’-]\w+)*ʻ?|[^\w\s]")
WORD_RE = re.compile(r"\w")


def tokens(sentence):
    return TOKEN_RE.findall(sentence)


def n_words(sentence):
    return sum(1 for t in tokens(sentence) if WORD_RE.match(t))
