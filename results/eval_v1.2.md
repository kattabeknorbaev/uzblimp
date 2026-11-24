# UzBLiMP v1.2: audited benchmark and model evaluation (2026-11-21; larger models added 2026-11-24)

**v1.2 = v1.1 with 120 pairs (5.0%) replaced** after an audit of the selected pairs (generator errors, then spelling and OCR errors found by a surprisal screen and a proofreading pass) and with the Cyrillic spelling of Russian loanwords corrected (72 word forms). The 143 excluded pairs (120 from the benchmark, 23 from the reserve) are listed with their reasons in `data/benchmark/excluded.tsv` and still have to be confirmed by the authors; 724 accepted pairs remain in reserve. Results reuse the v1.1 scores of unchanged pairs and score the rest (`scripts/run_models.py --carry-from v1.1`); all runs are float32 on CPU. The tables below come from `scripts/eval_report.py --previous v1.1`; the paper (`paper/uzblimp.pdf`) reports the same 42 runs of 17 models.

**Main results**
- In their own script, the best models reach 98.7% (Latin) and 97.3% (Cyrillic). With 100 MB of training text or more, the Latin and Cyrillic Goldfish models reach comparable accuracy (differences of at most 2.1 points except at 10 MB, where the Latin model is 8.0 points ahead).
- Models trained on one script lose 5.0 to 47.8 points on the other script (TahrirchiBERT 21.9, UzBERT 41.6). UzRoBERTa, trained on both scripts, scores 93.4% on Latin and 96.4% on Cyrillic, but loses 15.4 points in the reformed spelling.
- Reformed Latin costs TahrirchiBERT 11.4 points; where only the grammatical member's edited word contains a new letter, its accuracy falls from 99.6% to 44.5%.
- Multilingual models know much less of this grammar: XLM-R 78.2% on Latin (51.3% on Cyrillic), mBERT 62.5%, Qwen2.5 50.4% (0.5B) and 55.0% (1.5B).
- Larger models (added 2026-11-24): 14 open models from 0.9 to 36 billion parameters, scored on rented GPUs for the second author with `scripts/eval.py` (record and checks in `results/gpu_runs/`; paper Appendix H). They reach 66.3–97.3% on Latin and 62.8–98.1% on Cyrillic (11 of 14 higher on Cyrillic; Gemma 4 31B 97.3/98.1). Reformed Latin costs every one of them 6.8–16.5 points, 25.2–66.1 where only the grammatical member's edited word contains a new letter against 7.3–20.8 where both members' do. Tomaris.ai (98.7/92.6/92.8) is the model of the authors' company and is not held out: its private pretraining corpus contains 99.3% of the grammatical sentences from our own corpus (`results/gpu_runs/tomaris_overlap_v1.2.json`). The tables below list the larger models after the CPU models.
- The less grammar a run can use, the more its choices follow token counts: across all 42 runs, the gap between pairs whose ungrammatical member has more and fewer tokens falls as accuracy on equal-length pairs rises (Spearman ρ = −0.65; −0.67 without binding and NPI licensing). Byte normalisation does not remove the gap: of the 38 runs with a gap above ten points, 30 keep one of more than ten points and 18 reverse its sign.

## Accuracy (%) by model and alphabet (2400 pairs, 16 phenomena; chance 50)

Byte-normalised accuracy (log-probability per UTF-8 byte) in parentheses; 95% Wilson intervals are at most ±2 points.

| Model | Hugging Face id | Uzbek data | Latin | Cyrillic | Reformed |
|---|---|---|---|---|---|
| GF-L 5MB | goldfish-models/uzn_latn_5mb | latn | 63.3 (68.7) | 53.3 (56.0) | – |
| GF-L 10MB | goldfish-models/uzn_latn_10mb | latn | 73.4 (75.6) | 55.8 (61.6) | – |
| GF-L 100MB | goldfish-models/uzn_latn_100mb | latn | 95.8 (94.8) | 88.3 (85.3) | – |
| GF-L full | goldfish-models/uzn_latn_full | latn | 96.7 (95.3) | 91.7 (88.2) | – |
| GF-C 5MB | goldfish-models/uzn_cyrl_5mb | cyrl | 45.2 (51.5) | 61.3 (66.9) | – |
| GF-C 10MB | goldfish-models/uzn_cyrl_10mb | cyrl | 40.3 (51.2) | 65.4 (71.5) | – |
| GF-C 100MB | goldfish-models/uzn_cyrl_100mb | cyrl | 47.6 (53.7) | 94.7 (93.5) | – |
| GF-C full | goldfish-models/uzn_cyrl_full | cyrl | 49.5 (55.7) | 97.3 (95.7) | – |
| tahrirchi-bert | tahrirchi/tahrirchi-bert-base | latn | 98.7 (98.5) | 76.8 (76.4) | 87.3 (89.7) |
| tahrirchi-bert-small | tahrirchi/tahrirchi-bert-small | latn | 92.2 (92.9) | 59.2 (61.4) | 81.3 (81.7) |
| BERTbek | elmurod1202/bertbek-news-big-cased | latn | 87.6 (88.1) | 59.4 (61.1) | 68.2 (69.7) |
| UzBERT | coppercitylabs/uzbert-base-uncased | cyrl | 42.7 (46.4) | 84.3 (85.3) | – |
| UzRoBERTa | rifkat/uztext-3Gb-BPE-Roberta | both | 93.4 (93.4) | 96.4 (96.0) | 78.0 (80.1) |
| mBERT | google-bert/bert-base-multilingual-cased | multi | 62.5 (66.0) | 51.2 (54.6) | 55.6 (57.6) |
| XLM-R base | FacebookAI/xlm-roberta-base | multi | 78.2 (78.8) | 51.3 (51.5) | 71.5 (73.4) |
| Qwen2.5-0.5B | Qwen/Qwen2.5-0.5B | multi | 50.4 (56.8) | 46.2 (49.3) | 46.8 (53.0) |
| Qwen2.5-1.5B | Qwen/Qwen2.5-1.5B | multi | 55.0 (62.2) | 53.1 (55.6) | 49.7 (55.2) |
| Qwen3.5-0.8B | Qwen/Qwen3.5-0.8B-Base | multi | 66.3 (69.9) | 62.8 (65.5) | 55.8 (59.2) |
| Qwen3.5-2B | Qwen/Qwen3.5-2B-Base | multi | 77.1 (78.3) | 78.7 (77.6) | 66.1 (69.5) |
| Qwen3.5-4B | Qwen/Qwen3.5-4B-Base | multi | 78.6 (78.5) | 84.1 (80.3) | 63.4 (65.9) |
| Qwen3.5-9B | Qwen/Qwen3.5-9B-Base | multi | 80.0 (81.9) | 82.1 (81.0) | 65.5 (69.3) |
| Gemma 4 E4B | google/gemma-4-E4B | multi | 91.9 (90.4) | 95.9 (91.9) | 78.3 (77.5) |
| Llama 3.1 8B | unsloth/Meta-Llama-3.1-8B | multi | 81.6 (81.5) | 73.2 (71.3) | 65.1 (67.0) |
| Mistral Small 3.1 | mistralai/Mistral-Small-3.1-24B-Base-2503 | multi | 83.9 (84.2) | 77.8 (75.2) | 71.8 (74.0) |
| Gemma 4 26B-A4B | google/gemma-4-26B-A4B | multi | 94.8 (93.3) | 97.5 (95.0) | 86.2 (84.7) |
| Gemma 4 31B | google/gemma-4-31B | multi | 97.3 (96.4) | 98.1 (95.7) | 90.5 (89.0) |
| Qwen3.5-27B | Qwen/Qwen3.5-27B | multi | 92.3 (90.7) | 95.1 (90.8) | 82.2 (81.8) |
| Qwen3.6-27B | Qwen/Qwen3.6-27B | multi | 93.3 (91.6) | 93.8 (90.5) | 83.3 (82.6) |
| Qwen3.8-27B | Qwen/Qwen3.8-27B | multi | 92.9 (91.0) | 94.4 (92.3) | 81.0 (81.0) |
| Qwen3.5-35B-A3B | Qwen/Qwen3.5-35B-A3B-Base | multi | 92.5 (91.4) | 95.6 (92.3) | 80.7 (81.5) |
| Qwen3.6-35B-A3B | Qwen/Qwen3.6-35B-A3B | multi | 91.0 (89.3) | 91.6 (88.5) | 78.5 (78.5) |
| Tomaris.ai (not held out) | tomaris/Tomaris.ai | multi | 98.7 (97.5) | 92.6 (90.3) | 92.8 (91.6) |

