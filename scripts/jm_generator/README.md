# Javokhir Matniyazov's rule-based pair generator (v11/v12)

Source of `data/external/uzblimp_v11.json` and `data/external/uzblimp_v12.json`
(4,500 rule-generated pairs, 15 categories x 300, good sentences from `tahrirchi/uz-books-v2`, MIT).

- Mining: `common8.py` (sentence filter), `lex8.py` (word list), `mine8.py`
- Selection and filters: `build11.py` (v11), `build12.py` + `mine12_glide.py` (v12 vowel_glide_y)
- Full-corpus word counts: `wordfreq_full.py`, `wordfreq_merge.py`, lookup via `wf.py`
- What changed in v12 and why: `CHANGELOG_v12.md`

v12 = v11 with vowel_glide_y rebuilt (bad form drops the glide y, e.g. qutlayman -> *qutlaman,
instead of the v11 doubled-vowel form *qutlaaman). The other 14 categories are identical to v11.

The scripts expect the uz-books-v2 parquet shards and the word-count cache locally; those are not in the repo.
