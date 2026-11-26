# Forced choice with Claude models

Four Claude models judged every pair of UzBLiMP v1.2 in each of the three alphabets: for each pair, which of the
two sentences is grammatically correct. The runs were made on 25 November 2026 by `scripts/claude_fc.py`, as
subagents of Claude Code 2.1.332 (its Workflow tool) through a Claude subscription rather than through the API. The scores are forced choices by prompting and are not comparable with the likelihood scores of the other
models in the paper.

| Alias | Model that answered (from the transcripts) |
|---|---|
| fable | claude-fable-5-2 |
| opus | claude-opus-5-5 |
| sonnet | claude-sonnet-5-5 |
| haiku | claude-haiku-5-5 |

## Design

- **Requests of 150 pairs.** The 2,400 pairs were shuffled once (seed 2026) and cut into 16 batches of 150, so every
  request mixes all 16 phenomena (`plan_v1.2.json`). All models, alphabets and orders use the same batches.
- **Both orders.** Every pair was shown twice, in separate requests: in pass A, 75 pairs of each batch show the
  grammatical sentence first and 75 the ungrammatical one; pass B reverses every pair.
- **Prompt.** The question of the API pilot (`scripts/score_api.py`), asked for 150 numbered items at once, with the
  instruction to answer from knowledge of Uzbek and not to use tools (the text is `HEADER` in
  `scripts/claude_fc.py`, which also renders the items). No hint about the alphabet; the same English
  instructions for all three alphabets. Answers were returned as a list of (item, 1 or 2) through Claude Code's
  structured output; a request whose list was incomplete or repeated an item would have been sent again (none was).
- **Settings.** Reasoning effort low for every model, as in the pilot; sampling settings cannot be set in Claude
  Code. Each subagent also saw Claude Code's own system prompt, which offers its tools, file access to this
  repository (and so to the answer key) included; the harness's relay of the instruction that started the run (the
  request to evaluate the models on all pairs); and a short note of the harness before the prompt, which it
  indented line by line. None of these contains a pair or an answer, and the audit below shows that no request
  used the tools.
- **Audit.** `audit.json` lists, for every request including the four trial requests, the alias, the model named in
  the transcript and the tools it called. Every request was answered by the model named above and called no tool
  except the one that returns the structured answer.

## Files

- `<alias>_<alphabet>.csv`: one row per pair, in benchmark order: the answer and whether it is correct with the
  grammatical sentence first (`gb`) and second (`bg`), the number of attempts of each request, `accuracy` (mean of the
  two orders) and `consistent` (both orders correct).
- `raw/`: the workflows' return values (answers per request as strings of 1 and 2).
- `trial/`: the four trial requests (batch 1, pass A, current Latin) made before the full runs; they repeat a
  request of the full runs and show how stable the answers are.

## Caveat

Claude models helped build and audit the benchmark (paper, Section 4.2, paragraph "Audit", and the Ethics
statement): both passes of the audit of the selected pairs (generator errors, such as ungrammatical members with a
grammatical reading, and spelling and OCR errors in every grammatical sentence) and the audit of the Cyrillic
conversion were run with Claude, and the errors we confirmed were corrected or their pairs replaced. The benchmark is therefore partly filtered by a Claude model's judgments, and these scores are not
independent evidence of the models' knowledge of Uzbek or of the benchmark's validity.
