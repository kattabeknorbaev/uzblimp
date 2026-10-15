# Second check of the reviewed pairs (for JM)

Kattabek has already reviewed these 6 phenomena (250 pairs each). You check the same pairs **independently**, which gives the agreement number for the paper and catches mistakes. Kattabek's answers are not in these files.

## Setup (once)
1. `git pull` the repo. You only need Python 3.10 or newer; there's nothing to install.
2. Use a real terminal (Windows Terminal, PowerShell or the VS Code terminal) so single keypresses work.

## Run
From the repo folder, one file at a time:

```
python scripts/review.py handcheck/blind/pairs_v1_numeral_no_plural_JM.tsv --reviewer JM
python scripts/review.py handcheck/blind/pairs_v1_npi_hech_JM.tsv --reviewer JM
python scripts/review.py handcheck/blind/pairs_v1_postposition_case_JM.tsv --reviewer JM
python scripts/review.py handcheck/blind/pairs_v1_lexical_case_JM.tsv --reviewer JM
python scripts/review.py handcheck/blind/pairs_v1_dative_allomorphy_JM.tsv --reviewer JM
python scripts/review.py handcheck/blind/pairs_v1_stem_alternation_JM.tsv --reviewer JM
```

**How much:** the rows are shuffled, so **the first 50 in each file are a random sample**. Do at least those 50 per file (300 pairs, about 1.5 hours), then quit with `q`. Doing more is welcome. Everything is saved after every key, and the tool continues where you stopped.

## Keys
| Key | Does |
|---|---|
| `y` | accept |
| `n` | reject, then type a reason number + Enter (below) |
| `e` | edit a sentence (it's re-checked before saving) |
| `s` | skip for now |
| `u` | undo your last answer |
| `q` | quit (all answers are already saved) |

Reject reasons: `1` the bad sentence is actually grammatical · `2` the good sentence is unnatural or wrong · `3` the change alters meaning, not grammar · `4` a name or personal data · `5` a dialect or colloquial form. You can also type a short reason.

## When to accept
Accept only if **the ✓ sentence is natural Uzbek** and **the ✗ sentence is clearly wrong because of the highlighted word**. If you hesitate, reject or skip.

| File | The ✗ sentence should be wrong because… |
|---|---|
| `numeral_no_plural` | the noun after a numeral got *-lar* (*uchta kitob → \*uchta kitoblar*) |
| `npi_hech` | the verb lost its negation although *hech* is there (*hech kim kelmadi → \*hech kim keldi*) |
| `postposition_case` | *keyin* / *beri* got *-ga* instead of *-dan* (*darsdan keyin → \*darsga keyin*). Watch out: if the verb itself takes *-ga*, the ✗ sentence may be fine (reason `1`). |
| `lexical_case` | *qoʻrqmoq* / *ishonmoq* got an *-ni* object (*itdan qoʻrqadi → \*itni qoʻrqadi*) |
| `dative_allomorphy` | *-qa* / *-ka* became *-ga* (*qishloqqa → \*qishloqga*). This is a spelling-level error; accept if it's clearly wrong Uzbek. |
| `stem_alternation` | the *gʻ/g* went back to *q/k* (*oʻrtogʻim → \*oʻrtoqim*) |

## Keep it independent
- Don't open `data/pairs_v1_*.tsv` or `results/review_round1.md` (Kattabek's answers), and don't discuss specific pairs until you're done.
- When you're done, commit and push the `handcheck/blind/*_JM.tsv` files (or send them to Kattabek).