## Accuracy per phenomenon, own script (multilingual models: Latin)

| Model | Text | Ana | LexC | Ditr | Bind | Stem | NPI | Susp | Nmlz | Subj | Pass | Rel | Quan | Num | Post | Poss | Dat | All |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-L 5MB | Latin | 44.7 | 63.3 | 42.0 | 9.3 | 92.0 | 17.3 | 32.7 | 100.0 | 57.3 | 64.0 | 94.0 | 84.7 | 74.7 | 100.0 | 76.7 | 60.7 | **63.3** |
| GF-L 10MB | Latin | 84.0 | 77.3 | 66.0 | 22.7 | 88.0 | 26.7 | 44.0 | 100.0 | 66.0 | 74.0 | 97.3 | 87.3 | 87.3 | 100.0 | 84.0 | 70.0 | **73.4** |
| GF-L 100MB | Latin | 99.3 | 98.7 | 97.3 | 90.7 | 95.3 | 94.0 | 91.3 | 100.0 | 99.3 | 94.0 | 98.0 | 96.0 | 94.0 | 100.0 | 96.7 | 88.0 | **95.8** |
| GF-L full | Latin | 100.0 | 99.3 | 98.0 | 93.3 | 95.3 | 96.7 | 90.7 | 100.0 | 98.7 | 96.0 | 99.3 | 97.3 | 94.7 | 100.0 | 97.3 | 90.0 | **96.7** |
| GF-C 5MB | Cyrillic | 41.3 | 65.3 | 40.0 | 2.0 | 89.3 | 15.3 | 19.3 | 100.0 | 51.3 | 64.7 | 98.7 | 82.7 | 76.0 | 100.0 | 80.0 | 54.0 | **61.3** |
| GF-C 10MB | Cyrillic | 41.3 | 74.0 | 52.0 | 6.0 | 90.7 | 19.3 | 29.3 | 100.0 | 50.7 | 68.0 | 100.0 | 82.0 | 82.0 | 100.0 | 81.3 | 69.3 | **65.4** |
| GF-C 100MB | Cyrillic | 99.3 | 98.7 | 94.7 | 81.3 | 94.7 | 85.3 | 92.7 | 100.0 | 96.0 | 94.7 | 100.0 | 97.3 | 96.7 | 100.0 | 96.0 | 87.3 | **94.7** |
| GF-C full | Cyrillic | 100.0 | 98.7 | 98.7 | 93.3 | 97.3 | 94.7 | 96.0 | 100.0 | 97.3 | 96.7 | 100.0 | 98.0 | 98.0 | 100.0 | 95.3 | 93.3 | **97.3** |
| tahrirchi-bert | Latin | 99.3 | 100.0 | 99.3 | 100.0 | 99.3 | 96.7 | 98.0 | 99.3 | 100.0 | 98.0 | 100.0 | 98.7 | 98.7 | 100.0 | 100.0 | 92.0 | **98.7** |
| tahrirchi-bert-small | Latin | 96.7 | 97.3 | 96.0 | 48.0 | 99.3 | 84.0 | 94.0 | 100.0 | 99.3 | 98.7 | 100.0 | 93.3 | 93.3 | 99.3 | 97.3 | 78.7 | **92.2** |
| BERTbek | Latin | 76.7 | 84.0 | 92.7 | 44.7 | 86.7 | 85.3 | 91.3 | 98.0 | 94.7 | 93.3 | 93.3 | 90.0 | 92.0 | 100.0 | 95.3 | 84.0 | **87.6** |
| UzBERT | Cyrillic | 91.3 | 80.7 | 92.0 | 7.3 | 93.3 | 55.3 | 98.0 | 100.0 | 97.3 | 94.0 | 90.7 | 95.3 | 88.0 | 82.0 | 99.3 | 84.0 | **84.3** |
| UzRoBERTa | Latin | 96.0 | 99.3 | 97.3 | 36.0 | 99.3 | 95.3 | 99.3 | 100.0 | 99.3 | 99.3 | 99.3 | 94.7 | 92.0 | 100.0 | 98.0 | 89.3 | **93.4** |
| mBERT | Latin | 44.0 | 57.3 | 65.3 | 24.0 | 67.3 | 3.3 | 52.7 | 94.0 | 50.7 | 86.0 | 93.3 | 85.3 | 62.7 | 97.3 | 74.0 | 43.3 | **62.5** |
| XLM-R base | Latin | 66.0 | 62.0 | 79.3 | 52.0 | 70.0 | 62.7 | 90.0 | 99.3 | 96.0 | 95.3 | 96.7 | 90.0 | 68.0 | 95.3 | 90.7 | 38.0 | **78.2** |
| Qwen2.5-0.5B | Latin | 51.3 | 32.7 | 32.0 | 7.3 | 58.7 | 4.7 | 38.0 | 92.0 | 52.0 | 61.3 | 68.0 | 82.0 | 78.0 | 63.3 | 71.3 | 14.0 | **50.4** |
| Qwen2.5-1.5B | Latin | 59.3 | 35.3 | 35.3 | 14.7 | 75.3 | 9.3 | 43.3 | 99.3 | 49.3 | 61.3 | 82.7 | 88.7 | 76.7 | 72.0 | 73.3 | 4.7 | **55.0** |
| Qwen3.5-0.8B | Latin | 64.0 | 49.3 | 54.0 | 33.3 | 82.7 | 26.7 | 43.3 | 100.0 | 60.7 | 84.7 | 88.0 | 76.0 | 74.7 | 89.3 | 76.7 | 57.3 | **66.3** |
| Qwen3.5-2B | Latin | 67.3 | 70.0 | 76.7 | 59.3 | 84.7 | 53.3 | 68.0 | 99.3 | 73.3 | 95.3 | 96.7 | 86.7 | 80.0 | 84.0 | 84.0 | 54.7 | **77.1** |
| Qwen3.5-4B | Latin | 78.0 | 70.0 | 72.0 | 68.0 | 88.7 | 60.7 | 62.0 | 100.0 | 82.0 | 92.0 | 93.3 | 90.7 | 81.3 | 92.7 | 82.7 | 43.3 | **78.6** |
| Qwen3.5-9B | Latin | 87.3 | 70.0 | 78.7 | 69.3 | 86.0 | 61.3 | 58.7 | 99.3 | 80.0 | 96.0 | 96.0 | 95.3 | 83.3 | 79.3 | 82.0 | 56.7 | **80.0** |
| Gemma 4 E4B | Latin | 94.7 | 88.7 | 72.7 | 79.3 | 92.7 | 94.7 | 86.7 | 100.0 | 90.7 | 98.7 | 98.7 | 97.3 | 94.0 | 98.7 | 93.3 | 89.3 | **91.9** |
| Llama 3.1 8B | Latin | 78.0 | 75.3 | 67.3 | 71.3 | 88.7 | 67.3 | 78.0 | 99.3 | 72.0 | 97.3 | 96.7 | 86.0 | 81.3 | 90.0 | 80.7 | 76.0 | **81.6** |
| Mistral Small 3.1 | Latin | 76.0 | 81.3 | 66.0 | 78.0 | 90.0 | 73.3 | 72.7 | 100.0 | 75.3 | 98.0 | 96.7 | 91.3 | 87.3 | 87.3 | 88.0 | 80.7 | **83.9** |
| Gemma 4 26B-A4B | Latin | 95.3 | 90.7 | 76.7 | 95.3 | 94.0 | 97.3 | 92.7 | 100.0 | 94.0 | 99.3 | 98.7 | 98.7 | 96.7 | 98.0 | 94.7 | 94.0 | **94.8** |
| Gemma 4 31B | Latin | 100.0 | 94.7 | 89.3 | 95.3 | 96.7 | 99.3 | 98.7 | 100.0 | 98.7 | 99.3 | 99.3 | 99.3 | 94.7 | 98.7 | 98.0 | 94.7 | **97.3** |
| Qwen3.5-27B | Latin | 86.7 | 91.3 | 85.3 | 85.3 | 88.7 | 90.7 | 92.0 | 100.0 | 90.7 | 99.3 | 98.7 | 95.3 | 89.3 | 99.3 | 92.7 | 90.7 | **92.3** |
| Qwen3.6-27B | Latin | 92.7 | 82.0 | 82.7 | 90.7 | 91.3 | 93.3 | 96.7 | 100.0 | 98.7 | 100.0 | 98.7 | 94.0 | 86.0 | 98.7 | 94.0 | 93.3 | **93.3** |
| Qwen3.8-27B | Latin | 95.3 | 91.3 | 87.3 | 92.0 | 88.0 | 85.3 | 88.7 | 100.0 | 95.3 | 97.3 | 98.7 | 92.7 | 92.7 | 96.0 | 93.3 | 92.7 | **92.9** |
| Qwen3.5-35B-A3B | Latin | 93.3 | 92.0 | 81.3 | 86.7 | 90.0 | 87.3 | 92.0 | 100.0 | 90.7 | 98.7 | 98.7 | 98.0 | 92.7 | 96.0 | 94.0 | 88.0 | **92.5** |
| Qwen3.6-35B-A3B | Latin | 90.0 | 91.3 | 80.0 | 83.3 | 95.3 | 90.0 | 82.0 | 100.0 | 88.0 | 98.0 | 98.0 | 96.7 | 91.3 | 96.7 | 93.3 | 82.7 | **91.0** |
| Tomaris.ai (not held out) | Latin | 100.0 | 98.7 | 96.7 | 98.7 | 98.0 | 98.7 | 100.0 | 100.0 | 99.3 | 100.0 | 100.0 | 98.7 | 99.3 | 100.0 | 100.0 | 91.3 | **98.7** |

