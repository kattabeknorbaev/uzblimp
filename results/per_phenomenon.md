# Accuracy (%) per phenomenon

Written by `scripts/make_table.py` from `results/json/`.

## Current Latin

| Phenomenon | GF-L 5MB (logprob) | GF-L 10MB (logprob) | GF-L 100MB (logprob) | GF-L full (logprob) | GF-C 5MB (logprob) | GF-C 10MB (logprob) | GF-C 100MB (logprob) | GF-C full (logprob) | tahrirchi-bert (pll) | Qwen2.5-0.5B (logprob) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anaphor_agreement | 44.0 | 82.7 | 98.7 | 100.0 | 54.0 | 49.3 | 40.7 | 49.3 | 99.3 | 50.7 |
| binding | 9.3 | 22.7 | 90.7 | 93.3 | 0.0 | 0.0 | 0.0 | 3.3 | 100.0 | 7.3 |
| dative_allomorphy | 60.7 | 70.0 | 88.0 | 90.0 | 3.3 | 0.0 | 1.3 | 6.7 | 92.7 | 14.0 |
| ditransitive_dative | 42.0 | 64.7 | 96.7 | 98.0 | 46.0 | 30.0 | 45.3 | 46.0 | 99.3 | 31.3 |
| lexical_case | 63.3 | 76.7 | 98.7 | 99.3 | 30.7 | 44.0 | 45.3 | 56.0 | 100.0 | 31.3 |
| nominalization | 100.0 | 100.0 | 100.0 | 100.0 | 79.3 | 74.7 | 90.7 | 87.3 | 99.3 | 92.0 |
| npi_hech | 19.3 | 28.0 | 93.3 | 96.0 | 2.0 | 0.0 | 2.7 | 2.7 | 96.0 | 5.3 |
| numeral_no_plural | 76.0 | 89.3 | 93.3 | 95.3 | 97.3 | 99.3 | 93.3 | 92.0 | 98.0 | 77.3 |
| passives | 64.0 | 72.7 | 94.0 | 96.0 | 22.0 | 15.3 | 50.7 | 49.3 | 98.0 | 60.7 |
| person_agreement | 57.3 | 66.0 | 99.3 | 98.7 | 46.0 | 50.0 | 51.3 | 53.3 | 100.0 | 52.0 |
| possessive_agreement | 77.3 | 83.3 | 96.7 | 97.3 | 65.3 | 68.0 | 66.7 | 69.3 | 100.0 | 71.3 |
| postposition_case | 100.0 | 100.0 | 100.0 | 100.0 | 13.3 | 11.3 | 48.0 | 47.3 | 100.0 | 64.7 |
| quantifiers | 85.3 | 87.3 | 96.0 | 97.3 | 98.0 | 97.3 | 80.7 | 78.0 | 98.7 | 82.0 |
| relative_clauses | 90.0 | 96.0 | 98.0 | 98.7 | 48.0 | 32.0 | 70.0 | 62.7 | 98.7 | 66.7 |
| stem_alternation | 92.0 | 88.7 | 95.3 | 95.3 | 78.7 | 74.7 | 60.7 | 70.7 | 99.3 | 61.3 |
| suspended_affixation | 32.0 | 44.0 | 92.7 | 91.3 | 40.0 | 3.3 | 14.7 | 16.0 | 98.0 | 40.7 |
| **All** | **63.3** | **73.2** | **95.7** | **96.7** | **45.2** | **40.6** | **47.6** | **49.4** | **98.6** | **50.5** |

## Cyrillic

| Phenomenon | GF-L 5MB (logprob) | GF-L 10MB (logprob) | GF-L 100MB (logprob) | GF-L full (logprob) | GF-C 5MB (logprob) | GF-C 10MB (logprob) | GF-C 100MB (logprob) | GF-C full (logprob) | tahrirchi-bert (pll) | Qwen2.5-0.5B (logprob) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anaphor_agreement | 68.7 | 42.0 | 88.0 | 94.0 | 40.7 | 40.7 | 99.3 | 100.0 | 72.0 | 38.0 |
| binding | 0.0 | 10.7 | 67.3 | 79.3 | 2.0 | 6.0 | 81.3 | 93.3 | 39.3 | 1.3 |
| dative_allomorphy | 24.0 | 26.7 | 70.7 | 71.3 | 54.0 | 70.0 | 87.3 | 93.3 | 48.7 | 67.3 |
| ditransitive_dative | 40.7 | 34.0 | 94.7 | 97.3 | 39.3 | 51.3 | 94.0 | 98.7 | 89.3 | 24.0 |
| lexical_case | 53.3 | 63.3 | 98.7 | 98.7 | 66.7 | 74.0 | 98.0 | 98.7 | 84.0 | 28.7 |
| nominalization | 85.3 | 94.7 | 99.3 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 98.0 | 52.7 |
| npi_hech | 13.3 | 12.0 | 79.3 | 88.0 | 16.0 | 20.0 | 86.0 | 94.0 | 21.3 | 4.0 |
| numeral_no_plural | 90.7 | 86.7 | 80.7 | 81.3 | 76.7 | 81.3 | 96.0 | 98.7 | 73.3 | 94.7 |
| passives | 30.7 | 38.7 | 86.7 | 89.3 | 65.3 | 68.7 | 94.7 | 96.7 | 81.3 | 18.0 |
| person_agreement | 46.7 | 50.7 | 87.3 | 94.7 | 51.3 | 50.7 | 96.0 | 97.3 | 83.3 | 52.0 |
| possessive_agreement | 73.3 | 75.3 | 91.3 | 94.7 | 79.3 | 80.0 | 96.7 | 95.3 | 74.7 | 72.7 |
| postposition_case | 80.0 | 97.3 | 99.3 | 99.3 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 57.3 |
| quantifiers | 91.3 | 86.7 | 92.0 | 92.7 | 82.7 | 82.0 | 97.3 | 98.0 | 84.0 | 97.3 |
| relative_clauses | 90.0 | 92.7 | 98.7 | 98.0 | 97.3 | 98.7 | 98.7 | 100.0 | 97.3 | 56.7 |
| stem_alternation | 60.7 | 77.3 | 96.7 | 94.0 | 90.0 | 90.7 | 94.7 | 97.3 | 93.3 | 54.7 |
| suspended_affixation | 9.3 | 6.0 | 84.7 | 90.7 | 20.7 | 30.0 | 94.0 | 97.3 | 89.3 | 20.7 |
| **All** | **53.6** | **55.9** | **88.5** | **91.5** | **61.4** | **65.2** | **94.6** | **97.4** | **76.8** | **46.2** |

## Reformed Latin

| Phenomenon | tahrirchi-bert (pll) | Qwen2.5-0.5B (logprob) |
|---|---:|---:|
| anaphor_agreement | 86.7 | 42.0 |
| binding | 29.3 | 4.0 |
| dative_allomorphy | 90.7 | 37.3 |
| ditransitive_dative | 98.7 | 39.3 |
| lexical_case | 87.3 | 28.0 |
| nominalization | 74.7 | 19.3 |
| npi_hech | 61.3 | 13.3 |
| numeral_no_plural | 96.0 | 86.7 |
| passives | 98.0 | 54.0 |
| person_agreement | 99.3 | 46.7 |
| possessive_agreement | 100.0 | 70.7 |
| postposition_case | 100.0 | 72.0 |
| quantifiers | 98.0 | 82.7 |
| relative_clauses | 95.3 | 44.7 |
| stem_alternation | 84.0 | 57.3 |
| suspended_affixation | 98.0 | 59.3 |
| **All** | **87.3** | **47.3** |
