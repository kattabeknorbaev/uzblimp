# Reformed Latin (2026) vs current Latin: UzBLiMP v0.1 (provisional, 2026-10-15)

**Data:** the 900 benchmark pairs converted with `scripts/alphabets.py::to_reformed` (oʻ→ö, gʻ→ğ, sh→ş, ch→ç; nothing else changed), in `data/benchmark/uzblimp_reformed.tsv`. Every pair still differs in one place. Each pair is labelled by where the new letters fall:

| Category | Pairs | Meaning |
|---|---|---|
| critical word changed | 340 | the word that makes the pair (un)grammatical contains ö/ğ/ş/ç |
| only other words changed | 524 | new letters only in the rest of the sentence |
| unchanged | 36 | no oʻ/gʻ/sh/ch at all: identical to current Latin (sanity check) |

**Models (decision 8: only those with 0 `<unk>` on reformed text):**

| Model | `<unk>` on reformed | Tokens/sentence: current → reformed | Used |
|---|---|---|---|
| Goldfish uzn_latn_100mb | 89% of sentences | 17.2 → 19.9 | ❌ excluded (can't encode ğ/ş/ç) |
| Qwen2.5-0.5B (BOS) | 0% | 27.3 → 25.9 | ✅ |
| tahrirchi-bert-base | 0% | 17.9 → 21.3 | ✅ |

## Results (accuracy %, paired on the same pairs; McNemar, bootstrap 95% CI)

| Model / pairs | n | Current Latin | Reformed | Difference [95% CI] | p |
|---|---|---|---|---|---|
| **tahrirchi-bert, all** | 900 | 97.7 | **86.6** | **+11.1** [+8.9, +13.3] | 8e-21 |
| – critical word changed | 340 | 98.8 | 80.3 | **+18.5** [+14.4, +23.2] | 8e-14 |
| – only other words changed | 524 | 96.9 | 89.9 | +7.1 [+4.6, +9.5] | 4e-8 |
| – unchanged (sanity) | 36 | 97.2 | 97.2 | 0.0 | – |
| **Qwen2.5-0.5B, all** | 900 | 42.3 | 49.1 | −6.8 [−10.0, −3.6] | 2e-5 |
| – critical word changed | 340 | 39.4 | 46.2 | −6.8 | 0.02 |
| – only other words changed | 524 | 42.6 | 49.8 | −7.3 | 3e-4 |

**tahrirchi-bert by phenomenon (current → reformed):**

| Phenomenon | Current | Reformed |
|---|---|---|
| npi_hech | 96.0 | **61.3** |
| stem_alternation | 99.3 | 83.3 |
| lexical_case | 100.0 | 87.3 |
| dative_allomorphy | 92.7 | 91.3 |
| numeral_no_plural | 98.0 | 96.0 |
| postposition_case | 100.0 | 100.0 |

## All three alphabets at a glance (accuracy %, 900 pairs)

| Model (trained on) | Current Latin | Reformed Latin | Cyrillic |
|---|---|---|---|
| Goldfish uzn_latn_100mb (Latin) | **94.9** | excluded (89% `<unk>`) | 87.7 (33% `<unk>`) |
| Goldfish uzn_cyrl_100mb (Cyrillic) | 42.0 (78% `<unk>`) | – | **93.7** |
| tahrirchi-bert-base (Latin) | **97.7** | 86.6 | 70.2 |
| Qwen2.5-0.5B (multilingual) | 42.3 | 49.1 | 51.4 |

## What this suggests (provisional)

1. **A model trained on current Latin loses grammar accuracy on the reformed spelling.** It drops 11 points overall, and **18.5 points when the tested word itself contains a new letter**. It drops 7 points even when only *other* words change, so the surrounding context matters too.
2. **The drop is far smaller than a full change of script** (Cyrillic: −27). So in effect, current Latin > reformed Latin > Cyrillic, ordered by how close the text is to the training data.
3. **The practical point:** grammar checks and models trained before the reform will degrade on 2026-spelling text until they're retrained or adapted.
4. **The small multilingual model is near chance in every alphabet.** Its reformed-Latin "gain" (+6.8) is movement towards 50%, not grammar.

## Caveats
- **The reform rules are the 4 given in the project brief.** Other details (tutuq, names, loans) aren't covered.
- **No model has seen reformed Uzbek yet,** so these are zero-shot numbers.
- **Only 2 models qualify** (0 `<unk>`), and **only 6 of 16 phenomena** so far.
- **tahrirchi-bert's Latin score may be inflated by contamination** (see `results/eval_v0.1.md`).
