# Hand-check: second annotator

**`handcheck_iaa_562.csv` is the sheet to fill in.** It holds the 562 pairs that Kattabek also reviews in `scripts/review.py` (from `data/pairs_v2_*.tsv`). Comparing the two sets of answers gives the inter-annotator agreement reported in the paper.

## How to fill it in
- Follow `handcheck_guide.md` for `good_ok`, `bad_is_wrong`, `fixed_bad` and `comment`. Use **Y** / **N**.
- **Work independently.** Don't look at Kattabek's decisions (the `status` column in `data/pairs_v2_*.tsv`) or discuss pairs until the sheet is finished. Otherwise the agreement number means nothing.
- **The model's opinion (`mlm_suspicious`) is left out on purpose,** so it can't nudge your judgment.
- **Rows are shuffled across phenomena.** That's deliberate; just go top to bottom.
- Save as CSV (UTF-8) with the same file name.

## Afterwards
Run `python scripts/agreement.py handcheck/handcheck_iaa_562.csv --annotator JM`. It writes:
- `results/agreement_KN_JM.md`: raw agreement and Cohen's κ, overall and per phenomenon;
- `handcheck/disagreements_KN_JM.csv`: pairs to decide together.

## Other files
- `handcheck_1500.csv` / `.json`: the original 1,500-pair sheet (100 per v11 category). 679 of its pairs fail the benchmark filters (over 15 words, names, quotes) and aren't used, so they don't need checking.
- **Naming:** in this sheet, `determiners` (*har bir* + plural) is the benchmark's `quantifiers`, and `subject_verb_agreement` is `person_agreement`.

## Javokhir's returned sheet (2026-10-19)
`handcheck_iaa_562_v12_JM.csv` (semicolon-separated): all 562 rows judged. Notes from a first look:
- **Model-assisted:** it adds `suggested_*`, `suggestion_confidence`, `suggestion_note` and `judges_A_B` columns that look machine-generated; JM's `good_ok`/`bad_is_wrong` equal the suggestions in 544/562 rows, and some comments say "JM auto: override". **2026-10-20, KN:** JM says he reviewed every pair himself, so the sheet counts as the second annotator's judgment. For transparency the paper should still mention that the sheet came with model suggestions.
- **vowel_glide redesigned:** 51 v11 vowel_glide pairs are replaced by new `v12_vowel_glide_y_*` pairs whose bad form drops the glide (*quvlaymiz* → \**quvlamiz*, not \**quvlaamiz*); 3 more v11 vowel_glide bad sentences edited the same way. The other 508 rows are the pairs we sent.
- **Agreement not computed yet:** KN hasn't reviewed `pairs_v2_*` (0 pairs judged by both). `agreement.py` now reads semicolon CSVs.
