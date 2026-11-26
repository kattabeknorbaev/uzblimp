# Forced choice with chat models of other developers (OpenRouter)

Five chat models that had no part in building or auditing UzBLiMP answered the requests of the Claude runs
(`results/claude_fc/`) through the OpenRouter API on 26 November 2026, with `scripts/api_fc.py`. Every request is
the prompt of the Claude runs' first pass (pass A), unchanged: 150 numbered pairs, half of them with the grammatical
sentence first. Each pair was therefore asked once, in one order; the second pass was not run, to stay within the
budget. The scores are forced choices by prompting and are not comparable with the likelihood scores of the paper.

| Model | OpenRouter id | Endpoint (precision) |
|---|---|---|
| Kimi K3.1 Pro | moonshotai/kimi-k3.1-pro | morph/fp8 |
| GLM 5.3 | z-ai/glm-5.3 | novita/fp8 |
| DeepSeek V4 Flash | deepseek/deepseek-v4-flash-0731 | deepinfra/fp8/flex |
| MiniMax M3.1 Flash | minimax/minimax-m3.1-flash | parasail/fp8 |
| Seed 2.1 Turbo | bytedance-seed/seed-2-1-turbo | seed/fp8 |

Settings: temperature 0, reasoning effort low, answers as JSON with the schema of the Claude runs, only providers
that support every parameter and do not train on prompts, and fallbacks limited to endpoints in 8-bit or higher
precision. The provider that answered is recorded for every request in the per-pair files.

## What was answered, and why some is missing

- **Kimi K3.1 Pro and GLM 5.3**: every pair in all three alphabets.
- **DeepSeek V4 Flash**: all of current Latin, 12 of 16 batches in Cyrillic and 4 of 16 in reformed Latin. On the
  other batches it reasoned until its token limit (32,000, then 96,000 tokens) without answering, in up to four
  attempts; the batches it could not answer may be harder than the others, so its scores may be too high.
- **Seed 2.1 Turbo**: 5 batches (450 pairs in current Latin, 150 in Cyrillic, 150 in reformed Latin). Most of its
  responses ran out of the 32,000-token limit while reasoning, and it was then stopped at the authors' request.
- **MiniMax M3.1 Flash**: 13 batches of current Latin, when the budget was spent (the API key's limit of $10).
- **DeepSeek V4 Pro**: a planned subset of four batches per alphabet was not reached before the budget was spent;
  only its trial request exists.

`cost.json` gives the requests, valid answers, blocked requests and cost per model, trial included: about $10 in all.

## Files

- `<model>_<alphabet>.csv`: one row per answered pair, in benchmark order: the order shown (`gb`: grammatical first),
  the answer, whether it is correct, the attempt and the provider.
- `runs/`: the runner's record per model and alphabet (answers as strings of 1 and 2, usage per request).
- `cost.json`: cost and counts per model.
- Not in the repository (`.gitignore`): `responses/` (every API response, including the blocked placeholders),
  `truncated/` (responses that ran out of tokens, kept for the cost record) and `trial_responses/`.
