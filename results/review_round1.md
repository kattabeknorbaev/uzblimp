# Review round 1 (2026-10-08)

Reviewer: KN (all 750 pairs). Files: `data/pairs_v1_{numeral_no_plural,npi_hech,postposition_case}.tsv`.

## Results

| Phenomenon | Generated | Accepted | Edited | Rejected | Acceptance | Review time |
|---|---|---|---|---|---|---|
| `numeral_no_plural` | 250 | 232 | 1 | 17 | **93.2%** | 93 min (2.7 pairs/min) |
| `npi_hech` | 250 | 231 | 0 | 19 | **92.4%** | 41 min (6.2 pairs/min) |
| `postposition_case` | 250 | 228 | 0 | 22 | **91.2%** | 56 min (4.4 pairs/min) |
| **Total** | **750** | **691** | **1** | **58** | **92.3%** | ~190 min (~3.9 pairs/min, ~235/hour) |

Times are first-to-last timestamps per file, so any breaks are included.

**All three phenomena exceed the 150-pair target** (233 / 231 / 228 usable).

## Rejection reasons (top 3 per phenomenon)

| Phenomenon | 1st | 2nd | 3rd |
|---|---|---|---|
| `numeral_no_plural` | good sentence unnatural/wrong (10) | dialect/colloquial (4) | bad sentence actually grammatical (3) |
| `npi_hech` | good sentence unnatural/wrong (13) | dialect/colloquial (6) | – |
| `postposition_case` | good sentence unnatural/wrong (16) | dialect/colloquial (6) | – |

**What lies behind them** (read from the 58 rejected pairs):
- **Corpus typos and OCR errors in the source sentence:**
  - typos: *toʻrta*, *npma*, *ikkor*
  - broken or hyphen-split words: *min-natdor*, *ra-diomuxbirman*, *bor  i*
  - capitals inside words: *tiQ*, *MOgʻidan*
- **Colloquial or dialect forms:** *opchiqib*, *deyolmadim*, *yuribmen*, *tuvmaydir*, *suvrat*.
- **Foreign words and names in wiki sentences:** *Candida albicans*, *Kawamataga*, *encomienda*.
- **A false postposition match:** *yigʻlamoqdan beri boʻlib*, where *beri boʻlmoq* means "be on the verge of".
- **Genuinely grammatical "bad" sentences (3, all numerals):** a dialect noun (*boʻzbola*), hyperbole (*yuzta qarindosh*), and a numeral before a list of names.
- **By source:** books 8.7% rejected, wiki 6.2%. Too close to justify preferring one source.

## Generator rule changes (`scripts/make_pairs.py`)

Each change was checked against the 750 reviewed pairs before adopting it:

| Rule | Change | Would catch (of 58 rejected) | Would lose (of 692 accepted) | Adopted |
|---|---|---|---|---|
| R1 | Skip sentences with non-Uzbek letters (c without h, w, ö, …) | 3 | 0 | ✅ |
| R2 | Skip capitals inside a word, incl. after a hyphen (OCR/case errors, names) | 2 | 2 | ✅ |
| R3 | Skip the *beri boʻl-* idiom in `postposition_case` | 1 | 0 | ✅ |
| R4 | Collapse runs of whitespace (normalization; affects model tokenization) | – | – | ✅ |
| – | Skip sentences with rare words (corpus count < 2 / 3 / 5) | 15 / 18 / 25 | 58 / 83 / 107 | ❌ ~20% precision: Uzbek agglutination makes most rare forms legitimate (*afsuslanmaydilar*) |

**Not filterable automatically:** colloquial/dialect forms (16 rejections) and odd-but-correct sentences. These stay with the reviewer.

## Data fixes
- `numeral_no_plural-1035`: KN edited the grammatical sentence (*otib → sotib*) but not the ungrammatical one, so the pair differed in two places. The same change was mirrored into the ungrammatical sentence.
- R4 applied to the existing files: 14 sentences had whitespace collapsed. Each is marked in `notes`.
- **Review tool:** an edit now offers to apply the same change to the other sentence.
- **Validator after the fixes:** CLEAN.

## Projection
- **Remaining work:** 13 phenomena × 150 accepted at ~92% acceptance ≈ 2,120 candidates.
- **Review time:** about **9 hours** at round-1 speed.
- **Caveat:** hand-written phenomena (ellipsis, scrambling, passives, nominalization) will be slower to *produce*, though not necessarily to review.
