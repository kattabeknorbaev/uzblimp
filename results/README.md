# Results

Results on UzBLiMP v1.2: 2,400 pairs in each of the three alphabets. The paper's tables and figures are built from
these files with `python scripts/paper_tables.py` and `python scripts/paper_figures.py`.

| Path | Contents | Written by |
|---|---|---|
| `lm/latn/`, `lm/cyrl/`, `lm/latn_reformed/` | per-pair scores of the open models, one file per model | `scripts/run_models.py` |
| `lm/json/` | accuracy per model, alphabet and phenomenon | `scripts/results_to_json.py`, `scripts/eval.py` |
| `lm/per_phenomenon.md` | the same accuracies as tables | `scripts/make_table.py` |
| `lm/tokenizer_stats.json` | unknown tokens, tokens per sentence and per word | `scripts/run_models.py` |
| `lm/gpu_runs/` | records of the models scored on GPUs, and our checks (`CHECKS.md`) | the GPU runs |
| `chat/claude/` | forced choice by four Claude models, every pair in both orders | `scripts/claude_fc.py` |
| `chat/codex/` | forced choice by GPT 6.2 Sol and GPT 6.2 Astra through OpenAI Codex, every pair in both orders | `scripts/codex_fc.py` |
| `chat/openrouter/` | forced choice by chat models of other developers | `scripts/api_fc.py` |
| `chat/gemini_cli/` | how to run Gemini through the Gemini CLI (no results yet) | `scripts/gemini_cli_fc.py` |
| `human/` | human validation: summary and the released counts | `scripts/human_study_report.py` |

Each per-pair file of `lm/` has one row per pair: the pair (`id`, `phenomenon`, `good`, `bad`), the score of each
sentence (`good_logprob`, `bad_logprob`: log-probability for causal models, pseudo-log-likelihood for masked models)
and `correct`, true when the grammatical sentence scores higher; `correct_norm` makes the same comparison with each
score divided by the sentence's length in UTF-8 bytes.

## Strongest models

Accuracy (%) of the strongest models on all 2,400 pairs. A pair is correct when the model gives the grammatical
sentence the higher log-probability (pseudo-log-likelihood for TahrirchiBERT and UzRoBERTa).

| Model | Trained on | Latin | Cyrillic | Reformed |
|---|---|---:|---:|---:|
| Gemma 4 31B | multilingual | 97.3 | 98.1 | 90.5 |
| Gemma 4 26B-A4B | multilingual | 94.8 | 97.5 | 86.2 |
| Gemma 3 27B | multilingual | 94.1 | 97.7 | 84.5 |
| TahrirchiBERT | Uzbek, Latin script | 98.7 | 76.8 | 87.3 |
| UzRoBERTa | Uzbek, both scripts | 93.4 | 96.4 | 78.0 |
| Goldfish Latin (full) | Uzbek, Latin script | 96.7 | 91.7 | – |
| Goldfish Cyrillic (full) | Uzbek, Cyrillic script | 49.5 | 97.3 | – |

Goldfish models were not scored on reformed Latin, where their tokenizers produce unknown tokens. Native speakers
chose the grammatical sentence in 99.2% of 1,600 judgments.

## Open models

Accuracy (%). logprob: causal language models; pll: masked language models. Reformed Latin is scored only for
models without unknown tokens on its new letters, and not for models trained on Cyrillic only. The Cyrillic run of
alloma 8B is not reported, because its tokenizer deletes Cyrillic letters (`lm/gpu_runs/invalid/`). Tomaris.ai is
the model of the authors' company, and its pretraining corpus contains 99% of the grammatical sentences taken from
the authors' own corpus, so it is not held out (paper, Appendix H).

