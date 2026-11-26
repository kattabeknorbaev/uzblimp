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

UzBLiMP is a benchmark of minimal pairs for Uzbek: two sentences that differ in one word, one grammatical and one
not, to test whether a language model prefers the grammatical one.

2,400 pairs · 16 phenomena · 3 alphabets (current Latin, Cyrillic, reformed Latin) · validated by native speakers

## Example

A `lexical_case` pair, "Only I am afraid of him": the verb *qoʻrqmoq* "to fear" takes the ablative, not the accusative.

| | Sentence | Gloss |
|---|---|---|
| grammatical | Faqat men undan qoʻrqaman. | only 1SG 3SG-ABL fear-PRS-1SG |
| ungrammatical | Faqat men uni qoʻrqaman. | only 1SG 3SG-ACC fear-PRS-1SG |

In Cyrillic the pair reads Фақат мен ундан/уни қўрқаман, in reformed Latin Faqat men undan/uni qörqaman.

## Results

Accuracy (%) of the strongest models on all 2,400 pairs. A pair is correct when the model gives the grammatical
sentence the higher log-probability (pseudo-log-likelihood for TahrirchiBERT and UzRoBERTa).

| Model | Trained on | Latin | Cyrillic | Reformed |
|---|---|---:|---:|---:|
| Gemma 4 31B | multilingual | 97.3 | 98.1 | 90.5 |
| Gemma 4 26B-A4B | multilingual | 94.8 | 97.5 | 86.2 |
| Gemma 3 27B | multilingual | 94.1 | 97.7 | 84.5 |
| TahrirchiBERT | Uzbek, Latin script | 98.7 | 76.8 | 87.3 |
| UzRoBERTa | Uzbek, both scripts | 93.4 | 96.4 | 78.0 |
| Goldfish Latin (full) | Uzbek, Latin script | 96.7 | 91.7 | – |
| Goldfish Cyrillic (full) | Uzbek, Cyrillic script | 49.5 | 97.3 | – |

Goldfish models were not scored on reformed Latin, where their tokenizers produce unknown tokens. Native speakers
chose the grammatical sentence in 99.2% of 1,600 judgments. All models, chat models and per-phenomenon results are
in [`results/`](results/README.md) and in the paper ([`paper/uzblimp.pdf`](paper/uzblimp.pdf), Tables 3 and 18).

## Quickstart

```bash
pip install -r requirements.txt
python -c "import pandas as pd; print(pd.read_json('data/jsonl/latn/lexical_case.jsonl', lines=True).head())"
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn --out my_results
```

`eval.py` scores a causal language model from Hugging Face in one alphabet (`latn`, `cyrl` or `latn_reformed`)
and prints its accuracy per phenomenon; for this model, 95.8% overall, as in the paper. `scripts/paper_tables.py`
rebuilds the paper's tables and numbers from `results/`.

## Data

One pair per line in `data/jsonl/<config>/<paradigm>.jsonl`, for the configs `latn`, `cyrl` and `latn_reformed`:

```json
{"pair_id": "lexical_case-1189", "paradigm": "lexical_case", "phenomenon": "Lexical case", "field": "syntax", "sentence_good": "Faqat men undan qoʻrqaman.", "sentence_bad": "Faqat men uni qoʻrqaman.", "lexically_identical": false, "script": "latn", "source": "corpus-edit", "source_id": "books/O‘lmas Umarbekov. Ўлмас Умарбеков. Одам бўлиш қийин (роман).txt:3555:1", "verified": false, "verifier_id": null, "reviewer": "KN"}
```

`pair_id` names the same pair in all three alphabets. The fields, the phenomena and how the Cyrillic and reformed
versions were made: [`data/README.md`](data/README.md).

## Citation

```bibtex
@misc{uzblimp2026,
  title  = {{UzBLiMP}: A Benchmark of Linguistic Minimal Pairs for {U}zbek in Three Alphabets},
  author = {Norbaev, Kattabek and Matniyozov, Javohir},
  year   = {2026},
  note   = {Version 1.2},
  url    = {https://github.com/kattabeknorbaev/uzblimp}
}
```

## License

Data: CC BY-SA 4.0 ([`data/LICENSE`](data/LICENSE)); we remove any sentence on request.
Code: MIT ([`LICENSE`](LICENSE)).
