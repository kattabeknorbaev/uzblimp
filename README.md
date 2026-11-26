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

A `lexical_case` pair, "Only I am afraid of him": Faqat men **undan** qoʻrqaman. / Faqat men **uni** qoʻrqaman. The verb takes the ablative, not the accusative.

## Results

Accuracy (%) of the strongest models on all 2,400 pairs.

| Model | Trained on | Latin | Cyrillic | Reformed |
|---|---|---:|---:|---:|
| Gemma 4 31B | multilingual | 97.3 | 98.1 | 90.5 |
| TahrirchiBERT | Uzbek, Latin script | 98.7 | 76.8 | 87.3 |
| Goldfish Latin (full) | Uzbek, Latin script | 96.7 | 91.7 | – |

Full tables, and the human score (99.2% of 1,600 judgments), are in [`results/`](results/README.md) and the paper ([`paper/uzblimp.pdf`](paper/uzblimp.pdf)).

## Quickstart

```bash
pip install -r requirements.txt
python -c "import pandas as pd; print(pd.read_json('data/jsonl/latn/lexical_case.jsonl', lines=True).head())"
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn --out my_results
```

This model scores 95.8%, as in the paper.

## Data

One pair per line in `data/jsonl/<latn|cyrl|latn_reformed>/<paradigm>.jsonl`. Fields and construction: [`data/README.md`](data/README.md).

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
