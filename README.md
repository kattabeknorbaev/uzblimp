---
pretty_name: UzBLiMP
language:
- uz
license: cc-by-sa-4.0
task_categories:
- text-classification
task_ids:
- acceptability-classification
size_categories:
- 1K<n<10K
tags:
- minimal-pairs
- linguistic-acceptability
- benchmark
- uzbek
configs:
- config_name: latn
  default: true
  data_files:
  - split: test
    path: data/jsonl/latn/*.jsonl
- config_name: cyrl
  data_files:
  - split: test
    path: data/jsonl/cyrl/*.jsonl
- config_name: latn_reformed
  data_files:
  - split: test
    path: data/jsonl/latn_reformed/*.jsonl
---

# UzBLiMP

**Status, v1.2:** 2,400 pairs across 16 phenomena, in three alphabets; every pair was reviewed by a native speaker and checked with three other native speakers; in a forced-choice validation of 320 pairs, five further native speakers chose the grammatical sentence in 99.2% of 1,600 judgments and their majority agreed with the benchmark on every pair ([`results/human_study.md`](results/human_study.md)); acceptability ratings not yet collected; 31 models evaluated, 17 on CPU and 14 larger ones (up to 36 billion parameters) on GPUs, plus Tomaris.ai, which is not held out; evaluation harness and paper ([`paper/uzblimp.pdf`](paper/uzblimp.pdf)) included. v1.2 replaces 120 pairs (5.0%) found faulty in an audit of the selected pairs (generator errors, spelling and OCR errors) and corrects the Cyrillic spelling of Russian loanwords (72 word forms).

UzBLiMP is a benchmark of linguistic minimal pairs for Uzbek. Each pair is two sentences that differ in one word: one grammatical, one not. The grammatical sentence is a sentence found in a corpus; the ungrammatical one changes it with one controlled edit. A language model passes a pair if it gives the grammatical sentence the higher probability, or picks it when asked.

**Research question:** does a model's knowledge of Uzbek grammar hold up across Uzbek's three alphabets: Cyrillic, current Latin, and the reformed Latin of Law OʻRQ-1184 (approved by the Senate on 10 September 2026, signed on 21 October 2026, in force from 22 April 2027; oʻ→ö, gʻ→ğ, sh→ş, ch→ç)?

Related work: TurBLiMP (Turkish, EMNLP 2025), TatBLiMP (Tatar, arXiv 2026), MultiBLiMP 1.0 (101 languages, agreement only, includes Uzbek; TACL 2026).

## Phenomena

150 pairs each. Twelve phenomena share their category with TurBLiMP; the last four in the table lie outside its inventory.

| Paradigm | Phenomenon | Field | What the grammatical sentence gets right |
|---|---|---|---|
| `anaphor_agreement` | Anaphor agreement | morphology | reflexive oʻz- agrees with the subject in person/number |
| `binding` | Binding | syntax | reflexive, not a pronoun, inside its binding domain |
| `ditransitive_dative` | Ditransitive dative | syntax | indirect object takes dative, not a second accusative |
| `lexical_case` | Lexical case | syntax | verb assigns a lexical case to its object (qoʻrqmoq + ablative) |
| `nominalization` | Nominalization | syntax | predicates such as kerak, mumkin, lozim take the verbal noun in -(i)sh, not the participle -gan |
| `npi_hech` | NPI licensing (hech + negation) | semantics | hech- words need a negated predicate |
| `passives` | Passives | syntax | an agent phrase (tomonidan) needs a passive verb |
| `person_agreement` | Subject agreement | morphology | verb agrees in person and number with an overt pronoun subject |
| `quantifiers` | Quantifiers (har bir + singular) | morphology | noun after har bir stays singular |
| `relative_clauses` | Relative clauses | syntax | a relative clause verb is a participle (-gan), not a finite verb |
| `stem_alternation` | Stem alternation (q/k → gʻ/g) | morphology | stem-final q/k becomes gʻ/g before a vowel-initial suffix |
| `suspended_affixation` | Suspended affixation | morphology | first conjunct keeps its finite person/tense suffix |
| `numeral_no_plural` | No plural after numerals | morphology | noun after a numeral (+ta) stays singular |
| `postposition_case` | Case after postpositions | syntax | postposition governs a fixed case (-dan keyin, -dan beri) |
| `possessive_agreement` | Possessive agreement | morphology | possessive suffix agrees with the genitive possessor |
| `dative_allomorphy` | Dative allomorphy (-ga/-qa/-ka) | morphology | dative is -qa after q, -ka after k, -ga elsewhere |

The field follows BLiMP where BLiMP has the same contrast (agreement and irregular forms: morphology; argument structure: syntax; NPI licensing: semantics); the other assignments are ours.

## Alphabets

| Config | Alphabet | How it was made |
|---|---|---|
| `latn` | current Latin | the reviewed pairs |
| `cyrl` | Cyrillic | converted from `latn` with TurkicNLP's transliterator, fixes for errors found in it, and a table of the Russian loanwords in the benchmark (функция, концерт, пальто …) |
| `latn_reformed` | reformed Latin (2026) | converted from `latn` with the four main rules of the reform; `reform_category` says whether the edited word itself changed |

The same `pair_id` names the same pair in all three.

## Data format

`data/jsonl/<config>/<paradigm>.jsonl`, one pair per line:

| Field | Meaning |
|---|---|
| `pair_id` | e.g. `stem_alternation-1042`, the same in all alphabets |
| `paradigm` | phenomenon slug (one paradigm per phenomenon) |
| `phenomenon` | readable name |
| `field` | `morphology`, `syntax` or `semantics` |
| `sentence_good`, `sentence_bad` | the pair |
| `lexically_identical` | true when both sentences use the same words (false for every pair: each changes one word form) |
| `script` | `latn`, `cyrl` or `latn_reformed` |
| `source` | how the pair was made: `corpus-edit` for every pair (the format also allows `template` and `hand-written`) |
| `source_id` | where the grammatical sentence comes from |
| `verified`, `verifier_id` | checked by a linguist, and by whom: false and null for every pair so far |
| `reviewer` | native speaker who reviewed the pair (`KN`: Kattabek Norbaev) |
| `converted_from` | `cyrl` and `latn_reformed` only: `latn` |
| `reform_category` | `latn_reformed` only: critical word changed, only other words changed, or unchanged |

```json
{"pair_id": "stem_alternation-1042", "paradigm": "stem_alternation", "phenomenon": "Stem alternation (q/k → gʻ/g)", "field": "morphology", "sentence_good": "Saodatning gapini uch yil oldin eshitganimda, ishonmasam ham, yuragim hapriqar edi.", "sentence_bad": "Saodatning gapini uch yil oldin eshitganimda, ishonmasam ham, yurakim hapriqar edi.", "lexically_identical": false, "script": "latn", "source": "corpus-edit", "source_id": "books/Ahmad A’zam. Аҳмад Аъзам. Тугмачагул (новелла).txt:105:15", "verified": false, "verifier_id": null, "reviewer": "KN"}
```

The TSVs in `data/benchmark/` are the source: `python scripts/export_jsonl.py` rewrites `data/jsonl/` from them and `python scripts/validate.py` checks the result (format, duplicates, identical sentences, one changed place per pair, sentences at most a few characters apart, apostrophes).

**Apostrophes.** In current Latin, oʻ and gʻ are always written with U+02BB (ʻ). The glottal-stop sign (*tutuq belgisi*, as in *maʼno*) is a different letter, U+02BC (ʼ), and stays as it is. `export_jsonl.py` turns any other apostrophe after o or g (', ’, ‘, \`, ʼ, ´) into U+02BB, and `validate.py` rejects it: mixed apostrophes make a tokenizer split the same word in different ways, and a model would be scored on spelling instead of grammar.

## Evaluating a model

```bash
pip install -r requirements.txt
python scripts/validate.py
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn
python scripts/run_models.py --only "GF-L 100MB"          # the paper's scorer, for a model listed in scripts/models.py
python scripts/eval.py --method forced-choice --model google/gemma-3-12b-it --script cyrl --per-phenomenon 3
python scripts/make_table.py
```

- **logprob** (Hugging Face causal LMs): each sentence's total log-probability, summed over its tokens, scored the same way as `scripts/score_pairs.py`. Weights load in float32 by default; `--dtype auto` (bfloat16 or float16 on a GPU) is faster but too coarse for close pairs.
- **forced-choice** (chat models without log-probabilities, through OpenRouter): each pair is shown in both orders and the model answers 1 or 2. Accuracy counts both orders, so always answering "1" scores 50%. The API key is read from `OPENROUTER_API_KEY` or `.env`, and requests ask for providers that don't collect data.
- Masked LMs such as tahrirchi-bert are scored by pseudo-log-likelihood with `scripts/score_pairs.py --mlm`. With `--fast-pll` the same quantity is computed by the batched scorer in `scripts/pll.py` (equal to minicons' scores to within about 3e-4 nats, `python scripts/pll.py --selftest`); `run_models.py` uses it.

`eval.py` writes `results/json/<model>__<config>__<method>.json` and the per-pair scores to `results/pairs/`; `make_table.py` rebuilds the table below and `results/per_phenomenon.md`. Models to run go in `eval_models.txt` (`--models-file eval_models.txt`).

## Results (v1.2)

Accuracy (%) on all 2,400 pairs. **logprob**: causal LM log-probability; **pll**: masked-LM pseudo-log-likelihood; **forced-choice**: chat model picks the sentence. GF-L / GF-C are the Goldfish models trained on Latin-script / Cyrillic-script Uzbek. Only models with no unknown tokens on the new letters are run on reformed Latin (`notes/decisions.md`, decision 8), and not models trained on Cyrillic only. Per phenomenon: [`results/per_phenomenon.md`](results/per_phenomenon.md); what changed since v1.1: [`results/eval_v1.2.md`](results/eval_v1.2.md).

In short: the strongest monolingual models (TahrirchiBERT and the Goldfish models trained on 100 MB or more) score about 95–99% in the script they were trained on, Latin or Cyrillic alike, and every model trained on one script loses 5 to 48 points when the same sentences are written in the other script; there, and on the reformed spelling, their choices follow token counts and familiar spellings instead of grammar. UzRoBERTa, trained on both scripts, scores 93–96% on both. Small multilingual models know much less of this grammar (XLM-R 78% on Latin, 51% on Cyrillic), but the larger ones, scored on GPUs (`results/gpu_runs/`), know most of it in both scripts (Gemma 4 31B: 97.3% Latin, 98.1% Cyrillic) and still lose 7–17 points on reformed Latin. Tomaris.ai is the model of the authors' company; its pretraining corpus contains 99% of the grammatical sentences from our own corpus, so its scores are not held out (paper, Appendix H).

<!-- results:start -->
| Model | Method | Current Latin | Cyrillic | Reformed Latin |
|---|---|---:|---:|---:|
| GF-L 5MB (`goldfish-models/uzn_latn_5mb`) | logprob | 63.3 | 53.3 | — |
| GF-L 10MB (`goldfish-models/uzn_latn_10mb`) | logprob | 73.4 | 55.8 | — |
| GF-L 100MB (`goldfish-models/uzn_latn_100mb`) | logprob | 95.8 | 88.3 | — |
| GF-L full (`goldfish-models/uzn_latn_full`) | logprob | 96.7 | 91.7 | — |
| GF-C 5MB (`goldfish-models/uzn_cyrl_5mb`) | logprob | 45.2 | 61.3 | — |
| GF-C 10MB (`goldfish-models/uzn_cyrl_10mb`) | logprob | 40.3 | 65.4 | — |
| GF-C 100MB (`goldfish-models/uzn_cyrl_100mb`) | logprob | 47.6 | 94.7 | — |
| GF-C full (`goldfish-models/uzn_cyrl_full`) | logprob | 49.5 | 97.3 | — |
| tahrirchi-bert (`tahrirchi/tahrirchi-bert-base`) | pll | 98.7 | 76.8 | 87.3 |
| tahrirchi-bert-small (`tahrirchi/tahrirchi-bert-small`) | pll | 92.2 | 59.2 | 81.3 |
| BERTbek (`elmurod1202/bertbek-news-big-cased`) | pll | 87.6 | 59.4 | 68.2 |
| UzBERT (`coppercitylabs/uzbert-base-uncased`) | pll | 42.7 | 84.3 | — |
| UzRoBERTa (`rifkat/uztext-3Gb-BPE-Roberta`) | pll | 93.4 | 96.4 | 78.0 |
| mBERT (`google-bert/bert-base-multilingual-cased`) | pll | 62.5 | 51.2 | 55.6 |
| XLM-R base (`FacebookAI/xlm-roberta-base`) | pll | 78.2 | 51.3 | 71.5 |
| Qwen2.5-0.5B (`Qwen/Qwen2.5-0.5B`) | logprob | 50.4 | 46.2 | 46.8 |
| Qwen2.5-1.5B (`Qwen/Qwen2.5-1.5B`) | logprob | 55.0 | 53.1 | 49.7 |
| Qwen3.5-0.8B (`Qwen/Qwen3.5-0.8B-Base`) | logprob | 66.3 | 62.8 | 55.8 |
| Qwen3.5-2B (`Qwen/Qwen3.5-2B-Base`) | logprob | 77.1 | 78.7 | 66.1 |
| Qwen3.5-4B (`Qwen/Qwen3.5-4B-Base`) | logprob | 78.6 | 84.1 | 63.4 |
| Qwen3.5-9B (`Qwen/Qwen3.5-9B-Base`) | logprob | 80.0 | 82.1 | 65.5 |
| Gemma 4 E4B (`google/gemma-4-E4B`) | logprob | 91.9 | 95.9 | 78.3 |
| Llama 3.1 8B (`unsloth/Meta-Llama-3.1-8B`) | logprob | 81.6 | 73.2 | 65.1 |
| Mistral Small 3.1 (`mistralai/Mistral-Small-3.1-24B-Base-2503`) | logprob | 83.9 | 77.8 | 71.8 |
| Gemma 4 26B-A4B (`google/gemma-4-26B-A4B`) | logprob | 94.8 | 97.5 | 86.2 |
| Gemma 4 31B (`google/gemma-4-31B`) | logprob | 97.3 | 98.1 | 90.5 |
| Qwen3.5-27B (`Qwen/Qwen3.5-27B`) | logprob | 92.3 | 95.1 | 82.2 |
| Qwen3.6-27B (`Qwen/Qwen3.6-27B`) | logprob | 93.3 | 93.8 | 83.3 |
| Qwen3.8-27B (`Qwen/Qwen3.8-27B`) | logprob | 92.9 | 94.4 | 81.0 |
| Qwen3.5-35B-A3B (`Qwen/Qwen3.5-35B-A3B-Base`) | logprob | 92.5 | 95.6 | 80.7 |
| Qwen3.6-35B-A3B (`Qwen/Qwen3.6-35B-A3B`) | logprob | 91.0 | 91.6 | 78.5 |
| Tomaris.ai (not held out) (`tomaris/Tomaris.ai`) | logprob | 98.7 | 92.6 | 92.8 |
<!-- results:end -->

## How the pairs were made and checked

- **Sources.** 960 pairs come from Javohir Matniyozov's rule-based pairs over `tahrirchi/uz-books-v2` (`data/external/`, generator in `scripts/jm_generator/`) and 1,440 from Kattabek Norbaev's generator (`scripts/make_pairs.py`) over books (934), Uzbek Wikipedia (496) and legal codes (10).
- **Review.** Of 3,800 candidate pairs, 3,729 were reviewed and 3,267 (87.6%) accepted. Every pair was judged first by Kattabek Norbaev, a native speaker, and then checked with three other native speakers; for some phenomena an AI assistant was used as a consistency check. Rejected pairs keep their reason in `data/pairs_v*.tsv`.
- **Audit of the selected pairs (v1.2).** The 2,400 selected pairs were screened in two passes with the help of an AI assistant: for generator errors (ungrammatical members that have a grammatical reading, edited words that are not an instance of the phenomenon, malformed forms) and for spelling or OCR errors in the source sentences (found by reading the 1,000 most surprising words under the largest Latin Goldfish model and by proofreading every grammatical sentence once more). 120 pairs (5.0%) were replaced by the next accepted pairs of their phenomenon, and the replacements were checked in the same way. Every excluded pair is listed with its reason in `data/benchmark/excluded.tsv` (143 pairs, including reserve pairs); the first author confirmed them on 22 November 2026. Known weaknesses that were kept are described in the paper (Appendix A).
- **Cyrillic audit (v1.2).** The roughly 10,000 distinct word forms of the Cyrillic version were checked three times for Russian loanwords that Latin spells differently; 72 forms are respelled from a table (`scripts/alphabets.py`). Loanwords that were not recognised may remain. A native-speaker spot check of ten pairs per phenomenon (`handcheck/cyrillic_check_60.csv`, `handcheck/cyrillic_check_v1.2_remaining.csv`) found no conversion errors other than in Russian loanwords.
- **Human validation (November 2026).** Following BLiMP, five native speakers who had not worked on the benchmark, one of them a linguist, chose the grammatical sentence of 320 pairs (20 per phenomenon, shown as A and B in random order). 99.2% of the 1,600 judgments agree with the benchmark (individual annotators 97.8–100%), the majority agrees on all 320 pairs, mean pairwise agreement is 98.4% and Krippendorff's α 0.97. No pair was misjudged by more than one annotator; the 13 pairs misjudged by one were reread and are correct. On the same pairs TahrirchiBERT scores 98.4% and the largest Goldfish models 98.8% (Latin) and 98.1% (Cyrillic). Report: [`results/human_study.md`](results/human_study.md); materials and released counts: [`human_study/`](human_study/README.md) (the individual answer sheets stay private, as the consent text promised).
- **Not done yet.** No linguist has checked the full benchmark (`verified` is false everywhere); the Cyrillic and reformed versions are not validated separately; there are no acceptability ratings yet (sheets in [`human_study/`](human_study/README.md)). The comparison in `results/agreement_KN_JM.md` doesn't count as inter-annotator agreement, because the two sets of judgments weren't made independently (`notes/decisions.md`, decision 20).
- **Selection.** 150 accepted pairs per phenomenon, chosen at random with a fixed seed; 724 further accepted pairs (`data/benchmark/reserve.tsv`) can replace pairs that fail a later check.

## Repository layout

| Path | Contents |
|---|---|
| `data/jsonl/` | release files (above) |
| `data/benchmark/` | the benchmark TSVs, source of `data/jsonl/`, and the reserve |
| `data/pairs_v*.tsv` | candidate pairs with review decisions |
| `data/external/` | Javohir Matniyozov's generated pairs (v11, v12) |
| `data/multiblimp_uzb.tsv` | MultiBLiMP 1.0, Uzbek split (50 pairs), for comparison |
| `handcheck/` | review sheets |
| `human_study/` | sheets, instructions and keys of the human validation; released counts of the forced-choice study (individual sheets are private) |
| `scripts/` | generators, validators, scoring and tables: `models.py` lists the evaluated models, `run_models.py` scores them, `paper_tables.py` and `paper_figures.py` build every table, number and figure of the paper |
| `results/` | per-pair scores, `results/json/` summaries, `per_phenomenon.md` |
| `notes/` | design decisions, phenomena table, reading notes |
| `paper/` | paper (ACL format): `main.tex`, generated `tables/` and `figures/`, compiled `uzblimp.pdf` |
| `log.md` | research log: date – task – result – next step |

## Limitations

- **Converted alphabets.** The Cyrillic and reformed versions are converted from Latin, not written natively. Russian loanwords can't all be recovered by rule: those found in the benchmark are corrected from a table, and suffixed forms of loans ending in ь (медални, моделлари) are left as converted. The 2026 law gives an alphabet and no spelling rules, so only its four letter replacements are applied.
- **Review.** Judgments come from one native speaker, checked with three others. The independent validation covers 320 pairs (13%) as forced choice, without acceptability ratings, and the answer key of that sample was in this public repository while the study ran.
- **Models.** We scored models of up to 1.5 billion parameters on a CPU. The 14 larger ones were scored on rented GPUs for the second author with the same scorer, partly in bfloat16 and four of them post-trained checkpoints; we re-scored samples of the two smallest on CPU (`results/gpu_runs/CHECKS.md`). Chat models are covered only by a 48-pair pilot.
- **Size.** With 150 pairs, the 95% interval of a per-phenomenon accuracy is at most ±8 points.

## License

**Data** (`data/`): CC BY-SA 4.0 ([`data/LICENSE`](data/LICENSE)), except `data/multiblimp_uzb.tsv` (MultiBLiMP 1.0, under its own licence). Some sentences come from Uzbek Wikipedia (CC BY-SA), so the pairs keep its share-alike terms. Other sentences are short excerpts from published books, from copies publicly available on the internet; each pair's `source_id` names its source, and we remove any sentence on request (open an issue). **Code** (`scripts/`): MIT ([`LICENSE`](LICENSE)).

## Citation

The paper is [`paper/uzblimp.pdf`](paper/uzblimp.pdf) (preprint). Until it has an arXiv or ACL Anthology entry, please cite (also in [`CITATION.cff`](CITATION.cff)):

```bibtex
@misc{uzblimp2026,
  title  = {{UzBLiMP}: A Benchmark of Linguistic Minimal Pairs for {U}zbek in Three Alphabets},
  author = {Norbaev, Kattabek and Matniyozov, Javohir},
  year   = {2026},
  note   = {Version 1.2},
  url    = {https://github.com/kattabeknorbaev/uzblimp}
}
```

## Contributors

| Person | Role |
|---|---|
| Kattabek Norbaev | Project lead: phenomena and design, corpus pair generator, native-speaker review of every pair, evaluation, paper draft |
| Javohir Matniyozov | Rule-based pair generator and its 4,500 pairs (960 in the benchmark), second annotator sheet |
| Three native speakers | Checked the reviewed pairs (not named) |

AI assistants (Claude) helped write code, import review decisions, run the model evaluation, audit the Cyrillic conversion and draft the paper, its glosses and the grammar explanations prepared for a later experiment; the authors check the results. The paper's AI-assistance statement gives the details.
