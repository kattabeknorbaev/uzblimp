# Archive

Everything that is not needed to use the benchmark, evaluate a model or rebuild the paper, kept with its git
history. The version history is in [`CHANGELOG.md`](CHANGELOG.md).

| Path | Contents |
|---|---|
| `log.md` | research log: date, task, result, next step |
| `notes/` | design decisions, phenomena, corpus provenance, reading notes |
| `handcheck/` | review and spot-check sheets of the native speakers |
| `human_study/` | sheets, answer keys and instructions of the human validation, and the planned rating study |
| `data/` | candidate pairs with review decisions (`pairs_v*.tsv`, format in `data/README.md`), Javohir Matniyozov's generated pair sets (`external/`), the Uzbek split of MultiBLiMP 1.0, pilot and test pairs, grammar explanations |
| `results/` | results of the benchmark versions before v1.2, pilots, the run log (`summary.csv`), version reports, corpus and overlap statistics |
| `scripts/` | generators, converters, validators, review tools and one-off checks |
| `paper/` | the earlier paper README with the submission checklist, the ARR checklist draft, outreach drafts |
| `eval_models.txt` | an example model list for `scripts/eval.py --models-file` |

The files are kept as they were, so their text uses the old paths:

| Old path | Now |
|---|---|
| `scripts/<name>` (other than the kept scripts) | `archive/scripts/<name>` |
| `data/pairs_v*.tsv`, `human_study/` | `archive/data/`, `archive/human_study/` |
| `results/<model>_uzblimp_v1.2[_cyrl\|_reformed].csv` | `results/lm/<alphabet>/<model>.csv` |
| `results/json/`, `results/gpu_runs/` | `results/lm/json/`, `results/lm/gpu_runs/` |
| `results/claude_fc/`, `results/codex_fc/`, `results/api_fc/` | `results/chat/claude/`, `results/chat/codex/`, `results/chat/openrouter/` |

The archived scripts are not maintained and expect the old layout.

`scripts/paper_tables.py` still reads four archived inputs: `data/pairs_v[12]_*.tsv` (counts of the review and
reasons for rejection), `results/uzn_latn_100mb_uzblimp_v1.1.csv` (pairs replaced since v1.1),
`results/api_*_pilot3.csv` (the chat-model pilot of Table 17) and `human_study/ratings_key.csv` (size of the
planned rating study). `scripts/human_study_report.py` reads the answer keys in `human_study/` and the individual
answer sheets in `human_study/responses/`, which are private and not in the repository.

The data here is under the licence of `data/` (CC BY-SA 4.0, [`../data/LICENSE`](../data/LICENSE)), except
`data/multiblimp_uzb.tsv`, which is MultiBLiMP 1.0 under its own licence; the code is under MIT ([`../LICENSE`](../LICENSE)).
