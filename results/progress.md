# UzBLiMP progress

**Checkpoint 01 November 2026: at least 600 accepted pairs (goal ~1,000)** in the benchmark, 24 days from 08 October 2026. Full set: 16 × 150 = 2,400.

- Benchmark pairs so far: **462 / 2,400** (19%); checkpoint minimum: 462 / 600.
- Phenomena complete: 3 / 16. Reserve pairs: 247.

| Phenomenon | Target | Generated | Reviewed | Accepted | Acceptance | In benchmark | Reserve |
|---|---|---|---|---|---|---|---|
| 🟡 anaphor_agreement | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 lexical_case | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 ditransitive_dative | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 binding | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 stem_alternation | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| ✅ npi_hech | 150 | 252 | 252 | 233 | 92% | 150 | 83 |
| 🟡 suspended_affixation | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 nominalization | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| ⬜ person_agreement | 150 | 1 | 0 | 0 | – | 0 | 0 |
| 🟡 ellipsis | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 scrambling | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| 🟡 impersonal_passive | 150 | 1 | 1 | 1 | 100% | 1 | 0 |
| ✅ numeral_no_plural | 150 | 252 | 251 | 234 | 93% | 150 | 84 |
| ✅ postposition_case | 150 | 252 | 252 | 230 | 91% | 150 | 80 |
| ⬜ possessive_agreement | 150 | 1 | 0 | 0 | – | 0 | 0 |
| 🟡 dative_allomorphy | 150 | 2 | 2 | 2 | 100% | 2 | 0 |
| **Total** | **2,400** | **770** | **767** | **709** | | **462** | **247** |

✅ complete · 🟡 started · ⬜ not started. *Accepted* includes edited pairs. *In benchmark* = min(accepted, 150); the final 150 are picked at random (seeded) when the benchmark is built. Generated through `scripts/progress.py` from: `pairs_v0.tsv`, `pairs_v1_npi_hech.tsv`, `pairs_v1_numeral_no_plural.tsv`, `pairs_v1_postposition_case.tsv`.
