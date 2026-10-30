# UzBLiMP v12 (2026-10-15)

v12 = v11 with **vowel_glide_y rebuilt**. The other 14 categories are byte-identical to v11 and keep their v11 ids. v11 files are not modified.

## Why
Javohir's hand-check found that all 300 v11 vowel_glide_y bad forms (rule9) replace the glide y with a, doubling the vowel (qilmaydi → *qilmaadi, qutlayman → *qutlaaman). That "aa" is a surface cue, so a model can reject them without any grammar. In the full Latin corpus, 276/300 v11 bad words contain a doubled vowel absent from the good word, and 270/300 contain a character trigram seen in fewer than 1 in 10⁶ trigram tokens (`surface_scan_v11.tsv`).

## New rule (rule12)
bad = drop the glide y: qutlayman → *qutlaman, xohlaysiz → *xohlasiz, eslaymiz → *eslamiz. A pair is kept only if:
1. the bad word has **0 hits in the full tahrirchi/uz-books-v2 Latin corpus** (all 26 shards, every document, 10.5M types / 1.47B tokens). Cache: `cache/wordfreq_lat_full.tsv.gz` + `.sqlite`, built by `wordfreq_full.py` + `wordfreq_merge.py`, looked up via `wf.py`;
2. it has no known inflected reading. This is conservative; rejected are:
   - -ydi/-ydilar → -di/-dilar, a real past tense (qilmadi, ushladi);
   - -ysan → -san, conditional/colloquial (yashasan);
   - negative -ma- stems (-maman/-mamiz/-masiz, dialectal or verbal-noun -ma + possessive);
   - stems with nominal evidence (stem+ni/ning/lar/ga ≥ 5 hits), which would give a copula/possessive reading;
3. the good word has ≥20 hits and the stem is a verb (stem+sh / stem+moq attested).

Mined seeds must also pass these filters:
- the same sentence filter as v8–v11 (`common8.sents`);
- every word in the sentence has ≥20 hits;
- no likely typos or scan errors: the OCR swap check, the split-word check, and no word with a one-letter edit (or an added ʼ/ʻ) that is ≥30× more frequent, which catches tariflaymiz → taʼriflaymiz;
- the cue word is not repeated in the sentence, is not capitalised mid-sentence, and is ≤16 characters;
- one pair per book row; each cue word ≤3 times and each stem ≤5 times;
- round-robin across -man/-miz/-siz.

method = `rule12:V-stem+y+PERS -> *V-stem+PERS (...)`, confidence = high. Provenance is in `source` (shard:row).

## Result
- **v11 pairs that survived: 10/300.** Ids are kept, batch=`v12_from_v11`, and notes record the old 'aa' bad form.
- **Rejection reasons for the 290:**

| Reason | Pairs |
|---|---|
| -di/-dilar real past tense | 190 |
| bad form attested in the corpus | 63 |
| nominal stem | 28 |
| -san | 5 |
| negative -ma- | 4 |

  Per-pair detail is in `vowel_glide_y_v11_rejections.tsv`. Many 1st-person forms have a handful of hits (eslaman 2, oʻqiman 7, qaramiz 16), from typos or dialect, so they fail the strict 0-hit rule.
- **New pairs: 290** (ids `v12_vowel_glide_y_0001…0290`, batch=`v12_hf`), mined by `mine12_glide.py` from all Latin shards: 404,871 raw candidates, a clean pool of 12,398, 126 distinct cue words. **300/300 reached.** Suffix mix: -man 135, -miz 115, -siz 50.
- Stats: `vowel_glide_y_v12_stats.json`. Builder: `build12.py`.

## Outputs
- `uzblimp_v12.tsv`, `.csv` (UTF-8 BOM), `.json`, `uzblimp_v12_counts.tsv` (4,500 pairs: 2,700 high / 1,500 medium / 300 low).
- 3-script files (current translit, `python3 translit/make3.py v12`): `uzblimp_v12_3script.tsv`, `_latin.tsv`, `_cyrillic.tsv`, `_latin2026.tsv`, `_3script_exceptions.tsv`. The exceptions file has 18 rows, all Latin round-trip spelling variants.
- Minimal-pair check (`python3 translit/minpair_check.py v12` → `translit/minpair_issues_v12.tsv`): no pair collapses. The same 12 known flags as v11 (-ль/-лар spelling plus false positives) and **0 vowel_glide_y issues**.

## Is it harder? (vowel_glide_y only, all 300 pairs, CPU)

