# UzBLiMP v1.0: 2,400 pairs, 16 phenomena, three alphabets (2026-10-26)

**Benchmark v1.0:** 16 phenomena × 150 = 2,400 pairs (`data/benchmark/uzblimp.tsv`, `scripts/build_benchmark.py`); 881 reserve pairs. All 1,200 v0.2 pairs are unchanged. Sources: 1,441 pairs from our corpus (rule-based generators, `scripts/make_pairs.py`), 959 from Javokhir Matniyazov's v11 pairs built from `tahrirchi/uz-books-v2`. Every pair was reviewed by Kattabek (procedure in `notes/decisions.md`, decision 20).
- **Cyrillic** (`uzblimp_cyrl.tsv`): 0 Latin letters left, 0 broken pairs; 8 round-trip differences, all expected (*obyekt/subyekt* ↔ объект/субъект, *sentabr*). Native check: 80/80 for the v0.2 phenomena; 80 samples for the 8 new phenomena pending (two suspected loans: *Князь*, *принцип*).
- **Reformed Latin** (`uzblimp_reformed.tsv`): 1,070 pairs with a new letter in the critical word, 1,208 only elsewhere, 122 unchanged; Goldfish-latn excluded (82% `<unk>`).
- **Metric:** accuracy, log P(grammatical) > log P(ungrammatical), chance = 50%; tahrirchi-bert scored with PLL (`within_word_l2r`). Tables from `scripts/eval_report.py --version v1.0 --previous v0.2`.

## Accuracy (%) by model × alphabet (2400 pairs, 16 phenomena)

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Latin) | tahrirchi-bert (Latin) | Qwen2.5-0.5B (Latin) | Goldfish-latn (Cyrillic) | Goldfish-cyrl (Cyrillic) | tahrirchi-bert (Cyrillic) | Qwen2.5-0.5B (Cyrillic) | tahrirchi-bert (Reformed) | Qwen2.5-0.5B (Reformed) |
|---|---|---|---|---|---|---|---|---|---|---|
| anaphor_agreement | 98.7 | 40.0 | 99.3 | 50.7 | 88.0 | 99.3 | 72.0 | 38.0 | 86.7 | 42.0 |
| binding | 90.7 | 0.0 | 100.0 | 8.0 | 67.3 | 81.3 | 40.0 | 1.3 | 30.0 | 4.0 |
| dative_allomorphy | 88.7 | 1.3 | 92.7 | 14.7 | 70.7 | 88.7 | 48.7 | 68.0 | 91.3 | 38.0 |
| ditransitive_dative | 96.7 | 44.7 | 99.3 | 31.3 | 94.7 | 94.0 | 89.3 | 24.7 | 98.7 | 40.0 |
| lexical_case | 98.7 | 45.3 | 100.0 | 31.3 | 98.7 | 98.0 | 84.0 | 28.7 | 87.3 | 28.0 |
| nominalization | 100.0 | 90.7 | 99.3 | 92.7 | 99.3 | 100.0 | 98.0 | 53.3 | 74.0 | 19.3 |
| npi_hech | 93.3 | 3.3 | 96.0 | 6.0 | 79.3 | 86.0 | 22.0 | 4.7 | 61.3 | 14.0 |
| numeral_no_plural | 93.3 | 93.3 | 98.0 | 77.3 | 81.3 | 95.3 | 74.7 | 94.0 | 96.0 | 86.0 |
| passives | 94.0 | 50.7 | 98.0 | 60.7 | 86.7 | 94.7 | 81.3 | 18.0 | 98.0 | 54.0 |
| person_agreement | 99.3 | 51.3 | 100.0 | 52.0 | 87.3 | 96.0 | 83.3 | 51.3 | 99.3 | 46.7 |
| possessive_agreement | 96.7 | 66.7 | 100.0 | 71.3 | 91.3 | 96.7 | 74.7 | 72.7 | 100.0 | 70.7 |
| postposition_case | 100.0 | 48.7 | 100.0 | 64.0 | 99.3 | 100.0 | 100.0 | 58.0 | 100.0 | 71.3 |
| quantifiers | 96.0 | 80.7 | 98.7 | 82.0 | 92.0 | 97.3 | 84.0 | 97.3 | 98.0 | 82.7 |
| relative_clauses | 98.0 | 70.0 | 98.7 | 66.7 | 98.7 | 98.7 | 97.3 | 56.7 | 95.3 | 44.7 |
| stem_alternation | 95.3 | 60.0 | 99.3 | 60.7 | 96.7 | 94.7 | 92.7 | 55.3 | 83.3 | 57.3 |
| suspended_affixation | 92.7 | 14.7 | 98.0 | 40.7 | 84.0 | 94.0 | 90.0 | 20.7 | 98.0 | 59.3 |
| **All (2400)** | **95.8** | **47.6** | **98.6** | **50.6** | **88.5** | **94.7** | **77.0** | **46.4** | **87.3** | **47.4** |
| acc_norm (per byte) | 94.6 | 53.2 | 98.5 | 56.9 | 85.5 | 93.5 | 76.4 | 49.0 | 89.7 | 53.7 |

