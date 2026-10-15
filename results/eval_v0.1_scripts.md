# Latin vs Cyrillic: UzBLiMP v0.1 (provisional, 2026-10-15)

**Data:**
- **Latin:** the 900 benchmark pairs (6 phenomena × 150), `data/benchmark/uzblimp.tsv`.
- **Cyrillic:** the same pairs converted by `scripts/alphabets.py::to_cyrillic`, `data/benchmark/uzblimp_cyrl.tsv`. That's TurkicNLP 0.4.0 plus our fixes: t+s vs ц, the tutuq in *sʼh*, ъ/ь before *ye*, and month names.
- **Automatic checks on the conversion:**
  - 0 Latin letters left
  - every pair still differs in one place
  - 2/1,800 round-trip differences, both *сентябрь → sentyabr* (Cyrillic correct)
- **Native check:** a 60-pair sample is pending (`handcheck/cyrillic_check_60.csv`).

**Metric:** accuracy, i.e. log P(grammatical) > log P(ungrammatical); chance = 50%. Masked LM scored with PLL.

## Accuracy (%) by model × script

| Phenomenon | Goldfish-latn on Latin | Goldfish-cyrl on Cyrillic | Goldfish-latn on Cyrillic | Goldfish-cyrl on Latin | tahrirchi-bert Latin / Cyrillic | Qwen2.5-0.5B Latin / Cyrillic |
|---|---|---|---|---|---|---|
| dative_allomorphy | 88.7 | 88.0 | 71.3 | 1.3 | 92.7 / 48.0 | 14.7 / 68.0 |
| lexical_case | 98.7 | 98.0 | 98.7 | 45.3 | 100.0 / 84.0 | 31.3 / 28.7 |
| npi_hech | 93.3 | 86.0 | 79.3 | 3.3 | 96.0 / 22.0 | 6.0 / 4.0 |
| numeral_no_plural | 93.3 | 95.3 | 80.7 | 93.3 | 98.0 / 74.7 | 77.3 / 94.0 |
| postposition_case | 100.0 | 100.0 | 99.3 | 48.7 | 100.0 / 100.0 | 64.0 / 58.7 |
| stem_alternation | 95.3 | 94.7 | 96.7 | 60.0 | 99.3 / 92.7 | 60.7 / 55.3 |
| **All (900)** | **94.9** | **93.7** | **87.7** | **42.0** | **97.7 / 70.2** | **42.3 / 51.4** |

The first two columns are the **matched-script** comparison: each model reads the script it was trained on.

## Paired tests (same 900 pairs; McNemar, bootstrap 95% CI)

| Comparison | Difference | 95% CI | p |
|---|---|---|---|
| **Matched script:** Goldfish-latn on Latin vs Goldfish-cyrl on Cyrillic | +1.2 | −0.4, +3.0 | 0.23 |
| Goldfish-latn: Latin vs Cyrillic text | +7.2 | +5.1, +9.6 | 2e-9 |
| tahrirchi-bert: Latin vs Cyrillic text | +27.4 | +24.4, +30.4 | 2e-52 |
| Qwen2.5-0.5B: Latin vs Cyrillic text | −9.1 | −13.0, −5.3 | 1e-5 |

**Matched script, per phenomenon:** the only difference with p < 0.05 is `npi_hech` (93.3 vs 86.0, p = 0.022). With 6 tests, that's not significant after a Bonferroni correction (threshold 0.0083). All other phenomena differ by ≤ 2 points.

## Tokenizer coverage

| Model | `<unk>` on Latin | `<unk>` on Cyrillic | Tokens/sentence (Latin → Cyrillic) |
|---|---|---|---|
| Goldfish-latn | 0% | 33% | 17.2 → 19.6 |
| Goldfish-cyrl | 78% | 0% | 34.0 → 14.5 |
| Qwen2.5-0.5B | 0% | 0% | 27.3 → 35.3 |
| tahrirchi-bert | 0% | 0% | 17.9 → 32.0 |

## What this suggests (provisional)

1. **When a model reads the script it was trained on, its grammar knowledge holds across scripts.** Latin- and Cyrillic-trained Goldfish models score the same within noise (94.9 vs 93.7, n.s.).
2. **When a model reads a script it wasn't trained on, it loses a lot:**
   - Goldfish-latn −7 points (despite 33% `<unk>`);
   - *tahrirchi-bert* −27 points, with no `<unk>` but twice the tokens;
   - Goldfish-cyrl on Latin collapses (78% `<unk>`, a tokenizer artifact).

   So what these models know about grammar is tied to the script they were trained in.
3. **The small multilingual model is near chance in both scripts.** Its Latin/Cyrillic shift (e.g. dative 15% → 68%) follows how frequent the suffixes are in each script, not grammar.

## Caveats
- **The Goldfish models weren't trained on the same content.** They were trained on different Latin and Cyrillic corpora; same size class, but not content-matched.
- **The Cyrillic text is converted, not native.** Automatic checks are clean, but the native-speaker sample check is pending, and loanwords like *sirk → цирк* can't be recovered by rule.
- **Only 6 of 16 phenomena so far,** 150 pairs each.
- **Contamination is still unresolved** (see `results/eval_v0.1.md`).