## Accuracy per phenomenon, other script

| Model | Text | Ana | LexC | Ditr | Bind | Stem | NPI | Susp | Nmlz | Subj | Pass | Rel | Quan | Num | Post | Poss | Dat | All |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF-L 5MB | Cyrillic | 68.0 | 51.3 | 40.0 | 0.0 | 60.7 | 12.0 | 7.3 | 85.3 | 46.7 | 32.7 | 90.7 | 91.3 | 88.7 | 80.0 | 73.3 | 24.7 | **53.3** |
| GF-L 10MB | Cyrillic | 42.7 | 62.7 | 33.3 | 10.7 | 77.3 | 12.0 | 6.0 | 94.7 | 50.7 | 38.7 | 93.3 | 86.7 | 84.7 | 97.3 | 76.0 | 26.0 | **55.8** |
| GF-L 100MB | Cyrillic | 89.3 | 98.7 | 94.7 | 67.3 | 95.3 | 79.3 | 83.3 | 99.3 | 87.3 | 86.7 | 98.7 | 92.0 | 78.0 | 100.0 | 92.0 | 70.7 | **88.3** |
| GF-L full | Cyrillic | 94.7 | 99.3 | 97.3 | 79.3 | 94.0 | 88.0 | 90.7 | 100.0 | 94.7 | 88.7 | 99.3 | 92.7 | 83.3 | 100.0 | 94.7 | 70.7 | **91.7** |
| GF-C 5MB | Latin | 53.3 | 32.0 | 46.7 | 0.0 | 76.0 | 1.3 | 41.3 | 79.3 | 46.0 | 23.3 | 46.7 | 98.0 | 98.0 | 13.3 | 64.7 | 3.3 | **45.2** |
| GF-C 10MB | Latin | 48.7 | 44.0 | 31.3 | 0.0 | 72.7 | 0.0 | 2.7 | 74.7 | 50.0 | 15.3 | 31.3 | 97.3 | 98.7 | 10.0 | 68.0 | 0.0 | **40.3** |
| GF-C 100MB | Latin | 41.3 | 44.7 | 46.0 | 0.0 | 61.3 | 2.7 | 14.7 | 90.7 | 51.3 | 50.0 | 68.0 | 80.0 | 92.0 | 50.0 | 68.0 | 1.3 | **47.6** |
| GF-C full | Latin | 49.3 | 54.7 | 48.0 | 3.3 | 70.7 | 4.0 | 16.0 | 86.7 | 53.3 | 49.3 | 60.7 | 77.3 | 92.0 | 48.7 | 71.3 | 6.7 | **49.5** |
| tahrirchi-bert | Cyrillic | 72.7 | 82.7 | 89.3 | 39.3 | 95.3 | 21.3 | 91.3 | 98.0 | 83.3 | 79.3 | 97.3 | 83.3 | 71.3 | 100.0 | 74.0 | 50.0 | **76.8** |
| tahrirchi-bert-small | Cyrillic | 56.7 | 58.7 | 66.0 | 50.0 | 89.3 | 7.3 | 42.0 | 56.7 | 63.3 | 26.0 | 96.7 | 74.7 | 77.3 | 97.3 | 72.0 | 12.7 | **59.2** |
| BERTbek | Cyrillic | 50.0 | 47.3 | 45.3 | 42.7 | 70.7 | 25.3 | 65.3 | 78.0 | 52.0 | 32.0 | 78.0 | 80.7 | 74.0 | 94.0 | 72.7 | 42.7 | **59.4** |
| UzBERT | Latin | 34.0 | 34.0 | 23.3 | 11.3 | 45.3 | 7.3 | 67.3 | 56.0 | 49.3 | 16.7 | 55.3 | 72.7 | 81.3 | 42.7 | 66.7 | 20.0 | **42.7** |
| UzRoBERTa | Cyrillic | 95.3 | 100.0 | 99.3 | 77.3 | 94.0 | 96.7 | 98.7 | 100.0 | 100.0 | 100.0 | 100.0 | 96.7 | 96.7 | 100.0 | 99.3 | 88.7 | **96.4** |
| mBERT | Cyrillic | 46.0 | 44.7 | 26.7 | 6.0 | 64.7 | 6.7 | 78.7 | 54.0 | 48.7 | 37.3 | 52.7 | 83.3 | 82.7 | 55.3 | 69.3 | 62.7 | **51.2** |
| XLM-R base | Cyrillic | 34.0 | 63.3 | 45.3 | 2.7 | 58.0 | 3.3 | 48.7 | 39.3 | 62.0 | 26.0 | 60.0 | 90.7 | 90.0 | 56.7 | 71.3 | 69.3 | **51.3** |
| Qwen2.5-0.5B | Cyrillic | 38.7 | 28.0 | 24.0 | 1.3 | 55.3 | 4.0 | 20.0 | 53.3 | 52.0 | 20.0 | 54.0 | 97.3 | 94.7 | 57.3 | 71.3 | 68.0 | **46.2** |
| Qwen2.5-1.5B | Cyrillic | 38.7 | 37.3 | 52.0 | 1.3 | 56.7 | 6.0 | 14.0 | 81.3 | 56.0 | 48.0 | 87.3 | 85.3 | 84.0 | 61.3 | 74.0 | 66.0 | **53.1** |
| Qwen3.5-0.8B | Cyrillic | 54.7 | 46.0 | 42.0 | 5.3 | 67.3 | 36.7 | 58.0 | 92.0 | 60.0 | 81.3 | 81.3 | 84.0 | 65.3 | 79.3 | 80.0 | 71.3 | **62.8** |
| Qwen3.5-2B | Cyrillic | 67.3 | 74.7 | 69.3 | 47.3 | 93.3 | 73.3 | 74.0 | 100.0 | 82.0 | 90.0 | 97.3 | 89.3 | 70.0 | 82.7 | 82.7 | 65.3 | **78.7** |
| Qwen3.5-4B | Cyrillic | 84.7 | 84.0 | 73.3 | 70.7 | 90.7 | 72.7 | 81.3 | 97.3 | 86.7 | 94.7 | 96.0 | 91.3 | 78.0 | 92.7 | 92.7 | 58.7 | **84.1** |
| Qwen3.5-9B | Cyrillic | 86.0 | 69.3 | 79.3 | 88.7 | 83.3 | 58.7 | 58.7 | 95.3 | 89.3 | 92.7 | 96.7 | 95.3 | 84.0 | 80.0 | 89.3 | 66.7 | **82.1** |
| Gemma 4 E4B | Cyrillic | 96.7 | 95.3 | 84.0 | 92.0 | 96.0 | 98.7 | 92.7 | 99.3 | 98.0 | 98.7 | 99.3 | 99.3 | 92.7 | 98.7 | 96.0 | 97.3 | **95.9** |
| Llama 3.1 8B | Cyrillic | 72.0 | 73.3 | 63.3 | 35.3 | 56.7 | 58.0 | 71.3 | 98.0 | 69.3 | 91.3 | 90.0 | 77.3 | 77.3 | 86.7 | 75.3 | 75.3 | **73.2** |
| Mistral Small 3.1 | Cyrillic | 66.0 | 76.0 | 50.0 | 49.3 | 79.3 | 88.0 | 68.7 | 97.3 | 68.0 | 90.0 | 96.7 | 97.3 | 83.3 | 89.3 | 86.0 | 59.3 | **77.8** |
| Gemma 4 26B-A4B | Cyrillic | 97.3 | 97.3 | 84.7 | 97.3 | 98.0 | 98.0 | 98.0 | 100.0 | 99.3 | 100.0 | 100.0 | 100.0 | 97.3 | 98.0 | 98.0 | 97.3 | **97.5** |
| Gemma 4 31B | Cyrillic | 100.0 | 96.0 | 91.3 | 96.7 | 96.0 | 98.0 | 97.3 | 100.0 | 100.0 | 99.3 | 100.0 | 100.0 | 98.0 | 98.7 | 99.3 | 98.7 | **98.1** |
| Qwen3.5-27B | Cyrillic | 98.7 | 91.3 | 86.0 | 97.3 | 92.7 | 96.0 | 95.3 | 100.0 | 99.3 | 98.7 | 99.3 | 96.0 | 90.7 | 97.3 | 94.7 | 88.0 | **95.1** |
| Qwen3.6-27B | Cyrillic | 94.0 | 90.7 | 73.3 | 94.7 | 92.7 | 95.3 | 94.0 | 100.0 | 98.7 | 98.0 | 99.3 | 96.0 | 90.0 | 95.3 | 94.0 | 95.3 | **93.8** |
| Qwen3.8-27B | Cyrillic | 97.3 | 88.7 | 82.0 | 98.7 | 95.3 | 96.0 | 92.7 | 99.3 | 96.0 | 99.3 | 96.7 | 96.7 | 91.3 | 94.7 | 95.3 | 90.7 | **94.4** |
| Qwen3.5-35B-A3B | Cyrillic | 97.3 | 92.7 | 86.7 | 92.0 | 92.0 | 98.7 | 95.3 | 99.3 | 97.3 | 98.0 | 99.3 | 98.7 | 94.7 | 98.0 | 94.7 | 94.7 | **95.6** |
| Qwen3.6-35B-A3B | Cyrillic | 86.7 | 93.3 | 82.7 | 87.3 | 92.0 | 94.0 | 88.0 | 99.3 | 96.7 | 96.7 | 98.7 | 88.0 | 86.7 | 94.7 | 96.0 | 85.3 | **91.6** |
| Tomaris.ai (not held out) | Cyrillic | 87.3 | 88.7 | 90.0 | 96.0 | 94.0 | 95.3 | 90.7 | 99.3 | 97.3 | 98.7 | 99.3 | 92.7 | 98.7 | 99.3 | 98.0 | 56.0 | **92.6** |