## Paired tests (same pairs; McNemar, bootstrap 95% CI)

| Comparison | Difference | 95% CI | p |
|---|---|---|---|
| Matched script: Goldfish-latn on Latin vs Goldfish-cyrl on Cyrillic | +1.1 | +0.0, +2.2 | 0.052 |
| Goldfish-latn: Latin vs Cyrillic text | +7.3 | +5.9, +8.7 | 1.1e-23 |
| tahrirchi-bert: Latin vs Cyrillic text | +21.6 | +19.9, +23.4 | 2.6e-107 |
| Qwen2.5-0.5B: Latin vs Cyrillic text | +4.2 | +2.0, +6.6 | 0.00053 |
| tahrirchi-bert: current vs reformed Latin | +11.3 | +10.0, +12.6 | 1.8e-55 |
| Qwen2.5-0.5B: current vs reformed Latin | +3.2 | +1.3, +5.4 | 0.0019 |

Matched script per phenomenon (Bonferroni threshold 0.0031):

| Phenomenon | Goldfish-latn (Latin) | Goldfish-cyrl (Cyrillic) | Difference | p |
|---|---|---|---|---|
| anaphor_agreement | 98.7 | 99.3 | -0.7 | 1 |
| binding | 90.7 | 81.3 | +9.3 | 0.022 |
| dative_allomorphy | 88.7 | 88.7 | +0.0 | 0.84 |
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
| tahrirchi-bert | critical word changed | 1070 | 99.3 | 77.7 | +21.6 [+19.1, +24.3] | 1.2e-49 |
| tahrirchi-bert | only other words changed | 1208 | 98.0 | 94.8 | +3.2 [+2.1, +4.5] | 1.8e-07 |
| tahrirchi-bert | unchanged | 122 | 98.4 | 98.4 | +0.0 [+0.0, +0.0] | 1 |
| Qwen2.5-0.5B | critical word changed | 1070 | 50.3 | 39.2 | +11.1 [+7.7, +14.6] | 1.5e-09 |
| Qwen2.5-0.5B | only other words changed | 1208 | 50.5 | 53.9 | -3.4 [-5.8, -0.8] | 0.0085 |
| Qwen2.5-0.5B | unchanged | 122 | 54.9 | 54.9 | +0.0 [+0.0, +0.0] | 1 |

Critical word changed, split by which member has the new letter:

| Model | New letter in | n | Current | Reformed | Difference [95% CI] | p |
|---|---|---|---|---|---|---|
| tahrirchi-bert | both | 818 | 99.1 | 87.9 | +11.2 [+8.9, +13.6] | 2.1e-19 |
| tahrirchi-bert | grammatical only | 251 | 99.6 | 44.2 | +55.4 [+49.4, +61.8] | 1.2e-31 |
| tahrirchi-bert | ungrammatical only | 1 | 100.0 | 100.0 | +0.0 [+0.0, +0.0] | 1 |
| Qwen2.5-0.5B | both | 818 | 54.4 | 48.7 | +5.7 [+1.6, +9.9] | 0.0074 |
| Qwen2.5-0.5B | grammatical only | 251 | 36.7 | 8.0 | +28.7 [+22.3, +35.1] | 1.9e-14 |
| Qwen2.5-0.5B | ungrammatical only | 1 | 100.0 | 100.0 | +0.0 [+0.0, +0.0] | 1 |

## Pairs shared with v0.2: same result?

