UzBLiMP v1.2: larger open-weight models, scored by sentence log-probability
Date: 2026-11-24 (Asia/Tashkent). Run by Grok Bot for Javohir Matniyozov.

Scorer: the repo's own scripts/eval.py (logprob method: summed natural-log probability per sentence,
BOS prepended when the tokenizer adds none; a pair is correct when the grammatical sentence scores higher).
Data: data/jsonl/{latn,cyrl,latn_reformed} at repo commit 2e5c8cf (kattabeknorbaev/uzblimp), 2,400 pairs per alphabet.
Wrapper: scripts/run_big.py calls eval.py's run_logprob once per model for all three alphabets and writes the
same JSON/CSV files eval.py writes. Local patch (scripts/eval.py.local_patch.diff, never pushed): load weights
straight to the GPU (device_map) and fall back to AutoModelForImageTextToText for text+vision checkpoints.
Only text is ever fed in.

Check: Qwen/Qwen2.5-1.5B reproduced the paper exactly (55.0 / 53.1 / 49.7).
Precision check: Qwen3.5-9B-Base fp32 vs bf16 gave identical accuracy on all three alphabets
(about 1% of pairs flip, in both directions). Models over ~10B ran in bf16 (fp32 does not fit in 80 GB).

GPUs: run 1 = 1x A100-SXM4-80GB (Vast.ai instance 62259889, Texas); run 2 = 1x RTX PRO 6000 S 96GB
(Vast.ai instance 62267994, Virginia). torch 2.11.0+cu128, transformers 5.24.0, flash-linear-attention.

Accuracy (%), L = current Latin, C = Cyrillic, R = reformed 2026 Latin; 2,400 pairs each
model (HF id)                                dtype         L     C     R   run
tomaris/Tomaris.ai                           bfloat16   98.7  92.6  92.8   run1
google/gemma-4-31B                           bfloat16   97.3  98.1  90.5   run1
google/gemma-4-26B-A4B                       bfloat16   94.8  97.5  86.2   run2
Qwen/Qwen3.6-27B                             bfloat16   93.3  93.8  83.3   run2
Qwen/Qwen3.8-27B                             bfloat16   92.9  94.4  81.0   run2
Qwen/Qwen3.5-35B-A3B-Base                    bfloat16   92.5  95.6  80.7   run1
Qwen/Qwen3.5-27B                             bfloat16   92.3  95.1  82.2   run1
google/gemma-4-E4B                           float32    91.9  95.9  78.3   run1
Qwen/Qwen3.6-35B-A3B                         bfloat16   91.0  91.6  78.5   run2
mistralai/Mistral-Small-3.1-24B-Base-2503    bfloat16   83.9  77.8  71.8   run1
unsloth/Meta-Llama-3.1-8B                    float32    81.6  73.2  65.1   run1
Qwen/Qwen3.5-9B-Base                         float32    80.0  82.1  65.5   run1
Qwen/Qwen3.5-4B-Base                         float32    78.6  84.1  63.4   run1
Qwen/Qwen3.5-2B-Base                         float32    77.1  78.7  66.1   run1
Qwen/Qwen3.5-0.8B-Base                       float32    66.3  62.8  55.8   run1
Qwen/Qwen2.5-1.5B                            float32    55.0  53.1  49.7   run1

Notes
- unsloth/Meta-Llama-3.1-8B is an ungated public copy of meta-llama/Llama-3.1-8B (same 8,030,261,248 parameters).
- Qwen/Qwen3.5-27B, Qwen/Qwen3.6-27B, Qwen/Qwen3.6-35B-A3B, Qwen/Qwen3.8-27B are post-trained models (no Base
  checkpoint published). tomaris/Tomaris.ai is a fine-tune in the Qwen3.5 architecture; neither it nor Qwen3.5-27B is a pure base model.
- Per-phenomenon accuracy is inside each results/json file; per-pair scores are in results/pairs.