## Accuracy per phenomenon, reformed Latin

| Model | Text | Ana | LexC | Ditr | Bind | Stem | NPI | Susp | Nmlz | Subj | Pass | Rel | Quan | Num | Post | Poss | Dat | All |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tahrirchi-bert | Reformed | 87.3 | 87.3 | 98.7 | 29.3 | 83.3 | 61.3 | 98.0 | 74.7 | 99.3 | 98.0 | 96.0 | 97.3 | 96.0 | 100.0 | 100.0 | 90.0 | **87.3** |
| tahrirchi-bert-small | Reformed | 96.0 | 84.7 | 94.0 | 11.3 | 84.7 | 36.0 | 96.7 | 40.7 | 99.3 | 97.3 | 97.3 | 94.7 | 91.3 | 100.0 | 98.0 | 78.7 | **81.3** |
| BERTbek | Reformed | 70.0 | 40.7 | 84.0 | 8.0 | 64.7 | 24.7 | 89.3 | 14.0 | 90.7 | 87.3 | 81.3 | 88.7 | 82.0 | 98.7 | 92.0 | 74.7 | **68.2** |
| UzRoBERTa | Reformed | 80.0 | 56.0 | 93.3 | 10.0 | 78.0 | 40.0 | 95.3 | 28.7 | 99.3 | 98.0 | 96.0 | 96.7 | 90.7 | 100.0 | 98.7 | 87.3 | **78.0** |
| mBERT | Reformed | 41.3 | 36.7 | 58.0 | 5.3 | 58.0 | 8.7 | 63.3 | 28.7 | 49.3 | 79.3 | 88.7 | 83.3 | 62.0 | 95.3 | 68.7 | 62.7 | **55.6** |
| XLM-R base | Reformed | 82.0 | 41.3 | 74.0 | 41.3 | 68.7 | 58.7 | 88.7 | 33.3 | 94.0 | 88.7 | 94.7 | 87.3 | 63.3 | 96.7 | 87.3 | 44.7 | **71.5** |
| Qwen2.5-0.5B | Reformed | 42.7 | 27.3 | 38.7 | 4.0 | 54.0 | 12.0 | 56.7 | 19.3 | 46.7 | 54.7 | 44.7 | 82.7 | 88.0 | 72.0 | 68.0 | 36.7 | **46.8** |
| Qwen2.5-1.5B | Reformed | 48.0 | 34.7 | 30.0 | 5.3 | 67.3 | 22.7 | 51.3 | 30.7 | 48.7 | 61.3 | 74.0 | 87.3 | 82.7 | 68.0 | 67.3 | 16.0 | **49.7** |
| Qwen3.5-0.8B | Reformed | 62.7 | 25.3 | 51.3 | 2.0 | 73.3 | 13.3 | 60.0 | 24.0 | 62.0 | 79.3 | 68.0 | 77.3 | 72.0 | 80.7 | 75.3 | 66.7 | **55.8** |
| Qwen3.5-2B | Reformed | 71.3 | 43.3 | 72.0 | 30.7 | 75.3 | 34.7 | 72.0 | 30.0 | 74.7 | 89.3 | 85.3 | 82.0 | 78.7 | 78.0 | 80.0 | 60.7 | **66.1** |
| Qwen3.5-4B | Reformed | 67.3 | 48.0 | 66.7 | 12.0 | 70.0 | 43.3 | 59.3 | 35.3 | 75.3 | 89.3 | 80.0 | 90.0 | 74.7 | 84.0 | 76.7 | 42.0 | **63.4** |
| Qwen3.5-9B | Reformed | 73.3 | 59.3 | 64.7 | 27.3 | 70.0 | 32.0 | 56.7 | 41.3 | 74.0 | 89.3 | 87.3 | 94.7 | 78.7 | 72.0 | 72.7 | 54.7 | **65.5** |
| Gemma 4 E4B | Reformed | 81.3 | 63.3 | 66.7 | 30.7 | 80.0 | 84.0 | 82.0 | 59.3 | 85.3 | 97.3 | 94.0 | 90.7 | 86.7 | 76.7 | 90.7 | 84.0 | **78.3** |
| Llama 3.1 8B | Reformed | 57.3 | 37.3 | 64.7 | 6.0 | 70.0 | 50.7 | 70.0 | 39.3 | 66.0 | 94.7 | 85.3 | 81.3 | 77.3 | 81.3 | 80.7 | 80.0 | **65.1** |
| Mistral Small 3.1 | Reformed | 61.3 | 65.3 | 66.7 | 24.7 | 68.7 | 66.7 | 71.3 | 50.7 | 74.0 | 96.0 | 88.7 | 86.7 | 78.7 | 83.3 | 82.7 | 84.0 | **71.8** |
| Gemma 4 26B-A4B | Reformed | 89.3 | 80.0 | 78.0 | 70.0 | 82.0 | 83.3 | 86.7 | 74.7 | 93.3 | 96.7 | 95.3 | 92.0 | 88.7 | 88.0 | 92.7 | 88.7 | **86.2** |
| Gemma 4 31B | Reformed | 91.3 | 88.0 | 86.0 | 63.3 | 87.3 | 92.0 | 96.0 | 92.0 | 96.0 | 98.0 | 98.0 | 96.7 | 86.7 | 87.3 | 96.7 | 93.3 | **90.5** |
| Qwen3.5-27B | Reformed | 88.0 | 72.0 | 87.3 | 39.3 | 76.0 | 71.3 | 90.0 | 82.0 | 88.0 | 98.0 | 92.0 | 88.0 | 82.0 | 90.7 | 86.7 | 84.0 | **82.2** |
| Qwen3.6-27B | Reformed | 90.7 | 76.7 | 82.7 | 41.3 | 76.7 | 73.3 | 90.0 | 82.7 | 92.7 | 97.3 | 91.3 | 89.3 | 83.3 | 90.7 | 88.7 | 85.3 | **83.3** |
| Qwen3.8-27B | Reformed | 90.7 | 75.3 | 78.7 | 42.0 | 75.3 | 70.7 | 90.0 | 70.0 | 91.3 | 95.3 | 94.0 | 88.7 | 82.7 | 86.0 | 90.0 | 76.0 | **81.0** |
| Qwen3.5-35B-A3B | Reformed | 88.0 | 61.3 | 75.3 | 32.7 | 77.3 | 74.7 | 90.0 | 82.0 | 86.7 | 98.7 | 88.0 | 90.0 | 86.0 | 85.3 | 92.0 | 82.7 | **80.7** |
| Qwen3.6-35B-A3B | Reformed | 82.7 | 64.7 | 75.3 | 40.7 | 81.3 | 78.0 | 80.7 | 79.3 | 82.7 | 96.7 | 87.3 | 87.3 | 77.3 | 86.0 | 86.0 | 70.7 | **78.5** |
| Tomaris.ai (not held out) | Reformed | 98.7 | 92.7 | 88.7 | 72.7 | 88.0 | 96.0 | 98.7 | 76.7 | 98.0 | 98.0 | 98.0 | 95.3 | 96.7 | 100.0 | 99.3 | 88.0 | **92.8** |

