# Human validation of UzBLiMP

Written by `scripts/human_study_report.py`. Forced choice: from the per-pair and per-annotator counts in `results/human/forced_choice_judgments.csv` and `results/human/forced_choice_annotators.csv` (the individual sheets are private).

## Forced choice

5 annotators, 320 pairs, 20 per phenomenon. Each annotator chose the Latin or the Cyrillic version of the sheet.

| Annotator | Answered | Accuracy (%) | Marked unsure |
|---|---:|---:|---:|
| p06 | 320 | 99.4 | 0 |
| p07 | 320 | 97.8 | 4 |
| p08 | 320 | 99.4 | 1 |
| p09 | 320 | 100.0 | 0 |
| p10 | 320 | 99.4 | 4 |

- Accuracy over all 1600 judgments: 99.2%.
- Majority vote agrees with the benchmark on 320 of 320 pairs (100.0%; 0 ties left out).
- Mean pairwise agreement 98.4%; Krippendorff's alpha 0.97.
- Pairs by number of annotators who chose the ungrammatical sentence: 0: 307, 1: 13.
- Answers marked as unsure: 9, on 8 pairs; 2 of them chose the ungrammatical sentence.

Accuracy (%) on these pairs; models on the script of their Uzbek training data (L: current Latin, C: Cyrillic; multilingual models on Latin).

| Phenomenon | Pairs | Human mean | Majority | GF-L 5MB (L) | GF-L 10MB (L) | GF-L 100MB (L) | GF-L full (L) | GF-C 5MB (C) | GF-C 10MB (C) | GF-C 100MB (C) | GF-C full (C) | tahrirchi-bert (L) | tahrirchi-bert-small (L) | BERTbek (L) | UzBERT (C) | UzRoBERTa (L) | mBERT (L) | XLM-R base (L) | Qwen2.5-0.5B (L) | Qwen2.5-1.5B (L) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anaphor_agreement | 20 | 98.0 | 100.0 | 40.0 | 80.0 | 100.0 | 100.0 | 50.0 | 60.0 | 100.0 | 100.0 | 100.0 | 90.0 | 75.0 | 90.0 | 90.0 | 50.0 | 70.0 | 50.0 | 60.0 |
| binding | 20 | 100.0 | 100.0 | 20.0 | 20.0 | 95.0 | 90.0 | 0.0 | 5.0 | 85.0 | 95.0 | 100.0 | 35.0 | 55.0 | 5.0 | 25.0 | 35.0 | 55.0 | 10.0 | 15.0 |
| dative_allomorphy | 20 | 97.0 | 100.0 | 60.0 | 70.0 | 100.0 | 100.0 | 55.0 | 75.0 | 90.0 | 100.0 | 90.0 | 80.0 | 80.0 | 95.0 | 100.0 | 35.0 | 35.0 | 10.0 | 5.0 |
| ditransitive_dative | 20 | 99.0 | 100.0 | 50.0 | 55.0 | 100.0 | 95.0 | 60.0 | 40.0 | 100.0 | 95.0 | 100.0 | 95.0 | 90.0 | 95.0 | 95.0 | 60.0 | 65.0 | 40.0 | 30.0 |
| lexical_case | 20 | 98.0 | 100.0 | 60.0 | 80.0 | 95.0 | 100.0 | 80.0 | 65.0 | 100.0 | 95.0 | 100.0 | 100.0 | 90.0 | 90.0 | 100.0 | 60.0 | 75.0 | 40.0 | 40.0 |
| nominalization | 20 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.0 | 100.0 | 95.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.0 |
| npi_hech | 20 | 100.0 | 100.0 | 20.0 | 30.0 | 100.0 | 95.0 | 10.0 | 10.0 | 100.0 | 100.0 | 100.0 | 95.0 | 80.0 | 60.0 | 95.0 | 5.0 | 40.0 | 5.0 | 10.0 |
| numeral_no_plural | 20 | 100.0 | 100.0 | 70.0 | 90.0 | 100.0 | 100.0 | 65.0 | 80.0 | 100.0 | 100.0 | 95.0 | 90.0 | 95.0 | 85.0 | 90.0 | 50.0 | 90.0 | 80.0 | 75.0 |
| passives | 20 | 100.0 | 100.0 | 60.0 | 85.0 | 100.0 | 100.0 | 75.0 | 80.0 | 90.0 | 95.0 | 95.0 | 100.0 | 95.0 | 90.0 | 100.0 | 80.0 | 100.0 | 60.0 | 70.0 |
| person_agreement | 20 | 100.0 | 100.0 | 45.0 | 65.0 | 100.0 | 100.0 | 50.0 | 65.0 | 95.0 | 95.0 | 100.0 | 100.0 | 95.0 | 100.0 | 100.0 | 50.0 | 100.0 | 80.0 | 50.0 |
| possessive_agreement | 20 | 99.0 | 100.0 | 75.0 | 80.0 | 100.0 | 100.0 | 75.0 | 80.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.0 | 100.0 | 95.0 | 70.0 | 90.0 | 65.0 | 60.0 |
| postposition_case | 20 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 80.0 | 100.0 | 100.0 | 95.0 | 55.0 | 80.0 |
| quantifiers | 20 | 100.0 | 100.0 | 80.0 | 80.0 | 100.0 | 100.0 | 70.0 | 80.0 | 95.0 | 100.0 | 100.0 | 85.0 | 85.0 | 90.0 | 85.0 | 85.0 | 100.0 | 75.0 | 90.0 |
| relative_clauses | 20 | 100.0 | 100.0 | 90.0 | 95.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 90.0 | 90.0 | 100.0 | 90.0 | 95.0 | 70.0 | 95.0 |
| stem_alternation | 20 | 98.0 | 100.0 | 90.0 | 95.0 | 100.0 | 100.0 | 95.0 | 95.0 | 95.0 | 100.0 | 100.0 | 100.0 | 90.0 | 100.0 | 100.0 | 80.0 | 85.0 | 45.0 | 80.0 |
| suspended_affixation | 20 | 98.0 | 100.0 | 40.0 | 50.0 | 85.0 | 100.0 | 35.0 | 25.0 | 85.0 | 95.0 | 100.0 | 85.0 | 95.0 | 100.0 | 95.0 | 55.0 | 90.0 | 40.0 | 35.0 |
| All | 320 | 99.2 | 100.0 | 62.5 | 73.4 | 98.4 | 98.8 | 63.7 | 66.2 | 95.9 | 98.1 | 98.4 | 90.9 | 87.8 | 85.6 | 91.9 | 62.8 | 80.3 | 51.6 | 55.6 |

Pairs on which at least one annotator chose the ungrammatical sentence (item: pair, wrong/annotators): 47: anaphor_agreement-2041, 1/5; 68: anaphor_agreement-2220, 1/5; 71: dative_allomorphy-1055, 1/5; 86: dative_allomorphy-1171, 1/5; 88: suspended_affixation-1131, 1/5; 123: stem_alternation-1227, 1/5; 161: suspended_affixation-1004, 1/5; 167: lexical_case-1205, 1/5; 168: possessive_agreement-1048, 1/5; 230: dative_allomorphy-1058, 1/5; 233: ditransitive_dative-2081, 1/5; 279: stem_alternation-1102, 1/5; 283: lexical_case-1200, 1/5.

Pairs to re-examine (the majority disagrees with the benchmark, or the vote is tied): none.

No rating sheets found (archive/human_study/responses/ratings<1|2>_<participant>.csv).
