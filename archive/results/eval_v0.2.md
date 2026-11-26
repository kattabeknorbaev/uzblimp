# UzBLiMP v0.2: 1,200 pairs, three alphabets (provisional, 2026-10-18; Cyrillic updated 2026-10-19)

**Benchmark v0.2:** 8 complete phenomena × 150 = 1,200 pairs (`data/benchmark/uzblimp.tsv`, built with `scripts/build_benchmark.py`). New since v0.1: `suspended_affixation` and `possessive_agreement`. The 900 v0.1 pairs are unchanged (per-phenomenon seeds).
- **Cyrillic** (`uzblimp_cyrl.tsv`, `scripts/convert_cyrillic.py`): 0 Latin letters left, 0 broken pairs, 2/2,400 round-trip differences (*sentabr*, Cyrillic correct). Native check (KN): 80/80 sampled pairs OK (10 per phenomenon). Loan stems with ь fixed after the check (*film* → фильм, *kompyuter* → компьютер; 4 pairs changed, accuracies unchanged).
- **Reformed Latin** (`uzblimp_reformed.tsv`, `scripts/convert_reformed.py`): 443 pairs with a new letter in the critical word, 698 only elsewhere, 59 unchanged; 0 broken. Models with 0% `<unk>` (decision 8): Qwen2.5-0.5B and tahrirchi-bert; Goldfish-latn excluded (87% `<unk>`).
- **Metric:** accuracy, log P(grammatical) > log P(ungrammatical), chance = 50%; masked LM scored with PLL (`within_word_l2r`). Tables from `scripts/eval_report.py --version v0.2 --previous v0.1`.

## Accuracy (%) by model × alphabet (1200 pairs, 8 phenomena)

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Latin) | tahrirchi-bert (Latin) | Qwen2.5-0.5B (Latin) | Goldfish-latn (Cyrillic) | Goldfish-cyrl (Cyrillic) | tahrirchi-bert (Cyrillic) | Qwen2.5-0.5B (Cyrillic) | tahrirchi-bert (Reformed) | Qwen2.5-0.5B (Reformed) |
|---|---|---|---|---|---|---|---|---|---|---|
| dative_allomorphy | 88.7 | 1.3 | 92.7 | 14.7 | 70.7 | 88.7 | 48.7 | 68.0 | 91.3 | 38.0 |
| lexical_case | 98.7 | 45.3 | 100.0 | 31.3 | 98.7 | 98.0 | 84.0 | 28.7 | 87.3 | 28.0 |
| npi_hech | 93.3 | 3.3 | 96.0 | 6.0 | 79.3 | 86.0 | 22.0 | 4.7 | 61.3 | 14.0 |
| numeral_no_plural | 93.3 | 93.3 | 98.0 | 77.3 | 81.3 | 95.3 | 74.7 | 94.0 | 96.0 | 86.0 |
| possessive_agreement | 96.7 | 66.7 | 100.0 | 71.3 | 91.3 | 96.7 | 74.7 | 72.7 | 100.0 | 70.7 |
| postposition_case | 100.0 | 48.7 | 100.0 | 64.0 | 99.3 | 100.0 | 100.0 | 58.0 | 100.0 | 71.3 |
| stem_alternation | 95.3 | 60.0 | 99.3 | 60.7 | 96.7 | 94.7 | 92.7 | 55.3 | 83.3 | 57.3 |
| suspended_affixation | 92.7 | 14.7 | 98.0 | 40.7 | 84.0 | 94.0 | 90.0 | 20.7 | 98.0 | 59.3 |
| **All (1200)** | **94.8** | **41.7** | **98.0** | **45.8** | **87.7** | **94.2** | **73.3** | **50.2** | **89.7** | **53.1** |
| acc_norm (per byte) | 92.0 | 40.3 | 98.0 | 47.8 | 82.6 | 90.8 | 71.3 | 50.5 | 90.2 | 54.2 |

## Paired tests (same pairs; McNemar, bootstrap 95% CI)

| Comparison | Difference | 95% CI | p |
|---|---|---|---|
| Matched script: Goldfish-latn on Latin vs Goldfish-cyrl on Cyrillic | +0.7 | -0.8, +2.2 | 0.46 |
| Goldfish-latn: Latin vs Cyrillic text | +7.2 | +5.1, +9.1 | 1e-11 |
| tahrirchi-bert: Latin vs Cyrillic text | +24.7 | +22.2, +27.2 | 3.1e-62 |
| Qwen2.5-0.5B: Latin vs Cyrillic text | -4.5 | -7.8, -1.0 | 0.011 |
| tahrirchi-bert: current vs reformed Latin | +8.3 | +6.7, +10.1 | 8e-20 |
| Qwen2.5-0.5B: current vs reformed Latin | -7.3 | -10.0, -4.5 | 1.5e-07 |

Matched script per phenomenon (Bonferroni threshold 0.0063):

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Cyrillic) | Difference | p |
|---|---|---|---|---|
| dative_allomorphy | 88.7 | 88.7 | +0.0 | 0.84 |
| lexical_case | 98.7 | 98.0 | +0.7 | 1 |
| npi_hech | 93.3 | 86.0 | +7.3 | 0.022 |
| numeral_no_plural | 93.3 | 95.3 | -2.0 | 0.61 |
| possessive_agreement | 96.7 | 96.7 | +0.0 | 0.62 |
| postposition_case | 100.0 | 100.0 | +0.0 | 1 |
| stem_alternation | 95.3 | 94.7 | +0.7 | 1 |
| suspended_affixation | 92.7 | 94.0 | -1.3 | 0.8 |

