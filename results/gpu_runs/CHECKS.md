# The GPU run of the larger models: what was checked

The second author had 16 models scored on rented GPUs by an AI agent (README.txt, logs/, scripts/; one A100 80 GB and one RTX PRO
6000 96 GB, PyTorch 2.11.0, Transformers 5.24.0) with the repository's `scripts/eval.py` (logprob: summed
log-probability with a start token). `scripts/import_gpu_runs.py` imported the per-pair results of the 15 models in
`scripts/models.py` into `results/` and kept the run's Qwen2.5-1.5B results in `check/` and its float32-against-
bfloat16 control in `bf16check/`. The paper reports the numbers in Appendix H; `scripts/paper_tables.py` computes them
from these files.

Checks made on 2026-11-24, before the results went into the paper:

- **Consistency.** Every per-pair file has the 2,400 pairs of its alphabet, with the benchmark's sentences character
  for character; `correct` equals `good_logprob > bad_logprob`; the accuracies and per-phenomenon accuracies equal
  the run's JSON summaries and README.txt; no two models share score vectors; log-probabilities grow with token
  count as expected; the timings in the logs agree with the queue logs. The import checks ids, sentences and
  judgments again.
- **Same scorer as ours.** The run's Qwen2.5-1.5B scores match our CPU run on all 2,400 pairs in each of the
  three alphabets (7,200 judgments; log-probabilities within 0.002 nats, every judgment and token count the same).
- **Re-scoring on CPU.** `scripts/recheck_gpu_runs.py` re-scored random samples with Qwen3.5-0.8B (80 pairs per
  alphabet) and Qwen3.5-2B (40 of the same pairs per alphabet) in float32 on CPU: all 360 judgments agree with the GPU run, and the
  largest log-probability difference is 0.14 nats (`cpu_recheck_*.csv`). The models above 2 billion parameters
  could not be re-scored on our hardware.
- **Precision.** Qwen3.5-9B-Base in float32 and in bfloat16 gives the same accuracy to one decimal in all three
  alphabets; 0.9 to 1.3% of the pairs are judged differently, in both directions.
- **Models.** All 16 checkpoints are public on Hugging Face. Licences: Apache 2.0, except Llama 3.1 8B (Llama 3.1
  Community License; an ungated copy of Meta's checkpoint with the same parameter count and shard sizes) and
  Tomaris.ai (none stated). Qwen3.5-27B, Qwen3.6-27B, Qwen3.6-35B-A3B and Qwen3.8-27B are post-trained checkpoints
  without a published base model; the Gemma 4 checkpoints are those without the `-it` suffix.
- **Tomaris.ai.** The model of a company that both authors co-founded (Qwen3.5 architecture, tokenizer extended
  for Uzbek, no model card or licence). Its private pretraining corpus contains 1,430 of the 1,440 grammatical
  sentences from our own corpus and 28 of the 960 from UzBooks (`tomaris_overlap_v1.2.json`); its fine-tuning sets
  contain 2. It is reported only as not held out.
