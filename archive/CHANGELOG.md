# Changelog

Versions of the benchmark and the main additions to the repository. Details are in `log.md`; the results of each
version up to v1.1 are in `results/` and its reports in `results/eval_v*.md`.

## After v1.2 (benchmark unchanged)

- 2026-11-26: repository restructured: the release in `data/`, the scripts needed to evaluate models and rebuild
  the paper in `scripts/`, the final results in `results/` (by type: `lm/`, `chat/`, `human/`), everything else
  in `archive/`. No data, scores or paper numbers changed.
- 2026-11-26: GPU run 3: the four registered models not scored before (mGPT, mGPT-Uzbek, Glot500, XLM-R large)
  and eight further models (Gemma 3 4B, 12B and 27B, Aya Expanse 8B, alloma 8B, Llama 3.1 8B Uz, NeuronAI-Uzbek,
  Qwen3.5-9B Kazakh); GPT 6.2 Sol through OpenAI Codex on all pairs, in both orders.
- 2026-11-26: forced choice by chat models of other developers through OpenRouter (Kimi K3.1 Pro and GLM 5.3 on
  all pairs; DeepSeek V4 Flash, MiniMax M3.1 Flash and Seed 2.1 Turbo on part of them); a runner for Gemini through
  the Gemini CLI.
- 2026-11-25: forced choice by four Claude models on all pairs, in both orders and all three alphabets.
- 2026-11-24: 14 larger models (up to 36 billion parameters) and Tomaris.ai, scored on rented GPUs for the second
  author, checked against our CPU runs and added to the paper (Appendix H).
- 2026-11-22: human validation: five native speakers chose the grammatical sentence of 320 pairs, in 99.2% of
  1,600 judgments; the Cyrillic spot check was completed.

## v1.2 (2026-11-20)

- An audit of the 2,400 selected pairs excluded 55 pairs with generator errors (ungrammatical members with a
  grammatical reading, edited words outside the phenomenon, malformed forms) and 88 with spelling or OCR errors in
  the source sentence; 120 pairs (5.0%) were replaced by the next accepted pairs of their phenomenon.
  `data/benchmark/excluded.tsv` lists the 143 excluded pairs (23 of them from the reserve) with reasons.
- The Cyrillic spelling of Russian loanwords is corrected from a table (72 word forms).
- A model registry (`scripts/models.py`) and runner (`scripts/run_models.py`); results of 17 models on CPU
  (2026-11-21), reusing the v1.1 scores of unchanged pairs.

## Release files (2026-11-01)

- `data/jsonl/`: the pairs in BLiMP-style JSON Lines, one file per phenomenon and alphabet, with the evaluation
  harness `scripts/eval.py`.

## v1.1 (2026-10-27)

- Corpus pairs only: the 12 hand-written seed pairs were replaced; 2,388 pairs unchanged.

## v1.0 (2026-10-26)

- Review complete: all 16 phenomena at 150 pairs (2,400), all 1,200 pairs of v0.2 unchanged, 881 reserve pairs.

## v0.2 (2026-10-18)

- 1,200 pairs (8 phenomena), adding suspended affixation and possessive agreement; all 900 pairs of v0.1
  unchanged. First Cyrillic and reformed Latin versions.

## v0.1 (2026-10-15)

- First, provisional version: 900 pairs (6 phenomena × 150) and the first evaluation of three models.