## Reformed Latin by where the new letters fall

| Model | Category | n | Current | Reformed | Difference [95% CI] | p |
|---|---|---|---|---|---|---|
| tahrirchi-bert | critical word changed | 443 | 98.9 | 84.4 | +14.4 [+11.1, +18.1] | 1.1e-13 |
| tahrirchi-bert | only other words changed | 698 | 97.4 | 92.3 | +5.2 [+3.3, +7.2] | 2.5e-07 |
| tahrirchi-bert | unchanged | 59 | 98.3 | 98.3 | +0.0 [+0.0, +0.0] | 1 |
| Qwen2.5-0.5B | critical word changed | 443 | 43.8 | 52.6 | -8.8 [-13.8, -3.8] | 0.0009 |
| Qwen2.5-0.5B | only other words changed | 698 | 46.1 | 53.2 | -7.0 [-10.3, -3.7] | 6e-05 |
| Qwen2.5-0.5B | unchanged | 59 | 55.9 | 55.9 | +0.0 [+0.0, +0.0] | 1 |

## Pairs shared with v0.1: same result?

| Run | Shared pairs (same text) | Same correct/incorrect | Max abs. log-prob difference |
|---|---|---|---|
| Goldfish-latn (Latin) | 900 | 900 | 1.5e-05 |
| Goldfish-cyrl (Latin) | 900 | 900 | 3.1e-05 |
| tahrirchi-bert (Latin) | 900 | 900 | 3.8e-05 |
| Qwen2.5-0.5B (Latin) | 900 | 900 | 0.00012 |
| Goldfish-latn (Cyrillic) | 898 | 898 | 1.5e-05 |
| Goldfish-cyrl (Cyrillic) | 898 | 898 | 1.5e-05 |
| tahrirchi-bert (Cyrillic) | 898 | 898 | 3.1e-05 |
| Qwen2.5-0.5B (Cyrillic) | 898 | 898 | 6.1e-05 |
| tahrirchi-bert (Reformed) | 900 | 900 | 4.6e-05 |
| Qwen2.5-0.5B (Reformed) | 900 | 900 | 0.00012 |

## Tokenizer coverage (`<unk>` in % of sentences)

| Model | Latin | Cyrillic | Reformed |
|---|---|---|---|
| Goldfish-latn | 0 | 30 | 87 |
| Goldfish-cyrl | 79 | 0 | – |
| Qwen2.5-0.5B | 0 | 0 | 0 |
| tahrirchi-bert | 0 | 0 | 0 |

## What this suggests (provisional)

1. **Uzbek-only models know these phenomena; the small multilingual one doesn't.** tahrirchi-bert 98.0%, Goldfish-latn 94.8%; Qwen2.5-0.5B 45.8% (below chance, driven by length and suffix-frequency cues as in v0.1: *npi_hech* 6.0%, *dative_allomorphy* 14.7%).
2. **Matched script: grammar knowledge holds across scripts.** Goldfish-latn on Latin 94.8% vs Goldfish-cyrl on Cyrillic 94.2% (+0.7, CI −0.8 to +2.2, p = 0.46). No phenomenon differs after Bonferroni correction; the two new phenomena are equal or nearly so (96.7 vs 96.7, 92.7 vs 94.0).
3. **The other script costs single-script models a lot:** Goldfish-latn −7.2 on Cyrillic (with 30% `<unk>`), tahrirchi-bert −24.7 (98.0 → 73.3, no `<unk>` but about twice the tokens). Goldfish-cyrl on Latin collapses (41.7%, 79% `<unk>`).
4. **Reformed Latin costs less than a full script change:** tahrirchi-bert −8.3 (98.0 → 89.7); −14.4 when the critical word contains a new letter, −5.2 when only other words do, 0 for the 59 unchanged pairs. So current Latin > reformed Latin > Cyrillic for a Latin-trained model, as in v0.1.
5. **The two new phenomena are robust to spelling for tahrirchi-bert:** *suspended_affixation* 98.0 → 98.0 and *possessive_agreement* 100.0 → 100.0 in reformed Latin, so the overall reformed drop is smaller than in v0.1 (−11.1). In Cyrillic they hold up better than the v0.1 phenomena too (90.0 and 74.7).
6. **Reproducible:** every pair shared with v0.1 with identical text (900; 898 in Cyrillic after the loanword fix) gets the same result in all 10 runs (log-probabilities within 0.0002).

## Caveats
- **8 of 16 phenomena**; the other 8 (Javokhir's v11 pairs) are still to review.
- **Contamination:** tahrirchi-bert may have seen many v1 source sentences (uz-books); Tomaris saw 98.6% of the v0.1 grammatical sentences. Seen/unseen analysis pending (`results/eval_v0.1.md`).
- **The Goldfish models aren't content-matched** across scripts (different corpora, same size class).
- **Cyrillic is converted, not native**; reformed Latin follows only the 4 rules in the brief.
- **No instruction-tuned, mid-size or frontier model yet** (decision 19 needs them).
