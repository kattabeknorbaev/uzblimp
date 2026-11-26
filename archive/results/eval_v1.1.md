# UzBLiMP v1.1: corpus sentences only (2026-10-27)

**v1.1 = v1.0 with the 12 hand-written seed pairs replaced** by the next corpus pairs in the same seeded order (decision 21), so every pair now comes from an attested corpus sentence. 2,388 pairs are unchanged; reserve 867. Results reuse the v1.0 scores of the unchanged pairs and score the 12 new pairs with the same settings (`scripts/carry_over.py`); this is exact because per-pair scores don't depend on the other pairs (the 1,200 pairs shared by the independently scored v0.2 and v1.0 runs got identical results). Tables from `scripts/eval_report.py --version v1.1 --previous v1.0`; for the setup and caveats see `results/eval_v1.0.md`.

**What changed from v1.0:** accuracies moved by at most 0.2 points. The matched-script difference is still +1.1 points but now p = 0.044 (v1.0: 0.052): a small Latin advantage at the edge of significance, sensitive to which pairs are included. All other conclusions are unchanged: script switch −7.2 (Goldfish-latn) and −21.7 (tahrirchi-bert); reform −11.3 overall, −55.4 where only the grammatical member's changed word has a new letter, −11.4 where both do, −3.1 where only other words do. Tokenizer `<unk>` rates as in v1.0 (Goldfish-latn 28% on Cyrillic, 82% on reformed; Goldfish-cyrl 81% on Latin).

## Accuracy (%) by model × alphabet (2400 pairs, 16 phenomena)

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Latin) | tahrirchi-bert (Latin) | Qwen2.5-0.5B (Latin) | Goldfish-latn (Cyrillic) | Goldfish-cyrl (Cyrillic) | tahrirchi-bert (Cyrillic) | Qwen2.5-0.5B (Cyrillic) | tahrirchi-bert (Reformed) | Qwen2.5-0.5B (Reformed) |
|---|---|---|---|---|---|---|---|---|---|---|
| anaphor_agreement | 98.7 | 40.7 | 99.3 | 50.7 | 88.0 | 99.3 | 72.0 | 38.0 | 86.7 | 42.0 |
| binding | 90.7 | 0.0 | 100.0 | 7.3 | 67.3 | 81.3 | 39.3 | 1.3 | 29.3 | 4.0 |
| dative_allomorphy | 88.0 | 1.3 | 92.7 | 14.0 | 70.7 | 87.3 | 48.7 | 67.3 | 90.7 | 37.3 |
| ditransitive_dative | 96.7 | 45.3 | 99.3 | 31.3 | 94.7 | 94.0 | 89.3 | 24.0 | 98.7 | 39.3 |
| lexical_case | 98.7 | 45.3 | 100.0 | 31.3 | 98.7 | 98.0 | 84.0 | 28.7 | 87.3 | 28.0 |
| nominalization | 100.0 | 90.7 | 99.3 | 92.0 | 99.3 | 100.0 | 98.0 | 52.7 | 74.7 | 19.3 |
| npi_hech | 93.3 | 2.7 | 96.0 | 5.3 | 79.3 | 86.0 | 21.3 | 4.0 | 61.3 | 13.3 |
| numeral_no_plural | 93.3 | 93.3 | 98.0 | 77.3 | 81.3 | 95.3 | 74.0 | 94.0 | 96.0 | 86.7 |
| passives | 94.0 | 50.7 | 98.0 | 60.7 | 86.7 | 94.7 | 81.3 | 18.0 | 98.0 | 54.0 |
| person_agreement | 99.3 | 51.3 | 100.0 | 52.0 | 87.3 | 96.0 | 83.3 | 51.3 | 99.3 | 46.7 |
| possessive_agreement | 96.7 | 66.7 | 100.0 | 71.3 | 91.3 | 96.7 | 74.7 | 72.7 | 100.0 | 70.7 |
| postposition_case | 100.0 | 48.0 | 100.0 | 64.7 | 99.3 | 100.0 | 100.0 | 57.3 | 100.0 | 72.0 |
| quantifiers | 96.0 | 80.7 | 98.7 | 82.0 | 92.0 | 97.3 | 84.0 | 97.3 | 98.0 | 82.7 |
| relative_clauses | 98.0 | 70.0 | 98.7 | 66.7 | 98.7 | 98.7 | 97.3 | 56.7 | 95.3 | 44.7 |
| stem_alternation | 95.3 | 60.7 | 99.3 | 61.3 | 96.7 | 94.7 | 93.3 | 54.7 | 84.0 | 57.3 |
| suspended_affixation | 92.7 | 14.7 | 98.0 | 40.7 | 84.7 | 94.0 | 89.3 | 20.7 | 98.0 | 59.3 |
| **All (2400)** | **95.7** | **47.6** | **98.6** | **50.5** | **88.5** | **94.6** | **76.9** | **46.2** | **87.3** | **47.3** |
| acc_norm (per byte) | 94.6 | 53.2 | 98.5 | 56.8 | 85.6 | 93.4 | 76.2 | 48.9 | 89.8 | 53.6 |

## Paired tests (same pairs; McNemar, bootstrap 95% CI)

