# UzBLiMP progress

**Checkpoint 01 November 2026: at least 600 accepted pairs (goal ~1,000)** in the benchmark, 14 days from 18 October 2026. Full set: 16 × 150 = 2,400.

- Benchmark pairs so far: **1204 / 2,400** (50%); checkpoint minimum: 1204 / 600.
- Phenomena complete: 8 / 16. Reserve pairs: 591.

| Phenomenon | Target | Generated | Reviewed | Accepted | Acceptance | In benchmark | Reserve |
|---|---|---|---|---|---|---|---|
| 🟡 anaphor_agreement | 150 | 229 | 1 | 1 | 100% | 1 | 0 |
| ✅ lexical_case | 150 | 251 | 251 | 217 | 86% | 150 | 67 |
| 🟡 ditransitive_dative | 150 | 126 | 1 | 1 | 100% | 1 | 0 |
| 🟡 binding | 150 | 218 | 1 | 1 | 100% | 1 | 0 |
| ✅ stem_alternation | 150 | 251 | 251 | 227 | 90% | 150 | 77 |
| ✅ npi_hech | 150 | 252 | 252 | 233 | 92% | 150 | 83 |
| ✅ suspended_affixation | 150 | 203 | 203 | 188 | 93% | 150 | 38 |
| 🟡 nominalization | 150 | 173 | 1 | 1 | 100% | 1 | 0 |
| ⬜ person_agreement | 150 | 205 | 0 | 0 | – | 0 | 0 |
| ⬜ passives | 150 | 132 | 0 | 0 | – | 0 | 0 |
| ⬜ relative_clauses | 150 | 142 | 0 | 0 | – | 0 | 0 |
| ⬜ quantifiers | 150 | 168 | 0 | 0 | – | 0 | 0 |
| ✅ numeral_no_plural | 150 | 252 | 251 | 234 | 93% | 150 | 84 |
| ✅ postposition_case | 150 | 252 | 252 | 230 | 91% | 150 | 80 |
| ✅ possessive_agreement | 150 | 251 | 250 | 230 | 92% | 150 | 80 |
| ✅ dative_allomorphy | 150 | 252 | 252 | 232 | 92% | 150 | 82 |
| ⬜ vowel_glide (extra) | 150 | 149 | 0 | 0 | – | 0 | 0 |
| ⬜ postposition_order (extra) | 150 | 150 | 0 | 0 | – | 0 | 0 |
| **Total** | **2,400** | **3357** | **1966** | **1795** | | **1204** | **591** |

✅ complete · 🟡 started · ⬜ not started. *Accepted* includes edited pairs. *In benchmark* = min(accepted, 150); the final 150 are picked at random (seeded) when the benchmark is built. Generated through `scripts/progress.py` from: `pairs_v0.tsv`, `pairs_v1_dative_allomorphy.tsv`, `pairs_v1_lexical_case.tsv`, `pairs_v1_npi_hech.tsv`, `pairs_v1_numeral_no_plural.tsv`, `pairs_v1_possessive_agreement.tsv`, `pairs_v1_postposition_case.tsv`, `pairs_v1_stem_alternation.tsv`, `pairs_v1_suspended_affixation.tsv`, `pairs_v2_anaphor_agreement.tsv`, `pairs_v2_binding.tsv`, `pairs_v2_ditransitive_dative.tsv`, `pairs_v2_nominalization.tsv`, `pairs_v2_passives.tsv`, `pairs_v2_person_agreement.tsv`, `pairs_v2_postposition_order.tsv`, `pairs_v2_quantifiers.tsv`, `pairs_v2_relative_clauses.tsv`, `pairs_v2_vowel_glide.tsv`.