| Run | Shared pairs (same text) | Same correct/incorrect | Max abs. log-prob difference |
|---|---|---|---|
| Goldfish-latn (Latin) | 1200 | 1200 | 1.5e-05 |
| Goldfish-cyrl (Latin) | 1200 | 1200 | 3.1e-05 |
| tahrirchi-bert (Latin) | 1200 | 1200 | 3.8e-05 |
| Qwen2.5-0.5B (Latin) | 1200 | 1200 | 0.00012 |
| Goldfish-latn (Cyrillic) | 1200 | 1200 | 1.5e-05 |
| Goldfish-cyrl (Cyrillic) | 1200 | 1200 | 1.5e-05 |
| tahrirchi-bert (Cyrillic) | 1200 | 1200 | 4.6e-05 |
| Qwen2.5-0.5B (Cyrillic) | 1200 | 1200 | 6.1e-05 |
| tahrirchi-bert (Reformed) | 1200 | 1200 | 3.1e-05 |
| Qwen2.5-0.5B (Reformed) | 1200 | 1200 | 0.00012 |

## Tokenizer coverage (`<unk>` in % of sentences, v1.0)

| Model | Latin | Cyrillic | Reformed |
|---|---|---|---|
| Goldfish-latn | 0 | 28 | 82 |
| Goldfish-cyrl | 81 | 0 | – |
| Qwen2.5-0.5B | 0 | 0 | 0 |
| tahrirchi-bert | 0 | 0 | 0 |

## What this shows

1. **Uzbek-only models know Uzbek grammar:** tahrirchi-bert 98.6%, Goldfish-latn 95.8% on 2,400 pairs. The hardest phenomena are dative allomorphy (88.7 / 92.7) and, for Goldfish, binding (90.7) and *hech* + negation (93.3).
2. **A small multilingual model doesn't:** Qwen2.5-0.5B is at chance (50.6%), with strong biases on single phenomena (binding 8.0%, *hech* 6.0%, nominalization 92.7%) that follow length and suffix frequency, not grammar.
3. **Matched script, grammar knowledge largely holds:** Goldfish-latn on Latin 95.8% vs Goldfish-cyrl on Cyrillic 94.7% (+1.1, CI 0.0 to +2.2, p = 0.052). No phenomenon differs after Bonferroni correction; the largest gaps are binding (+9.3) and *hech* (+7.3), both p = 0.022. A small Latin advantage can't be ruled out on 2,400 pairs.
4. **The other script costs a lot:** Goldfish-latn −7.3 on Cyrillic (28% `<unk>`), tahrirchi-bert −21.6 (98.6 → 77.0, no `<unk>`), Goldfish-cyrl on Latin 47.6% (81% `<unk>`).
5. **The 2026 reform: two different costs.** tahrirchi-bert loses 11.3 points overall (98.6 → 87.3), but the split by where the new letters fall shows:
   - **only the grammatical member's changed word has a new letter** (251 pairs: all of binding, *özimni* vs *meni*; most of nominalization, *-iş* vs *-gan*): **−55.4, to 44.2%, below chance.** The model prefers the familiar old spelling even when it is ungrammatical, so this is an orthography effect, not grammar;
   - **both members' changed words have new letters** (818 pairs): −11.2 (99.1 → 87.9): the genuine cost of the new spelling for grammar judgments;
   - **only other words changed** (1,208): −3.2; **nothing changed** (122): 0.
   **Methodological point:** minimal pairs whose members differ in spelling familiarity confound grammar with orthography; the reform's effect on grammar should be read from the "both" and "other words" rows.
6. **Reproducible:** all 1,200 pairs shared with v0.2 give the same result in all 10 runs (log-probabilities within 0.0002).

## Caveats
- **Review procedure:** KN's first pass, then a check with his co-founder (a second native speaker) and an AI assistant (decision 20). Inter-annotator agreement with Javokhir (86.4% on 419 pairs, κ 0.40) is only reportable if that co-founder is not Javokhir.
- **Contamination:** 959 pairs come from uz-books, which tahrirchi-bert was probably trained on; the Tomaris pretraining corpus contains most v0.1 sentences. Seen/unseen analysis pending.
- **The Goldfish models aren't content-matched** across scripts. Cyrillic is converted, not native; reformed Latin follows only the 4 rules in the brief.
- **No instruction-tuned, mid-size or frontier model yet** (needed for decision 19, grammar prompting).