| Comparison | Difference | 95% CI | p |
|---|---|---|---|
| Matched script: Goldfish-latn on Latin vs Goldfish-cyrl on Cyrillic | +1.1 | +0.1, +2.2 | 0.044 |
| Goldfish-latn: Latin vs Cyrillic text | +7.2 | +5.9, +8.6 | 3.6e-23 |
| tahrirchi-bert: Latin vs Cyrillic text | +21.7 | +20.1, +23.4 | 5.8e-108 |
| Qwen2.5-0.5B: Latin vs Cyrillic text | +4.4 | +2.0, +6.8 | 0.00031 |
| tahrirchi-bert: current vs reformed Latin | +11.3 | +9.9, +12.6 | 1.8e-55 |
| Qwen2.5-0.5B: current vs reformed Latin | +3.2 | +1.2, +5.2 | 0.002 |

Matched script per phenomenon (Bonferroni threshold 0.0031):

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Cyrillic) | Difference | p |
|---|---|---|---|---|
| anaphor_agreement | 98.7 | 99.3 | -0.7 | 1 |
| binding | 90.7 | 81.3 | +9.3 | 0.022 |
| dative_allomorphy | 88.0 | 87.3 | +0.7 | 1 |
| ditransitive_dative | 96.7 | 94.0 | +2.7 | 0.42 |
| lexical_case | 98.7 | 98.0 | +0.7 | 1 |
| nominalization | 100.0 | 100.0 | +0.0 | 1 |
| npi_hech | 93.3 | 86.0 | +7.3 | 0.022 |
| numeral_no_plural | 93.3 | 95.3 | -2.0 | 0.61 |
| passives | 94.0 | 94.7 | -0.7 | 1 |
| person_agreement | 99.3 | 96.0 | +3.3 | 0.074 |
| possessive_agreement | 96.7 | 96.7 | +0.0 | 0.62 |
| postposition_case | 100.0 | 100.0 | +0.0 | 1 |
| quantifiers | 96.0 | 97.3 | -1.3 | 0.72 |
| relative_clauses | 98.0 | 98.7 | -0.7 | 1 |
| stem_alternation | 95.3 | 94.7 | +0.7 | 1 |
| suspended_affixation | 92.7 | 94.0 | -1.3 | 0.8 |

## Reformed Latin by where the new letters fall

| Model | Category | n | Current | Reformed | Difference [95% CI] | p |
|---|---|---|---|---|---|---|
| tahrirchi-bert | critical word changed | 1070 | 99.3 | 77.6 | +21.7 [+19.3, +24.4] | 7e-50 |
| tahrirchi-bert | only other words changed | 1208 | 98.0 | 94.9 | +3.1 [+2.0, +4.3] | 2.9e-07 |
| tahrirchi-bert | unchanged | 122 | 98.4 | 98.4 | +0.0 [+0.0, +0.0] | 1 |
| Qwen2.5-0.5B | critical word changed | 1070 | 50.0 | 38.9 | +11.1 [+7.7, +14.6] | 1.2e-09 |
| Qwen2.5-0.5B | only other words changed | 1208 | 50.6 | 54.1 | -3.5 [-6.0, -1.1] | 0.0069 |
| Qwen2.5-0.5B | unchanged | 122 | 54.9 | 54.9 | +0.0 [+0.0, +0.0] | 1 |

Critical word changed, split by which member has the new letter:

| Model | New letter in | n | Current | Reformed | Difference [95% CI] | p |
|---|---|---|---|---|---|---|
| tahrirchi-bert | both | 819 | 99.1 | 87.8 | +11.4 [+9.0, +13.8] | 1.2e-19 |
| tahrirchi-bert | grammatical only | 251 | 99.6 | 44.2 | +55.4 [+49.4, +61.4] | 1.2e-31 |
| Qwen2.5-0.5B | both | 819 | 54.3 | 48.4 | +6.0 [+1.8, +10.0] | 0.005 |
| Qwen2.5-0.5B | grammatical only | 251 | 35.9 | 8.0 | +27.9 [+21.5, +33.9] | 5.1e-14 |

## Pairs shared with v1.0: same result?

| Run | Shared pairs (same text) | Same correct/incorrect | Max abs. log-prob difference |
|---|---|---|---|
| Goldfish-latn (Latin) | 2388 | 2388 | 2.8e-14 |
| Goldfish-cyrl (Latin) | 2388 | 2388 | 2.8e-14 |
| tahrirchi-bert (Latin) | 2388 | 2388 | 3.6e-15 |
| Qwen2.5-0.5B (Latin) | 2388 | 2388 | 2.8e-14 |
| Goldfish-latn (Cyrillic) | 2388 | 2388 | 2.8e-14 |
| Goldfish-cyrl (Cyrillic) | 2388 | 2388 | 3.6e-15 |
| tahrirchi-bert (Cyrillic) | 2388 | 2388 | 2.8e-14 |
| Qwen2.5-0.5B (Cyrillic) | 2388 | 2388 | 2.8e-14 |
| tahrirchi-bert (Reformed) | 2388 | 2388 | 2.8e-14 |
| Qwen2.5-0.5B (Reformed) | 2388 | 2388 | 2.8e-14 |
