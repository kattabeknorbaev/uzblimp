# First evaluation: UzBLiMP v0.1 (provisional, 2026-10-15)

**Data:** `data/benchmark/uzblimp.tsv`, 900 pairs (6 complete phenomena × 150), current Latin. Built by `scripts/build_benchmark.py` and scored with `scripts/score_pairs.py` (sum of log-probs, float32; the masked LM uses PLL `within_word_l2r`, as TurBLiMP did for BERTurk).
- **acc** = log P(good) > log P(bad).
- **acc_norm** = the same comparison per UTF-8 byte (TatBLiMP).
- Chance = 50%.

| Phenomenon | Goldfish uzn_latn_100mb acc / norm | tahrirchi-bert-base acc / norm | Qwen2.5-0.5B acc / norm |
|---|---|---|---|
| dative_allomorphy | 88.7 / 88.7 | 92.7 / 92.7 | 14.7 / 14.7 |
| lexical_case | 98.7 / 98.7 | 100.0 / 100.0 | 31.3 / 46.0 |
| npi_hech | 93.3 / 97.3 | 96.0 / 99.3 | 6.0 / 60.0 |
| numeral_no_plural | 93.3 / 66.0 | 98.0 / 94.7 | 77.3 / 10.7 |
| postposition_case | 100.0 / 100.0 | 100.0 / 100.0 | 64.0 / 85.3 |
| stem_alternation | 95.3 / 96.0 | 99.3 / 99.3 | 60.7 / 68.0 |
| **All (900)** | 94.9 / 91.1 | 97.7 / 97.7 | 42.3 / 47.4 |

**Models:** `goldfish-models/uzn_latn_100mb` = causal, Uzbek-only, 125M-class; `tahrirchi/tahrirchi-bert-base` = masked LM (PLL), Uzbek-only, 110M; `Qwen/Qwen2.5-0.5B` = causal, multilingual, 494M, with BOS (without: 41.9 / 46.2).

## Observations (provisional; n = 150 per phenomenon, about ±5 points)
- **The two Uzbek-only models are near ceiling:** Goldfish 94.9%, tahrirchi-bert 97.7%. The masked LM is best, as BERTurk was in TurBLiMP.
- **Qwen2.5-0.5B is below chance (42.3%): it prefers the ungrammatical sentence.** The pattern points to surface cues, not grammar:
  - *hech*: 6% → 60% with length normalization, because the bad sentence lacks *-ma-* and is shorter;
  - dative 15% and lexical case 31%: the bad forms use the more frequent suffixes *-ga*, *-ni*;
  - numerals flip between the two metrics (77% → 11%) because *-lar* only adds length.
  - Adding a BOS token changed almost nothing (41.9% → 42.3%).
- **acc_norm has its own bias:** it favours the longer sentence, so it hurts phenomena where the bad member is longer (numerals: Goldfish 93.3% → 66.0%). Report both metrics, as TatBLiMP does.
- **Dative -qa/-ka is the hardest phenomenon for every model.** It's the morphophonology layer TatBLiMP says is missing from these benchmarks.

## Contamination (training-data overlap), from `scripts/check_overlap.py`

| Grammatical sentences from | In Tomaris pretraining corpus (`tomaris/fullcorpus`) |
|---|---|
| our corpus (v1 generators) | 1,490 / 1,952 = **76.3%**; the 900 benchmark pairs: 887 = **98.6%** |
| Javokhir's pairs (`tahrirchi/uz-books-v2`, v2) | 43 / 1,687 = **2.5%** |
| Tomaris SFT sets (`tomaris-sft`, `phase-d`, `tomaris-v1`) | 3 / 1,517 = 0.2% |

- **tahrirchi-bert was trained on `tahrirchi/uz-books` + `uz-crawl` (model card).** It has probably seen the v2 sentences: the reverse pattern to Tomaris.
- **Goldfish's training data hasn't been checked yet.**
- **This gives a natural seen/unseen comparison:** score each model on pairs whose grammatical sentence it has / hasn't seen. Only the grammatical members can have been seen.
- **Before final claims about Tomaris,** evaluate it on unseen pairs (v2, or v1-style pairs regenerated from tahrirchi books).