| model | metric | v11 | v12 |
|---|---|---|---|
| tahrirchi-bert-base (PLL) | acc / median margin | 99.7% / 12.1 | **95.0% / 7.1** |
| Goldfish uzn_latn_full | sum (Latin) | 100.0 | 95.7 |
| Goldfish uzn_cyrl_full | sum (Cyrillic) | 100.0 | 98.0 |
| Qwen2.5-0.5B fp32 | sum (Lat / Cyr / 2026) | 92.0 / 76.0 / 87.0 | **39.0 / 2.7 / 35.0** |
| Qwen2.5-0.5B fp32 | mean per token | 93.7 / 74.7 / 87.0 | 78.7 / 43.7 / 75.7 |
| Qwen2.5-0.5B fp32 | SLOR | 90.0 / 84.0 / 89.7 | 89.3 / 55.7 / 81.3 |
| Qwen2.5-0.5B fp32 | length-matched | 93.1 / 80.4 / 87.7 | 42.3 / 1.6 / 36.8 |

Results are in `v12_glide_pll_scores.tsv` and `eval/results/v12_glide/`.

- ⚠ **v12 vowel_glide_y is length-confounded.** Dropping y makes the bad word one character and usually one token shorter (median Δtok = +1, good longer), so summed log-prob favours the bad form. For small models, the drop under sum overstates "harder". Mean-per-token and SLOR are fairer. Add `vowel_glide_y` to `LENGTH_CONFOUNDED` in `eval/eval_blimp.py` before reporting (not done yet).
- The bad forms are still **non-words by design** (0 corpus hits), so a lexical-frequency cue remains. But it no longer has an orthographic one: in the v12 surface scan (`surface_scan_v12.tsv`), the 300 vowel_glide_y bad forms have 0 doubled vowels and 0 rare trigrams.
- Uzbek-specific models (BERT, Goldfish) still score ~95–98%. That's expected for a morphological glide error.

## Surface scan of the other 14 categories (report only, nothing changed) — `surface_scan_v11.py` → `surface_scan_v11.tsv`
Flags on bad-only words:
- NONWORD: 0 hits in the full corpus;
- RARE_TRIGRAM: a trigram seen in fewer than 1 in 10⁶ trigram tokens and absent from the good word;
- DOUBLE_VOWEL: a new aa/ii/uu/ee/oo.

| category | nonword | rare trigram | double vowel | verdict / proposal |
|---|---|---|---|---|
| anaphor, ditransitive, binding, npi, passives, postposition_order, quantifiers, subject_verb_agreement | 0 | 0 | 0 | clean: bad forms are real words in the wrong context |
| argument_structure_transitive | 0 | 8 | 0 | false alarms: real words with rare clusters (faylga 4,298 hits, nutqqa 7,448, seyfga 299, duoga). No action. |
| determiners / numeral_noun_number | 0 | 1 / 2 | 0 | false alarms (kosmonavtlar, burjlar, alplar are attested) |
| relative_clauses | 0 | 1 | 0 | false alarm (sepdi 1,844) |
| nominalization | 2 | 1 | 0 | **0148** taqdirlaganga, **0229** tullaganga have 0 hits (rare -ganga). Propose an attested -gan form instead (-ganni/-ganda if the frame allows), or drop. **0152** has a scan-error good sentence (boish < boʻlish; "boigan"): **drop**. |
| suspended_affixation | 1 | 2 | 0 | **0079 is a broken pair**: the bad sentence contains "(mahsuloa" (a truncated word from the -ga move inside a parenthesis). **Regenerate or drop.** taʼmga/hajv are real words. |

Net result: apart from vowel_glide_y, only 3 of 4,200 pairs are surface-obvious (0079, 0148/0229), plus 1 scan-error sentence (0152).

## Kattabek's repo (read-only, NOT edited)
`/workspace/kattabek_uzblimp_ro` imported the v11 vowel_glide pairs with the 'aa' rule:
- `data/pairs_v2_vowel_glide.tsv`: 149 rows, `vowel_glide-2001…`, method notes "rule9:V-stem+ydi -> *V-stem+adi";
- `data/external/uzblimp_v11.json`;
- the mapping `vowel_glide_y → vowel_glide` in `scripts/import_v11.py`;
- 54 vowel_glide rows in `handcheck/handcheck_iaa_562.csv`.

**It needs the same fix:** re-import vowel_glide from `uzblimp_v12.tsv`, keeping only the 10 surviving v11 ids plus the new `v12_vowel_glide_y_*` rows, and drop the rule9 rows. The 54 IAA hand-check rows on the 'aa' pairs no longer apply to v12.
