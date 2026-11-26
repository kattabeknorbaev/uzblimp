UzBLiMP v1.2, GPU run 3: twelve more open models
Date: 2026-11-26 (Asia/Tashkent). Run by Grok Bot (an AI agent) for Javohir Matniyozov.

GPU: 1x RTX PRO 6000 Blackwell Workstation 96GB (Vast.ai instance 62652727, Taiwan), rented 12:05-13:31
(UTC+5). torch 2.11.0+cu128, transformers 5.24.0. Data: data/benchmark at repo commit 7733532.

Causal LMs (8): scripts/run_big.py, i.e. scripts/eval.py logprob with the same local loading patch as runs 1-2
(scripts/eval.py.local_patch.diff): weights loaded straight onto the GPU, image-text-to-text class for the
Gemma 3 checkpoints, text input only. Models up to 10B in float32, Gemma 3 12B and 27B in bfloat16.
Per-pair files: run3_RTXPRO6000/results/pairs -> results/<model>_uzblimp_v1.2*.csv (scripts/import_gpu_runs.py).
The first Gemma 3 27B attempt stopped when the disk was full during the download; the retry ran to the end
(logs/run3_RTXPRO6000/google_gemma-3-27b-pt_bfloat16_retry.log).

Registry models of the CPU groups (4): mGPT, mGPT-Uzbek, Glot500, XLM-R large were scored with
scripts/run_models.py (score_pairs.py, float32; --mlm --fast-pll for the masked LMs) on the GPU instead of the
CPU (the run used a local switch, UZB_DEVICE=cuda; the committed script has --device cuda for the same
change). Their result files were copied into results/ as written; logs/run3_RTXPRO6000/small.log.

Accuracy (%), L = current Latin, C = Cyrillic, R = reformed 2026 Latin; 2,400 pairs each
model (HF id)                           dtype       L     C     R
google/gemma-3-27b-pt                   bfloat16  94.1  97.7  84.5
google/gemma-3-12b-pt                   bfloat16  92.9  96.0  79.5
uzlm/alloma-8B-Base                     float32   92.5  n/a   74.8
ai-forever/mGPT                         float32   91.2  95.6  77.3
ai-forever/mGPT-1.3B-uzbek              float32   91.2  61.0  75.7
issai/Qwen3.5-9B-Base-Kazakh            float32   90.5  88.0  76.8
behbudiy/Llama-3.1-8B-Instruct-Uz       float32   89.2  73.8  71.2
google/gemma-3-4b-pt                    float32   86.9  91.5  70.1
FacebookAI/xlm-roberta-large            float32   84.0  52.8  74.5
cis-lmu/glot500-base                    float32   79.4  93.7  77.6
NeuronUz/NeuronAI-Uzbek                 float32   78.1  81.0  67.5
CohereLabs/aya-expanse-8b               float32   54.0  55.1  54.3

Not reported: alloma-8B-Base on Cyrillic. Its tokenizer drops Cyrillic letters (e.g. a Cyrillic sentence
encodes to the spaces and the full stop only), so 2,297 of the 2,400 Cyrillic pairs tie; the per-pair file
is kept in results/gpu_runs/invalid/.

Checks
- Reproduction: Qwen3.5-0.8B-Base scored again in this run (results/gpu_runs/repro/) gives 66.2 / 62.8 / 55.8
  against 66.3 / 62.8 / 55.8 in run 1; 7,198 of the 7,200 judgments agree, log-probabilities within 0.1 nats.
- Precision: Aya Expanse 8B in bfloat16 on current Latin (results/gpu_runs/bf16check/) gives 54.3 against
  54.0 in float32.
- Aya Expanse 8B is near chance in all three alphabets, with some phenomena far below chance (binding 8.0% on
  Latin); this was not explained further.

Notes
- Post-trained checkpoints: Aya Expanse 8B, Llama-3.1-8B-Instruct-Uz, NeuronAI-Uzbek (fine-tuned from Qwen3-4B)
  and alloma-8B-Base (fine-tuned from Llama-3.1-8B-Instruct, per its model card despite its name). They are scored
  without a chat template, like the others. Gemma 3 checkpoints are the -pt ones; Qwen3.5-9B-Base-Kazakh is
  continued pretraining of Qwen3.5-9B-Base.
