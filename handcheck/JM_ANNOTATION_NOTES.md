# JM second-annotator labels (IAA 562)

Annotator: Javohir Matniyazov (JM), Khorezm dialect speaker judging literary/standard Uzbek.

## Files
- `handcheck_iaa_562_v12_JM_labels.csv` — clean IAA columns only (`good_ok`, `bad_is_wrong`, `fixed_bad`, `comment`)
- `handcheck_iaa_562_v12_JM.csv` — same labels plus LLM `suggested_*` columns used during review

## Label counts
- YY: 517
- YN: 33
- NY: 12
- NN: 0

## Method (important for the paper)
Most blank rows were filled from high-confidence LLM suggestions after a native-speaker pass on all flagged / medium-confidence / pattern-exception pairs. Report agreement as **LLM-preannotated, native-checked**, not as fully independent double annotation.

## Pair-set mismatch vs `handcheck_iaa_562.csv`
511 / 562 pair `id`s match the empty IAA template in this repo.
The other **51** are all `vowel_glide_y`: this sheet uses `v12_vowel_glide_y_*` ids; the template still has `v11_vowel_glide_y_*`.
Do **not** compute κ on those 51 until Kattabek confirms which vowel-glide set he annotated (or replace one file so both annotators share the same 562).

## Source
Built from the Numbers / Claude working sheet `handcheck_iaa_562_v12_JM.csv` (2026-10-19).