## Own script against other script (same pairs)

Exact McNemar test and percentile bootstrap (2,000 resamples) over pairs.

| Comparison | Δ (points) | 95% CI | only first right | only second right | p (McNemar) | p (Holm) |
|---|---|---|---|---|---|---|
| GF-L 5MB: Latin vs Cyrillic | +10.0 | +7.8 .. +12.2 | 486 | 245 | 3.3e-19 | 6.2e-18 |
| GF-L 10MB: Latin vs Cyrillic | +17.6 | +15.5 .. +19.6 | 569 | 146 | 8.6e-60 | 2.1e-58 |
| GF-L 100MB: Latin vs Cyrillic | +7.5 | +6.1 .. +8.9 | 242 | 62 | 2.8e-26 | 5.9e-25 |
| GF-L full: Latin vs Cyrillic | +5.0 | +3.8 .. +6.2 | 169 | 50 | 2.7e-16 | 4.6e-15 |
| GF-C 5MB: Cyrillic vs Latin | +16.0 | +13.7 .. +18.2 | 619 | 234 | 7.2e-41 | 1.7e-39 |
| GF-C 10MB: Cyrillic vs Latin | +25.1 | +22.9 .. +27.3 | 762 | 160 | 1.5e-94 | 3.8e-93 |
| GF-C 100MB: Cyrillic vs Latin | +47.0 | +45.1 .. +49.1 | 1149 | 20 | 2.0e-309 | 6.2e-308 |
| GF-C full: Cyrillic vs Latin | +47.8 | +45.8 .. +49.9 | 1163 | 15 | 4.0e-321 | 1.3e-319 |
| tahrirchi-bert: Latin vs Cyrillic | +21.9 | +20.2 .. +23.7 | 541 | 15 | 8.3e-139 | 2.3e-137 |
| tahrirchi-bert-small: Latin vs Cyrillic | +33.0 | +30.9 .. +35.2 | 856 | 63 | 1.4e-178 | 4.0e-177 |
| BERTbek: Latin vs Cyrillic | +28.2 | +26.1 .. +30.5 | 807 | 130 | 5.6e-120 | 1.5e-118 |
| UzBERT: Cyrillic vs Latin | +41.6 | +39.3 .. +43.8 | 1093 | 95 | 1.4e-215 | 4.1e-214 |
| UzRoBERTa: Latin vs Cyrillic | -3.0 | -4.0 .. -1.9 | 46 | 118 | 1.8e-08 | 2.1e-07 |
| mBERT: Latin vs Cyrillic | +11.3 | +9.0 .. +13.6 | 589 | 317 | 1.2e-19 | 2.3e-18 |
| XLM-R base: Latin vs Cyrillic | +26.9 | +24.5 .. +29.4 | 868 | 222 | 1.1e-90 | 2.8e-89 |
| Qwen2.5-0.5B: Latin vs Cyrillic | +4.2 | +1.9 .. +6.5 | 464 | 363 | 5.0e-04 | 0.004 |
| Qwen2.5-1.5B: Latin vs Cyrillic | +2.0 | -0.3 .. +4.2 | 431 | 384 | 0.107 | 0.428 |
| Qwen3.5-0.8B: Latin vs Cyrillic | +3.5 | +1.3 .. +5.7 | 418 | 334 | 0.002 | 0.020 |
| Qwen3.5-2B: Latin vs Cyrillic | -1.6 | -3.6 .. +0.3 | 272 | 310 | 0.125 | 0.428 |
| Qwen3.5-4B: Latin vs Cyrillic | -5.5 | -7.3 .. -3.7 | 188 | 320 | 5.1e-09 | 7.1e-08 |
| Qwen3.5-9B: Latin vs Cyrillic | -2.1 | -4.0 .. -0.3 | 232 | 283 | 0.027 | 0.165 |
| Gemma 4 E4B: Latin vs Cyrillic | -4.0 | -5.2 .. -2.8 | 62 | 159 | 5.2e-11 | 8.4e-10 |
| Llama 3.1 8B: Latin vs Cyrillic | +8.4 | +6.3 .. +10.4 | 403 | 201 | 1.5e-16 | 2.7e-15 |
| Mistral Small 3.1: Latin vs Cyrillic | +6.1 | +4.1 .. +7.9 | 355 | 209 | 8.3e-10 | 1.2e-08 |
| Gemma 4 26B-A4B: Latin vs Cyrillic | -2.8 | -3.8 .. -1.8 | 35 | 102 | 8.7e-09 | 1.1e-07 |
| Gemma 4 31B: Latin vs Cyrillic | -0.8 | -1.6 .. -0.0 | 35 | 54 | 0.056 | 0.279 |
| Qwen3.5-27B: Latin vs Cyrillic | -2.8 | -4.0 .. -1.7 | 72 | 140 | 3.5e-06 | 3.5e-05 |
| Qwen3.6-27B: Latin vs Cyrillic | -0.5 | -1.7 .. +0.6 | 99 | 112 | 0.409 | 0.818 |
| Qwen3.8-27B: Latin vs Cyrillic | -1.5 | -2.7 .. -0.3 | 100 | 136 | 0.023 | 0.158 |
| Qwen3.5-35B-A3B: Latin vs Cyrillic | -3.1 | -4.4 .. -2.0 | 72 | 147 | 4.5e-07 | 4.9e-06 |
| Qwen3.6-35B-A3B: Latin vs Cyrillic | -0.6 | -2.0 .. +0.8 | 149 | 163 | 0.462 | 0.818 |
| Tomaris.ai: Latin vs Cyrillic | +6.1 | +5.0 .. +7.2 | 165 | 18 | 6.4e-31 | 1.4e-29 |

