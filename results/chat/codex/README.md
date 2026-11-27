# Forced choice with GPT through Codex

Two GPT 6.2 models judged every pair of UzBLiMP v1.2 in each of the three alphabets, in both orders, in OpenAI
Codex under a ChatGPT Plus subscription (not through the API), with reasoning set to Light for the whole of
each run. The runs were set up by an AI agent (Grok Bot) for the second author, who ran Codex on his own
computer. The scores are forced choices by prompting and are not comparable with the likelihood scores of the
other models in the paper.

## Design

- **The requests of the Claude runs.** `scripts/codex_fc.py kit` writes 96 question files: the 16 batches of 150
  pairs of `results/chat/claude/plan_v1.2.json` in current Latin, Cyrillic and reformed Latin, each in pass A
  (the order of the plan) and pass B (every pair reversed). Files 1-16 are current Latin A, 17-32 current Latin B,
  33-48 Cyrillic A, 49-64 Cyrillic B, 65-80 reformed Latin A, 81-96 reformed Latin B.
- **Prompt.** Each file starts with the question of the Claude runs (`HEADER` in `scripts/claude_fc.py`) without
  its sentence about tools, since Codex has to read the question files and write its answers. The prompt pasted
  into Codex (`PROMPT` in `scripts/codex_fc.py`) asks it to read only the question files, to answer from its
  own knowledge of Uzbek, not to run code or scripts to decide the answers, not to search the web, and to write
  one answer file per question file. The kit holds no pair id, phenomenon name or answer, and Codex was opened in
  the kit's folder only, not in this repository. The kit that was used is reproduced byte for byte by
  `scripts/codex_fc.py kit`. For Astra, one sentence was added: it was told to read each pair in full and not to
  write helpers that shorten, diff or pre-process the pairs, and to use code only to read the question files and
  save its answers.
- **Sessions.** Codex stopped after a few files at a time; the same prompt was pasted again until all 96 answer
  files existed. Model and reasoning level were not changed during a run.

## GPT 6.2 Sol (26 November 2026)

The second author's Codex session log was read after the run (it is not in this repository). Every answer
was typed by the model itself; no script chose an answer. From batch 09 on, however, Codex wrote and used a
small helper that shortened each pair to the words in which its two sentences differ, plus a few words of
context around them, and it judged from that shortened view rather than from the full sentences. Batches 01-08
were read in full. This differs from the Claude runs, which saw whole sentences, and goes against the instruction
not to run code or scripts to decide the answers, although the helper chose no answer.

14,384 of the 14,400 judgments are correct (99.9%): current Latin 99.8% (10 wrong of 4,800), Cyrillic 99.9%
(3 wrong), reformed Latin 99.9% (3 wrong).

## GPT 6.2 Astra (26-27 November 2026)

The session log (not in this repository) shows that every answer was typed by the model itself; no script chose
an answer. It read the question files in full, later in two halves when a file was long, and it did not use
shortening helpers. The session had three context compactions, and after a usage-limit pause one already written
answer file was written again unchanged.

All 14,400 judgments are correct (100% in each alphabet, and consistent in both orders on every pair).

## Files

- `gpt_<alphabet>.csv` and `astra_<alphabet>.csv`: one row per pair, in benchmark order, in the format of
  `results/chat/claude/`: the answer and whether it is correct with the grammatical sentence first (`gb`) and
  second (`bg`), the answer file each came from, `accuracy` (mean of the two orders) and `consistent` (both
  orders correct).
- `gpt_answers/` and `astra_answers/`: the 96 answer files as Codex wrote them. Rebuild the CSVs with
  `scripts/codex_fc.py collect <answers folder> --alias gpt --model "GPT 6.2 Sol" --effort light` or
  `--alias astra --model "GPT 6.2 Astra" --effort light`.