<!-- results:start -->
| Model | Method | Current Latin | Cyrillic | Reformed Latin |
|---|---|---:|---:|---:|
| GF-L 5MB (`goldfish-models/uzn_latn_5mb`) | logprob | 63.3 | 53.3 | — |
| GF-L 10MB (`goldfish-models/uzn_latn_10mb`) | logprob | 73.4 | 55.8 | — |
| GF-L 100MB (`goldfish-models/uzn_latn_100mb`) | logprob | 95.8 | 88.3 | — |
| GF-L full (`goldfish-models/uzn_latn_full`) | logprob | 96.7 | 91.7 | — |
| GF-C 5MB (`goldfish-models/uzn_cyrl_5mb`) | logprob | 45.2 | 61.3 | — |
| GF-C 10MB (`goldfish-models/uzn_cyrl_10mb`) | logprob | 40.3 | 65.4 | — |
| GF-C 100MB (`goldfish-models/uzn_cyrl_100mb`) | logprob | 47.6 | 94.7 | — |
| GF-C full (`goldfish-models/uzn_cyrl_full`) | logprob | 49.5 | 97.3 | — |
| tahrirchi-bert (`tahrirchi/tahrirchi-bert-base`) | pll | 98.7 | 76.8 | 87.3 |
| tahrirchi-bert-small (`tahrirchi/tahrirchi-bert-small`) | pll | 92.2 | 59.2 | 81.3 |
| BERTbek (`elmurod1202/bertbek-news-big-cased`) | pll | 87.6 | 59.4 | 68.2 |
| UzBERT (`coppercitylabs/uzbert-base-uncased`) | pll | 42.7 | 84.3 | — |
| UzRoBERTa (`rifkat/uztext-3Gb-BPE-Roberta`) | pll | 93.4 | 96.4 | 78.0 |
| mBERT (`google-bert/bert-base-multilingual-cased`) | pll | 62.5 | 51.2 | 55.6 |
| XLM-R base (`FacebookAI/xlm-roberta-base`) | pll | 78.2 | 51.3 | 71.5 |
| Glot500 (`cis-lmu/glot500-base`) | pll | 79.4 | 93.7 | 77.6 |
| XLM-R large (`FacebookAI/xlm-roberta-large`) | pll | 84.0 | 52.8 | 74.5 |
| Qwen2.5-0.5B (`Qwen/Qwen2.5-0.5B`) | logprob | 50.4 | 46.2 | 46.8 |
| Qwen2.5-1.5B (`Qwen/Qwen2.5-1.5B`) | logprob | 55.0 | 53.1 | 49.7 |
| mGPT (`ai-forever/mGPT`) | logprob | 91.2 | 95.6 | 77.3 |
| mGPT-Uzbek (`ai-forever/mGPT-1.3B-uzbek`) | logprob | 91.2 | 61.0 | 75.7 |
| Qwen3.5-0.8B (`Qwen/Qwen3.5-0.8B-Base`) | logprob | 66.3 | 62.8 | 55.8 |
| Qwen3.5-2B (`Qwen/Qwen3.5-2B-Base`) | logprob | 77.1 | 78.7 | 66.1 |
| Qwen3.5-4B (`Qwen/Qwen3.5-4B-Base`) | logprob | 78.6 | 84.1 | 63.4 |
| Qwen3.5-9B (`Qwen/Qwen3.5-9B-Base`) | logprob | 80.0 | 82.1 | 65.5 |
| Gemma 4 E4B (`google/gemma-4-E4B`) | logprob | 91.9 | 95.9 | 78.3 |
| Llama 3.1 8B (`unsloth/Meta-Llama-3.1-8B`) | logprob | 81.6 | 73.2 | 65.1 |
| Mistral Small 3.1 (`mistralai/Mistral-Small-3.1-24B-Base-2503`) | logprob | 83.9 | 77.8 | 71.8 |
| Gemma 4 26B-A4B (`google/gemma-4-26B-A4B`) | logprob | 94.8 | 97.5 | 86.2 |
| Gemma 4 31B (`google/gemma-4-31B`) | logprob | 97.3 | 98.1 | 90.5 |
| Qwen3.5-27B (`Qwen/Qwen3.5-27B`) | logprob | 92.3 | 95.1 | 82.2 |
| Qwen3.6-27B (`Qwen/Qwen3.6-27B`) | logprob | 93.3 | 93.8 | 83.3 |
| Qwen3.8-27B (`Qwen/Qwen3.8-27B`) | logprob | 92.9 | 94.4 | 81.0 |
| Qwen3.5-35B-A3B (`Qwen/Qwen3.5-35B-A3B-Base`) | logprob | 92.5 | 95.6 | 80.7 |
| Qwen3.6-35B-A3B (`Qwen/Qwen3.6-35B-A3B`) | logprob | 91.0 | 91.6 | 78.5 |
| Gemma 3 4B (`google/gemma-3-4b-pt`) | logprob | 86.9 | 91.5 | 70.1 |
| Gemma 3 12B (`google/gemma-3-12b-pt`) | logprob | 92.9 | 96.0 | 79.5 |
| Gemma 3 27B (`google/gemma-3-27b-pt`) | logprob | 94.1 | 97.7 | 84.5 |
| Aya Expanse 8B (`CohereLabs/aya-expanse-8b`) | logprob | 54.0 | 55.1 | 54.3 |
| alloma 8B (`uzlm/alloma-8B-Base`) | logprob | 92.5 | — | 74.8 |
| Llama 3.1 8B Uz (`behbudiy/Llama-3.1-8B-Instruct-Uz`) | logprob | 89.2 | 73.8 | 71.2 |
| NeuronAI-Uzbek (`NeuronUz/NeuronAI-Uzbek`) | logprob | 78.1 | 81.0 | 67.5 |
| Qwen3.5-9B Kazakh (`issai/Qwen3.5-9B-Base-Kazakh`) | logprob | 90.5 | 88.0 | 76.8 |
| Tomaris.ai (not held out) (`tomaris/Tomaris.ai`) | logprob | 98.7 | 92.6 | 92.8 |
<!-- results:end -->