## Current against reformed Latin

| Comparison | Δ (points) | 95% CI | only first right | only second right | p (McNemar) | p (Holm) |
|---|---|---|---|---|---|---|
| tahrirchi-bert: Latin vs Reformed | +11.4 | +10.1 .. +12.7 | 285 | 11 | 5.2e-70 | 1.1e-68 |
| tahrirchi-bert-small: Latin vs Reformed | +10.9 | +9.5 .. +12.3 | 298 | 36 | 1.8e-52 | 3.0e-51 |
| BERTbek: Latin vs Reformed | +19.5 | +17.5 .. +21.5 | 572 | 105 | 1.2e-78 | 2.6e-77 |
| UzRoBERTa: Latin vs Reformed | +15.4 | +13.9 .. +16.9 | 399 | 29 | 2.7e-84 | 6.3e-83 |
| mBERT: Latin vs Reformed | +7.0 | +5.1 .. +8.8 | 348 | 181 | 3.4e-13 | 1.4e-12 |
| XLM-R base: Latin vs Reformed | +6.7 | +5.0 .. +8.5 | 326 | 166 | 4.8e-13 | 1.4e-12 |
| Qwen2.5-0.5B: Latin vs Reformed | +3.7 | +1.5 .. +5.7 | 350 | 262 | 4.3e-04 | 4.3e-04 |
| Qwen2.5-1.5B: Latin vs Reformed | +5.3 | +3.2 .. +7.3 | 379 | 251 | 3.8e-07 | 7.7e-07 |
| Qwen3.5-0.8B: Latin vs Reformed | +10.5 | +8.5 .. +12.3 | 419 | 168 | 1.0e-25 | 5.1e-25 |
| Qwen3.5-2B: Latin vs Reformed | +11.0 | +9.0 .. +12.9 | 424 | 161 | 2.9e-28 | 1.7e-27 |
| Qwen3.5-4B: Latin vs Reformed | +15.2 | +13.3 .. +17.1 | 470 | 105 | 4.5e-56 | 8.0e-55 |
| Qwen3.5-9B: Latin vs Reformed | +14.5 | +12.7 .. +16.2 | 464 | 117 | 7.7e-50 | 1.2e-48 |
| Gemma 4 E4B: Latin vs Reformed | +13.6 | +12.1 .. +15.2 | 382 | 56 | 9.8e-61 | 2.0e-59 |
| Llama 3.1 8B: Latin vs Reformed | +16.5 | +14.5 .. +18.4 | 522 | 127 | 9.7e-58 | 1.9e-56 |
| Mistral Small 3.1: Latin vs Reformed | +12.0 | +10.3 .. +13.8 | 407 | 118 | 3.3e-38 | 3.3e-37 |
| Gemma 4 26B-A4B: Latin vs Reformed | +8.5 | +7.2 .. +10.0 | 256 | 51 | 5.3e-34 | 4.2e-33 |
| Gemma 4 31B: Latin vs Reformed | +6.8 | +5.7 .. +7.9 | 181 | 19 | 2.5e-34 | 2.2e-33 |
| Qwen3.5-27B: Latin vs Reformed | +10.0 | +8.5 .. +11.6 | 307 | 66 | 2.9e-38 | 3.2e-37 |
| Qwen3.6-27B: Latin vs Reformed | +10.0 | +8.5 .. +11.5 | 299 | 59 | 9.2e-40 | 1.1e-38 |
| Qwen3.8-27B: Latin vs Reformed | +11.9 | +10.2 .. +13.5 | 348 | 63 | 7.3e-49 | 1.0e-47 |
| Qwen3.5-35B-A3B: Latin vs Reformed | +11.8 | +10.2 .. +13.4 | 344 | 61 | 5.6e-49 | 8.4e-48 |
| Qwen3.6-35B-A3B: Latin vs Reformed | +12.5 | +10.8 .. +14.2 | 395 | 95 | 1.7e-44 | 2.2e-43 |
| Tomaris.ai: Latin vs Reformed | +5.9 | +4.9 .. +6.9 | 151 | 10 | 1.8e-33 | 1.2e-32 |

## Script-matched Goldfish models (Latin model on Latin vs Cyrillic model on Cyrillic)

| Comparison | Δ (points) | 95% CI | only first right | only second right | p (McNemar) | p (Holm) |
|---|---|---|---|---|---|---|
| 5MB | +2.1 | +0.3 .. +4.0 | 280 | 230 | 0.030 | 0.090 |
| 10MB | +8.0 | +6.2 .. +9.9 | 362 | 169 | 3.6e-17 | 1.4e-16 |
| 100MB | +1.1 | +0.1 .. +2.2 | 95 | 68 | 0.041 | 0.090 |
| full | -0.7 | -1.5 .. +0.2 | 44 | 60 | 0.141 | 0.141 |

## Reformed Latin by where the new letters fall (current → reformed, %)

| Model | critical word: both (n=803) | critical word: grammatical only (n=254) | only other words changed (n=1220) | unchanged (n=123) |
|---|---|---|---|---|
| tahrirchi-bert | 99.3 → 87.7 | 99.6 → 44.5 | 98.2 → 94.8 | 98.4 → 98.4 |
| tahrirchi-bert-small | 95.6 → 82.9 | 68.9 → 21.3 | 94.6 → 91.4 | 94.3 → 94.3 |
| BERTbek | 88.8 → 66.5 | 64.6 → 8.3 | 91.0 → 79.1 | 94.3 → 94.3 |
| UzRoBERTa | 97.4 → 75.5 | 62.2 → 15.0 | 96.7 → 90.7 | 99.2 → 99.2 |
| mBERT | 61.6 → 54.4 | 50.8 → 15.0 | 64.8 → 63.4 | 69.9 → 69.9 |
| XLM-R base | 77.6 → 73.0 | 66.5 → 33.5 | 80.7 → 77.5 | 81.3 → 81.3 |
| Qwen2.5-0.5B | 54.5 → 48.2 | 35.8 → 8.3 | 50.5 → 53.2 | 52.8 → 52.8 |
| Qwen2.5-1.5B | 55.5 → 50.9 | 44.5 → 11.0 | 56.8 → 56.3 | 56.1 → 56.1 |
| Qwen3.5-0.8B | 68.0 → 56.9 | 57.5 → 6.7 | 66.8 → 64.1 | 68.3 → 68.3 |
| Qwen3.5-2B | 77.2 → 65.5 | 71.3 → 24.8 | 77.9 → 73.7 | 80.5 → 80.5 |
| Qwen3.5-4B | 82.6 → 64.1 | 77.6 → 17.3 | 76.7 → 71.5 | 73.2 → 73.2 |
| Qwen3.5-9B | 82.3 → 65.3 | 79.5 → 27.2 | 78.4 → 72.0 | 81.3 → 81.3 |
| Gemma 4 E4B | 94.4 → 80.1 | 85.8 → 35.4 | 91.6 → 84.8 | 91.1 → 91.1 |
| Llama 3.1 8B | 84.7 → 63.9 | 80.3 → 14.2 | 80.5 → 75.6 | 74.8 → 74.8 |
| Mistral Small 3.1 | 86.1 → 72.1 | 83.9 → 28.7 | 83.2 → 80.2 | 76.4 → 76.4 |
| Gemma 4 26B-A4B | 96.6 → 86.4 | 95.3 → 65.7 | 93.6 → 89.7 | 92.7 → 92.7 |
| Gemma 4 31B | 98.6 → 91.3 | 96.5 → 71.3 | 96.6 → 93.4 | 96.7 → 96.7 |
| Qwen3.5-27B | 93.4 → 83.7 | 89.4 → 50.4 | 92.3 → 87.0 | 90.2 → 90.2 |
| Qwen3.6-27B | 95.4 → 85.7 | 92.5 → 52.4 | 92.0 → 87.0 | 94.3 → 94.3 |
| Qwen3.8-27B | 94.3 → 83.4 | 91.3 → 47.2 | 92.5 → 85.5 | 91.1 → 91.1 |
| Qwen3.5-35B-A3B | 95.3 → 81.7 | 89.8 → 47.6 | 91.5 → 86.1 | 89.4 → 88.6 |
| Qwen3.6-35B-A3B | 93.8 → 79.3 | 89.4 → 51.2 | 90.0 → 82.7 | 87.0 → 88.6 |
| Tomaris.ai | 99.1 → 94.8 | 98.4 → 67.7 | 98.4 → 96.1 | 100.0 → 100.0 |

