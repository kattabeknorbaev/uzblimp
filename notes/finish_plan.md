# Finish plan: from v0.2 to the preprint (drafted 2026-10-22)

Goal: **arXiv preprint ~15 December 2026**, then the **January 2027 ACL Rolling Review cycle** (deadline likely ~4 Jan 2027, not yet official; `notes/venues.md`). Owners: KN = Kattabek, JM = Javokhir, C = Claude, RS = Russell (roles not yet agreed).

## Where we are (22 Oct)
- Benchmark v0.2: 8/16 phenomena, 1,200 pairs; all three alphabets scored with 4 models (`results/eval_v0.2.md`).
- Remaining 8 phenomena: JM's v11 pairs (`data/pairs_v2_*`, 1,687) unreviewed. Top-up generators written for the four likely to fall short of 150 (ditransitive_dative, passives, relative_clauses, quantifiers; forecast from JM's acceptance rates).
- Second annotator: JM's 562-pair sheet done; agreement computed once KN has reviewed those pairs.
- Grammar prompting (decision 19): design, code and 8 explanations ready; models and compute not chosen.

## Plan
| Dates | Task | Owner | Critical? |
|---|---|---|---|
| 22 Oct – 1 Nov | Review the 8 v2 phenomena (~1,700 pairs incl. top-ups; ~170/day) | KN | **yes** (everything waits on it) |
| by 1 Nov | Decide compute: Kaggle account + Llama 3.1 licence on HF; frontier model via API with a budget (or RS's lab credits) | KN | yes |
| by 1 Nov | Agree with RS: his role/credit, the human study design and ethics route | KN, RS | yes for the human baseline |
| 2–4 Nov | Agreement KN–JM (`agreement.py`), settle disagreements together; build **v1.0** (16 × 150 = 2,400); convert to Cyrillic/reformed; native check of 80 new Cyrillic samples | C, KN, JM | yes |
| 4–6 Nov | Rescore the 4 current models on v1.0 in 3 alphabets (CPU, ~5 h, plugged in) | C | |
| 6–13 Nov | Mid-size instruction-tuned models (Llama-3.1-8B-Instruct + Uzbek-tuned versions, Qwen2.5-7B-Instruct) on Kaggle; frontier model via API; 3 alphabets | C (+KN runs notebook) | yes |
| 13–20 Nov | Grammar prompting: baseline / explanation / control on the models that pass the baseline check; explanations for the 8 new phenomena (C drafts, KN checks) | C, KN | |
| 13–20 Nov | Contamination: seen/unseen split by source (our corpus vs uz-books) and Tomaris overlap | C | |
| 15 Nov – 10 Dec | Human baseline (~30 native speakers): build the survey, recruit, collect | KN, RS | risky; if late, report as in progress in the preprint and complete for ARR |
| 5 Nov – 1 Dec | Paper draft (ACL template, Overleaf): data/method sections while models run, results from 20 Nov | C drafts, KN owns | yes |
| 1–8 Dec | Feedback round (RS; others who offered) | KN | |
| 1–12 Dec | Release prep: licence audit (books' terms unknown; Wikipedia CC BY-SA; uz-books MIT), dataset card, public GitHub + Hugging Face | C, KN | yes before release |
| ~15 Dec | arXiv preprint. **First-time arXiv submitters usually need an endorsement for cs.CL**: ask an established author early (e.g. RS, if eligible) | KN | yes |
| ~4 Jan 2027 | ARR submission (check the official date; anonymised version) | KN | |

## Risks and fallbacks
- **Review throughput** is the bottleneck. Fallback: freeze v1.0 with the phenomena that reached 150 and report the rest as an extra set.
- **Compute/API not decided by early November** → the paper has only small models. Fallback: Kaggle free GPUs for open models, and the frontier model only on a subset.
- **Human study needs ethics approval and participants**; may not finish by mid-December.
- **Licence of book sentences** may block releasing some pairs; every pair keeps its `source_id`, so those can be replaced from reserve or other sources.
- **AI assistance** in code, explanations and writing should be disclosed (the ARR Responsible NLP checklist asks about AI assistants; check the current ACL policy wording). Authors stay responsible for everything in the paper.