## Chat models

Prompted to choose the grammatical sentence in requests of 150 numbered pairs (paper, Appendix I). A prompted choice
is not comparable with the likelihood scores above, and as Claude models helped build and audit the benchmark,
their scores are not independent of it. Accuracy (%) over both orders; in parentheses, the share of pairs answered
correctly in both.

<!-- claude:start -->
| Model | Current Latin | Cyrillic | Reformed Latin |
|---|---:|---:|---:|
| Claude Fable 5.2 | 100.0 (100.0) | 100.0 (100.0) | 100.0 (100.0) |
| Claude Opus 5.5 | 100.0 (100.0) | 100.0 (100.0) | 99.9 (99.9) |
| Claude Sonnet 5.5 | 99.0 (98.0) | 99.2 (98.5) | 98.6 (97.3) |
| Claude Haiku 5.5 | 96.7 (93.7) | 96.5 (93.1) | 97.4 (95.1) |
<!-- claude:end -->

GPT 6.2 Sol answered the same requests in both orders through OpenAI Codex: 99.8 (99.6) in current Latin, 99.9 (99.9)
in Cyrillic and 99.9 (99.9) in reformed Latin. From its ninth request on, Codex judged each pair through a helper it
wrote that cut the two sentences down to the words that differ and a few words around them. GPT 6.2 Astra answered
the same requests with an added instruction to read each pair in full and did not use shortening helpers: 100.0 (100.0)
in all three alphabets ([`chat/codex/`](chat/codex/README.md)).

Chat models of other developers answered the same requests through OpenRouter, each pair once. Only Kimi and GLM
answered every pair: DeepSeek V4 Flash and Seed 2.1 Turbo often reasoned until their token limit without answering
(those pairs, perhaps the harder ones, are missing), Seed was stopped early, and the budget of about $10 ran out
during the MiniMax run. The number of pairs is given where it is not 2,400 ([`chat/openrouter/`](chat/openrouter/README.md)).

<!-- chat:start -->
| Model | Current Latin | Cyrillic | Reformed Latin |
|---|---:|---:|---:|
| Kimi K3.1 Pro | 99.2 | 99.0 | 99.1 |
| GLM 5.3 | 95.8 | 95.9 | 95.5 |
| DeepSeek V4 Flash | 99.2 | 98.9 (1,800 pairs) | 99.5 (600 pairs) |
| MiniMax M3.1 Flash | 87.6 (1,950 pairs) | — | — |
| Seed 2.1 Turbo | 100.0 (450 pairs) | 98.7 (150 pairs) | 100.0 (150 pairs) |
<!-- chat:end -->