## Length effect: accuracy by token count of the ungrammatical member

Tokens counted with each model's own tokenizer; Δ = accuracy where the ungrammatical member has more tokens minus where it has fewer.

| Model | Text | fewer | same | more | Δ |
|---|---|---|---|---|---|
| GF-L 5MB | Latin | 24.5 (n=335) | 64.1 (n=1672) | 93.1 (n=393) | +68.7 |
| GF-L 5MB | Cyrillic | 29.0 (n=411) | 49.4 (n=1505) | 86.0 (n=484) | +57.0 |
| GF-L 10MB | Latin | 29.1 (n=316) | 77.0 (n=1685) | 93.2 (n=399) | +64.1 |
| GF-L 10MB | Cyrillic | 21.8 (n=335) | 53.0 (n=1624) | 91.8 (n=441) | +70.0 |
| GF-L 100MB | Latin | 86.6 (n=284) | 96.7 (n=1680) | 98.2 (n=436) | +11.5 |
| GF-L 100MB | Cyrillic | 76.3 (n=253) | 88.7 (n=1654) | 93.1 (n=493) | +16.8 |
| GF-L full | Latin | 89.8 (n=284) | 97.6 (n=1680) | 97.7 (n=436) | +7.9 |
| GF-L full | Cyrillic | 79.4 (n=253) | 92.6 (n=1654) | 95.1 (n=493) | +15.7 |
| GF-C 5MB | Latin | 18.0 (n=667) | 42.9 (n=1292) | 93.2 (n=441) | +75.2 |
| GF-C 5MB | Cyrillic | 38.5 (n=187) | 57.3 (n=1835) | 91.5 (n=378) | +53.0 |
| GF-C 10MB | Latin | 7.9 (n=750) | 36.7 (n=1094) | 91.2 (n=556) | +83.3 |
| GF-C 10MB | Cyrillic | 34.4 (n=154) | 61.5 (n=1839) | 94.6 (n=407) | +60.2 |
| GF-C 100MB | Latin | 9.7 (n=761) | 55.0 (n=1132) | 88.0 (n=507) | +78.2 |
| GF-C 100MB | Cyrillic | 77.8 (n=108) | 94.7 (n=1850) | 98.6 (n=442) | +20.9 |
| GF-C full | Latin | 13.3 (n=761) | 57.5 (n=1132) | 86.0 (n=507) | +72.7 |
| GF-C full | Cyrillic | 90.7 (n=108) | 97.4 (n=1850) | 98.6 (n=442) | +7.9 |
| tahrirchi-bert | Latin | 99.1 (n=325) | 98.6 (n=1579) | 98.8 (n=496) | -0.3 |
| tahrirchi-bert | Cyrillic | 50.3 (n=588) | 83.6 (n=1180) | 88.6 (n=632) | +38.3 |
| tahrirchi-bert | Reformed | 59.3 (n=455) | 93.3 (n=1543) | 95.8 (n=402) | +36.4 |
| tahrirchi-bert-small | Latin | 67.0 (n=324) | 96.0 (n=1588) | 96.5 (n=488) | +29.5 |
| tahrirchi-bert-small | Cyrillic | 30.1 (n=642) | 64.7 (n=1279) | 83.5 (n=479) | +53.4 |
| tahrirchi-bert-small | Reformed | 37.1 (n=447) | 90.7 (n=1565) | 94.3 (n=388) | +57.2 |
| BERTbek | Latin | 67.5 (n=403) | 91.6 (n=1564) | 92.1 (n=433) | +24.7 |
| BERTbek | Cyrillic | 44.2 (n=884) | 65.6 (n=1176) | 77.4 (n=340) | +33.1 |
| BERTbek | Reformed | 31.9 (n=527) | 77.3 (n=1495) | 82.5 (n=378) | +50.7 |
| UzBERT | Latin | 27.4 (n=887) | 42.2 (n=856) | 64.1 (n=657) | +36.7 |
| UzBERT | Cyrillic | 34.1 (n=328) | 92.6 (n=1576) | 91.1 (n=496) | +57.0 |
| UzRoBERTa | Latin | 68.1 (n=329) | 97.7 (n=1584) | 96.5 (n=487) | +28.4 |
| UzRoBERTa | Cyrillic | 95.0 (n=181) | 96.0 (n=1753) | 98.5 (n=466) | +3.5 |
| UzRoBERTa | Reformed | 36.5 (n=471) | 86.4 (n=1494) | 94.0 (n=435) | +57.5 |
| mBERT | Latin | 31.8 (n=578) | 69.7 (n=1414) | 81.4 (n=408) | +49.5 |
| mBERT | Cyrillic | 33.9 (n=709) | 49.9 (n=1165) | 77.6 (n=526) | +43.7 |
| mBERT | Reformed | 27.5 (n=612) | 60.9 (n=1380) | 79.7 (n=408) | +52.2 |
| XLM-R base | Latin | 60.4 (n=490) | 81.7 (n=1379) | 85.5 (n=531) | +25.1 |
| XLM-R base | Cyrillic | 20.1 (n=662) | 56.7 (n=1234) | 79.0 (n=504) | +58.9 |
| XLM-R base | Reformed | 48.9 (n=450) | 74.9 (n=1445) | 82.0 (n=505) | +33.1 |
| Qwen2.5-0.5B | Latin | 30.9 (n=650) | 51.3 (n=1262) | 74.0 (n=488) | +43.1 |
| Qwen2.5-0.5B | Cyrillic | 16.7 (n=765) | 50.0 (n=1249) | 92.5 (n=386) | +75.8 |
| Qwen2.5-0.5B | Reformed | 30.6 (n=674) | 46.0 (n=1219) | 70.0 (n=507) | +39.5 |
| Qwen2.5-1.5B | Latin | 36.2 (n=650) | 57.4 (n=1262) | 74.0 (n=488) | +37.8 |
| Qwen2.5-1.5B | Cyrillic | 27.3 (n=765) | 59.7 (n=1249) | 82.6 (n=386) | +55.3 |
| Qwen2.5-1.5B | Reformed | 38.6 (n=674) | 50.0 (n=1219) | 63.7 (n=507) | +25.1 |
| Qwen3.5-0.8B | Latin | 52.0 (n=635) | 70.1 (n=1339) | 75.8 (n=426) | +23.9 |
| Qwen3.5-0.8B | Cyrillic | 42.8 (n=666) | 68.1 (n=1330) | 78.2 (n=404) | +35.4 |
| Qwen3.5-0.8B | Reformed | 33.2 (n=672) | 61.0 (n=1226) | 73.5 (n=502) | +40.3 |
| Qwen3.5-2B | Latin | 66.6 (n=635) | 80.2 (n=1339) | 82.9 (n=426) | +16.2 |
| Qwen3.5-2B | Cyrillic | 69.5 (n=666) | 81.6 (n=1330) | 84.2 (n=404) | +14.6 |
| Qwen3.5-2B | Reformed | 51.8 (n=672) | 69.2 (n=1226) | 77.7 (n=502) | +25.9 |
| Qwen3.5-4B | Latin | 72.6 (n=635) | 79.4 (n=1339) | 85.0 (n=426) | +12.4 |
| Qwen3.5-4B | Cyrillic | 79.9 (n=666) | 85.6 (n=1330) | 86.1 (n=404) | +6.3 |
| Qwen3.5-4B | Reformed | 47.3 (n=672) | 65.0 (n=1226) | 80.9 (n=502) | +33.6 |
| Qwen3.5-9B | Latin | 74.2 (n=635) | 79.5 (n=1339) | 89.9 (n=426) | +15.7 |
| Qwen3.5-9B | Cyrillic | 77.2 (n=666) | 82.2 (n=1330) | 89.9 (n=404) | +12.7 |
| Qwen3.5-9B | Reformed | 47.6 (n=672) | 67.7 (n=1226) | 84.1 (n=502) | +36.4 |
| Gemma 4 E4B | Latin | 87.0 (n=661) | 93.3 (n=1290) | 95.1 (n=449) | +8.1 |
| Gemma 4 E4B | Cyrillic | 93.5 (n=566) | 96.5 (n=1383) | 97.3 (n=451) | +3.9 |
| Gemma 4 E4B | Reformed | 68.3 (n=710) | 83.2 (n=1201) | 80.8 (n=489) | +12.5 |
| Llama 3.1 8B | Latin | 77.3 (n=651) | 82.8 (n=1328) | 84.6 (n=421) | +7.3 |
| Llama 3.1 8B | Cyrillic | 63.6 (n=850) | 77.0 (n=1073) | 81.6 (n=477) | +17.9 |
| Llama 3.1 8B | Reformed | 51.0 (n=698) | 70.0 (n=1204) | 73.1 (n=498) | +22.1 |
| Mistral Small 3.1 | Latin | 80.0 (n=646) | 84.4 (n=1215) | 87.4 (n=539) | +7.4 |
| Mistral Small 3.1 | Cyrillic | 66.1 (n=713) | 79.8 (n=1196) | 89.8 (n=491) | +23.8 |
| Mistral Small 3.1 | Reformed | 61.6 (n=683) | 74.7 (n=1212) | 78.8 (n=505) | +17.2 |
| Gemma 4 26B-A4B | Latin | 91.4 (n=661) | 95.7 (n=1290) | 96.9 (n=449) | +5.5 |
| Gemma 4 26B-A4B | Cyrillic | 96.3 (n=566) | 97.7 (n=1383) | 98.7 (n=451) | +2.4 |
| Gemma 4 26B-A4B | Reformed | 82.4 (n=710) | 88.8 (n=1201) | 85.5 (n=489) | +3.1 |
| Gemma 4 31B | Latin | 96.4 (n=661) | 97.9 (n=1290) | 96.9 (n=449) | +0.5 |
| Gemma 4 31B | Cyrillic | 95.9 (n=566) | 98.6 (n=1383) | 99.1 (n=451) | +3.2 |
| Gemma 4 31B | Reformed | 85.8 (n=710) | 93.3 (n=1201) | 90.8 (n=489) | +5.0 |
| Qwen3.5-27B | Latin | 89.6 (n=635) | 93.4 (n=1339) | 92.5 (n=426) | +2.9 |
| Qwen3.5-27B | Cyrillic | 93.5 (n=666) | 95.9 (n=1330) | 94.8 (n=404) | +1.3 |
| Qwen3.5-27B | Reformed | 76.0 (n=672) | 85.4 (n=1226) | 82.7 (n=502) | +6.6 |
| Qwen3.6-27B | Latin | 92.3 (n=635) | 94.2 (n=1339) | 91.8 (n=426) | -0.5 |
| Qwen3.6-27B | Cyrillic | 90.8 (n=666) | 95.0 (n=1330) | 94.8 (n=404) | +4.0 |
| Qwen3.6-27B | Reformed | 76.3 (n=672) | 86.4 (n=1226) | 85.1 (n=502) | +8.7 |
| Qwen3.8-27B | Latin | 89.3 (n=635) | 94.5 (n=1339) | 93.2 (n=426) | +3.9 |
| Qwen3.8-27B | Cyrillic | 93.5 (n=666) | 94.7 (n=1330) | 94.8 (n=404) | +1.3 |
| Qwen3.8-27B | Reformed | 72.5 (n=672) | 84.4 (n=1226) | 84.3 (n=502) | +11.8 |
| Qwen3.5-35B-A3B | Latin | 89.0 (n=635) | 93.7 (n=1339) | 93.9 (n=426) | +4.9 |
| Qwen3.5-35B-A3B | Cyrillic | 93.7 (n=666) | 96.0 (n=1330) | 97.3 (n=404) | +3.6 |
| Qwen3.5-35B-A3B | Reformed | 72.5 (n=672) | 83.5 (n=1226) | 84.7 (n=502) | +12.2 |
| Qwen3.6-35B-A3B | Latin | 89.0 (n=635) | 91.9 (n=1339) | 91.5 (n=426) | +2.6 |
| Qwen3.6-35B-A3B | Cyrillic | 91.1 (n=666) | 92.3 (n=1330) | 90.3 (n=404) | -0.8 |
| Qwen3.6-35B-A3B | Reformed | 71.1 (n=672) | 82.1 (n=1226) | 79.9 (n=502) | +8.7 |
| Tomaris.ai | Latin | 97.3 (n=376) | 99.0 (n=1463) | 98.9 (n=561) | +1.6 |
| Tomaris.ai | Cyrillic | 93.8 (n=923) | 89.0 (n=844) | 95.6 (n=633) | +1.8 |
| Tomaris.ai | Reformed | 81.0 (n=436) | 95.3 (n=1473) | 95.9 (n=491) | +15.0 |

