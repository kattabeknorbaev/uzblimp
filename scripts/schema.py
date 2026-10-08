"""Shared definitions for UzBLiMP pair files (see data/README.md)."""
import re

COLUMNS = ["id", "phenomenon", "grammatical", "ungrammatical", "method", "source_id", "status", "notes"]
OPTIONAL_COLUMNS = ["reviewer", "reviewed_at", "reason"]
METHODS = {"corpus-edit", "template", "hand-written"}
STATUSES = {"unchecked", "accepted", "rejected", "edited"}

# The 16 phenomena (notes/decisions.md). Value: short description.
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
    "ellipsis": "backward gapping keeps parallel order in both conjuncts",
    "scrambling": "no postverbal scrambling out of an embedded clause",
    "impersonal_passive": "impersonal passive of an intransitive takes an agent phrase",
    "numeral_no_plural": "noun after a numeral (+ta) stays singular",
    "postposition_case": "postposition governs a fixed case (-dan keyin, -dan beri)",
    "possessive_agreement": "possessive suffix agrees with the genitive possessor",
    "dative_allomorphy": "dative is -qa after q, -ka after k, -ga elsewhere",
}
# Phenomena whose pairs differ by word order: same words, different order.
WORD_ORDER = {"ellipsis", "scrambling"}

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
