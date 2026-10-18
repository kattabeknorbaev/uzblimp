# Grammar prompting on UzBLiMP (decision 19, design draft 2026-10-18)

Idea from Russell Scheinberg (Google Doc "Two ideas for UzBLiMP paper", Idea 1), building on
Scheinberg et al., *Explain-then-Process* (ACL Findings 2025). Status: design only; no results yet.

## Question
A short explanation of the phenomenon raised accuracy on English, Chinese and Russian minimal
pairs, and an unrelated explanation didn't. Two readings fit that result:
1. **Rule-following:** the model reads the rule and applies it.
2. **Cueing:** the model already learned the pattern from data; the explanation only reminds it.

In a high-resource language both predict a gain. Where the learned pattern is weak, cueing
predicts a small gain and rule-following a large one, so the size of the gain on UzBLiMP is
evidence either way.

## Conditions (per pair)
| Condition | What goes in front of the pair |
|---|---|
| baseline | nothing |
| explanation | the explanation of the pair's own phenomenon |
| control | the explanation of an unrelated phenomenon (`control_phenomenon` in `data/explanations.tsv`; each phenomenon is used as a control exactly once) |

Key comparison: **explanation − control** (the content effect), with McNemar on the same pairs;
**control − baseline** shows the effect of just having text in front.

## Explanations (Kattabek writes them)
`data/explanations.tsv`, column `explanation`. The `tests` column is only a reminder of what
the pairs change; the explanations must be in Kattabek's own words (native-written is what makes
this cleaner than model-written explanations).
- English, 2–4 sentences, roughly the same length for every phenomenon (the control is another
  phenomenon's explanation, so similar lengths keep the two conditions comparable).
- State the rule. One correct and one incorrect Uzbek example are fine, but **not** sentences or
  word forms from the benchmark or reserve (a check script is still to write).
- Don't mention the task, the answer options or which sentence is right.
- `explanation_uz` (optional): the same in Uzbek, for a later explanation-language comparison.

## Scoring
- **A. Log-probability** (any open causal LM; implemented): `score_pairs.py --explanations
  data/explanations.tsv --condition explanation|control` scores log P(sentence | explanation + "\n").
  Checked on Qwen2.5-0.5B against a manual computation (agrees to 0.002). Masked LMs aren't
  supported (minicons' MLM `conditional_score` ignores the PLL variant used for the baseline).
- **B. Forced choice** (instruction-tuned and frontier models; not built yet): show both
  sentences, ask which is grammatical, each pair in both orders to remove position bias.
  Build once the models are chosen; match Russell's prompt format where possible.

## Models: baseline check first
The premise needs models that know some Uzbek but not much. Our current models don't qualify:
Uzbek-only models are at ceiling (Goldfish 94.8% on v0.2, tahrirchi-bert 97.7% on v0.1) and
can't follow instructions; Qwen2.5-0.5B is below chance (45.8% on v0.2), so it may not be
attempting the task. Plan:
1. Baselines (A and B) for 3–4 open instruction-tuned models in the 7–9B range and one frontier
   model. None chosen yet. Candidates found 2026-10-18 (model-card claims, not verified):
   - `meta-llama/Llama-3.1-8B-Instruct` (general; gated, the licence must be accepted on HF) and its
     Uzbek-tuned versions `behbudiy/Llama-3.1-8B-Instuct-Uz` (sic, repo name) and
     `uzlm/alloma-8B-Instruct` (custom Uzbek tokenizer). Same architecture with a weak vs a strong
     Uzbek pattern: a within-architecture version of the cueing test.
   - `Qwen/Qwen2.5-7B-Instruct`; a Gemma model (Gemma 3 claims 140+ languages; Uzbek not confirmed).
   - Related work to cite: UzLiB (tahrirchi, github.com/tahrirchi/uzlib), multiple-choice questions
     on Uzbek linguistic knowledge.
2. Keep models that are clearly above chance and clearly below ceiling (working criterion,
   to agree with Russell).
3. Then the three conditions on the full benchmark.

**Script variant:** tahrirchi-bert drops from 97.7% (Latin) to 70.3% (Cyrillic) on the same
pairs. If an instruction-tuned model shows a similar script gap, running the conditions in both
scripts compares a strong and a weak learned pattern inside one model.

## Compute
7–9B models need a GPU with ~16–24 GB (the laptop's RTX 3050 has 4 GB and the installed PyTorch
is CPU-only). Options: Tomaris GPUs (Javokhir, decision 13) or a cloud GPU. The frontier model
needs an API key and a small budget. Scoring is cheap: 1,200 pairs × 2 sentences × 3 conditions.

## Open questions
- **For Russell:** his prompt formats and how small models were scored in *Explain-then-Process*;
  explanation language (English vs Uzbek); his and So Young Lee's roles and credit.
- **For Kattabek:** GPU source, frontier model and budget.