## Reproducibility: v1.2 against v1.1 on pairs with unchanged text

| Model | Text | shared pairs | same verdict | largest score difference | accuracy v1.1 | accuracy v1.2 |
|---|---|---|---|---|---|---|
| GF-L 100MB | Latin | 2280 | 2280 | 0.0e+00 | 95.7 | 95.8 |
| GF-L 100MB | Cyrillic | 2223 | 2223 | 2.8e-14 | 88.5 | 88.3 |
| GF-C 100MB | Latin | 2280 | 2280 | 2.8e-14 | 47.6 | 47.6 |
| GF-C 100MB | Cyrillic | 2223 | 2223 | 0.0e+00 | 94.6 | 94.7 |
| tahrirchi-bert | Latin | 2280 | 2280 | 0.0e+00 | 98.6 | 98.7 |
| tahrirchi-bert | Cyrillic | 2223 | 2223 | 2.8e-14 | 76.9 | 76.8 |
| tahrirchi-bert | Reformed | 2280 | 2280 | 2.8e-14 | 87.3 | 87.3 |
| Qwen2.5-0.5B | Latin | 2280 | 2280 | 2.8e-14 | 50.5 | 50.4 |
| Qwen2.5-0.5B | Cyrillic | 2223 | 2223 | 2.8e-14 | 46.2 | 46.2 |
| Qwen2.5-0.5B | Reformed | 2280 | 2280 | 2.8e-14 | 47.3 | 46.8 |

Runs reported: 87 (32 models). With 150 pairs, a per-phenomenon accuracy has a 95% Wilson interval of at most ±8 points.
