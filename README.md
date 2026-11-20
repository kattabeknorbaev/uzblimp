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

**Status, v1.1:** 2,400 of 2,400 pairs across 16 phenomena, in three alphabets; 0 verified by linguists (every pair was reviewed by a native speaker and checked with three other native speakers; review by linguists is planned); evaluation harness included.

UzBLiMP is a benchmark of linguistic minimal pairs for Uzbek. Each pair is two sentences that differ in one word: one grammatical, one not. The grammatical sentence is a sentence found in a corpus; the ungrammatical one changes it with one controlled edit. A language model passes a pair if it gives the grammatical sentence the higher probability, or picks it when asked.

**Research question:** does a model's knowledge of Uzbek grammar hold up across Uzbek's three alphabets: Cyrillic, current Latin, and the reformed Latin approved on 10 September 2026 (oʻ→ö, gʻ→ğ, sh→ş, ch→ç)?

Related work: TurBLiMP (Turkish, EMNLP 2025), TatBLiMP (Tatar, 2026), MultiBLiMP 1.0 (101 languages, agreement only, includes Uzbek).

## Phenomena

150 pairs each. Twelve phenomena follow the TurBLiMP inventory; the last four in the table are specific to Uzbek.

| Paradigm | Phenomenon | Field | What the grammatical sentence gets right |
|---|---|---|---|
| `anaphor_agreement` | Anaphor agreement | morphology | reflexive oʻz- agrees with the subject in person/number |
| `binding` | Binding | syntax | reflexive, not a pronoun, inside its binding domain |
| `ditransitive_dative` | Ditransitive dative | syntax | indirect object takes dative, not a second accusative |
| `lexical_case` | Lexical case | syntax | verb assigns a lexical case to its object (qoʻrqmoq + ablative) |
| `nominalization` | Nominalization | syntax | verb selects an -ish/-moq or -gan complement |
| `npi_hech` | NPI licensing (hech + negation) | semantics | hech- words need a negated predicate |
| `passives` | Passives | syntax | an agent phrase (tomonidan) needs a passive verb |
| `person_agreement` | Person agreement | morphology | verb agrees in person with an overt pronoun subject |
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
| `cyrl` | Cyrillic | converted from `latn` with TurkicNLP's transliterator and fixes for errors found in it |
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
python scripts/eval.py --method forced-choice --model google/gemma-3-12b-it --script cyrl --per-phenomenon 3
python scripts/make_table.py
```

- **logprob** (Hugging Face causal LMs): each sentence's total log-probability, summed over its tokens, scored the same way as `scripts/score_pairs.py`. Weights load in float32 by default; `--dtype auto` (bfloat16 or float16 on a GPU) is faster but too coarse for close pairs.
- **forced-choice** (chat models without log-probabilities, through OpenRouter): each pair is shown in both orders and the model answers 1 or 2. Accuracy counts both orders, so always answering "1" scores 50%. The API key is read from `OPENROUTER_API_KEY` or `.env`, and requests ask for providers that don't collect data.
- Masked LMs such as tahrirchi-bert are scored by pseudo-log-likelihood with `scripts/score_pairs.py --mlm`.

`eval.py` writes `results/json/<model>__<config>__<method>.json` and the per-pair scores to `results/pairs/`; `make_table.py` rebuilds the table below and `results/per_phenomenon.md`. Models to run go in `eval_models.txt` (`--models-file eval_models.txt`).

## Results (v1.1)

Accuracy (%) on all 2,400 pairs. **logprob**: causal LM log-probability; **pll**: masked-LM pseudo-log-likelihood; **forced-choice**: chat model picks the sentence. Only models with no unknown tokens on the new letters are run on reformed Latin (`notes/decisions.md`, decision 8). Per phenomenon: [`results/per_phenomenon.md`](results/per_phenomenon.md).

<!-- results:start -->
| Model | Method | Current Latin | Cyrillic | Reformed Latin |
|---|---|---:|---:|---:|
| GF-L 5MB (`goldfish-models/uzn_latn_5mb`) | logprob | 63.3 | 53.6 | — |
| GF-L 10MB (`goldfish-models/uzn_latn_10mb`) | logprob | 73.2 | 55.9 | — |
| GF-L 100MB (`goldfish-models/uzn_latn_100mb`) | logprob | 95.7 | 88.5 | — |
| GF-L full (`goldfish-models/uzn_latn_full`) | logprob | 96.7 | 91.5 | — |
| GF-C 5MB (`goldfish-models/uzn_cyrl_5mb`) | logprob | 45.2 | 61.4 | — |
| GF-C 10MB (`goldfish-models/uzn_cyrl_10mb`) | logprob | 40.6 | 65.2 | — |
| GF-C 100MB (`goldfish-models/uzn_cyrl_100mb`) | logprob | 47.6 | 94.6 | — |
| GF-C full (`goldfish-models/uzn_cyrl_full`) | logprob | 49.4 | 97.4 | — |
| tahrirchi-bert (`tahrirchi/tahrirchi-bert-base`) | pll | 98.6 | 76.8 | 87.3 |
| Qwen2.5-0.5B (`Qwen/Qwen2.5-0.5B`) | logprob | 50.5 | 46.2 | 47.3 |
<!-- results:end -->

## How the pairs were made and checked

- **Sources.** 962 pairs come from Javohir Matniyozov's rule-based pairs over `tahrirchi/uz-books-v2` (`data/external/`, generator in `scripts/jm_generator/`) and 1,438 from Kattabek Norbaev's generator (`scripts/make_pairs.py`) over books (923), Uzbek Wikipedia (506) and legal codes (9).
- **Review.** Of 3,800 candidate pairs, 3,729 were reviewed and 3,267 (87.6%) accepted. Every pair was judged first by Kattabek Norbaev, a native speaker, and then checked with three other native speakers; for some phenomena an AI assistant was used as a consistency check. Rejected pairs keep their reason in `data/pairs_v*.tsv`.
- **Not done yet.** No linguist has verified the pairs (`verified` is false everywhere), and no inter-annotator agreement is reported: the comparison in `results/agreement_KN_JM.md` doesn't count as one, because the two sets of judgments weren't made independently (`notes/decisions.md`, decision 20).
- **Selection.** 150 accepted pairs per phenomenon, chosen at random with a fixed seed; 867 further accepted pairs (`data/benchmark/reserve.tsv`) can replace pairs that fail a later check.

## Repository layout

| Path | Contents |
|---|---|
| `data/jsonl/` | release files (above) |
| `data/benchmark/` | the benchmark TSVs, source of `data/jsonl/`, and the reserve |
| `data/pairs_v*.tsv` | candidate pairs with review decisions |
| `data/external/` | Javohir Matniyozov's generated pairs (v11, v12) |
| `data/multiblimp_uzb.tsv` | MultiBLiMP 1.0, Uzbek split (50 pairs), for comparison |
| `handcheck/` | review sheets |
| `scripts/` | generators, validators, scoring and tables (`score_pairs.py` and `eval_report.py` produced the paper's runs) |
| `results/` | per-pair scores, `results/json/` summaries, `per_phenomenon.md` |
| `notes/` | design decisions, phenomena table, reading notes |
| `paper/` | paper draft (ACL format) |
| `log.md` | research log: date – task – result – next step |

## Limitations

- **Converted alphabets.** The Cyrillic and reformed versions are converted from Latin, not written natively. Russian loanwords can't all be recovered by rule, and only the four main rules of the 2026 reform are applied.
- **Review.** Judgments come from one native speaker, checked with three others; there is no linguist verification or independent agreement figure yet.
- **Size.** 150 pairs per phenomenon gives about ±6 points of precision per phenomenon.

## License

**Data** (`data/`): CC BY-SA 4.0. Some sentences come from Uzbek Wikipedia (CC BY-SA), so the pairs keep its share-alike terms. Other sentences are short excerpts from published books; each pair's `source_id` names its source, and we remove any sentence on request (open an issue). **Code** (`scripts/`): MIT.

## Citation

A paper is in preparation (`paper/`). Until then:

```bibtex
@misc{uzblimp2026,
  title  = {{UzBLiMP}: A Benchmark of Linguistic Minimal Pairs for {U}zbek},
  author = {Norbaev, Kattabek and Matniyozov, Javohir},
  year   = {2026},
  note   = {Version 1.1},
  url    = {https://github.com/kattabeknorbaev/uzblimp}
}
```

## Contributors

| Person | Role |
|---|---|
| Kattabek Norbaev | Project lead: phenomena and design, corpus pair generator, native-speaker review of every pair, evaluation, paper draft |
| Javohir Matniyozov | Rule-based pair generator and its 4,500 pairs (962 in the benchmark), second annotator sheet |
| Three native speakers | Checked the reviewed pairs (not named) |

AI assistants (Claude) helped write code, import review decisions and draft the grammar explanations used in one experiment; the authors checked the results. The paper's AI-assistance statement gives the details.
