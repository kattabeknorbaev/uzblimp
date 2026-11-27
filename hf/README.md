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

<h1 align="center">UzBLiMP</h1>

<p align="center"><b>Does your language model know Uzbek grammar?</b><br>
2,400 minimal pairs · 16 phenomena · 3 alphabets · checked by native speakers</p>

<p align="center">
  <a href="paper/uzblimp.pdf">Paper</a> ·
  <a href="data/">Data</a> ·
  <a href="results/README.md">Results</a> ·
  <a href="#citation">Citation</a>
</p>

Each pair is a grammatical Uzbek sentence and a copy with one word made wrong. A model passes the pair if it gives the grammatical one the higher probability. Every pair comes in current Latin, Cyrillic and the new reformed Latin.

```
✓  Faqat men undan qoʻrqaman.     "Only I am afraid of him."
✗  Faqat men uni qoʻrqaman.       (lexical_case: this verb takes the ablative)
```

<p align="center"><img src="assets/results.svg" width="720" alt="Accuracy of the strongest open models in the three alphabets"></p>

Strongest open models, accuracy (%) on all 2,400 pairs. Native speakers chose the grammatical sentence in 99.2% of 1,600 judgments. Asked to pick the grammatical sentence, Claude Fable 5.2 and GPT 6.2 Astra score 100% in all three alphabets (Claude helped build the benchmark, so its score is not independent). More in [results](results/README.md).

## Quickstart

```
pip install -r requirements.txt
python -c "import pandas as pd; print(pd.read_json('data/jsonl/latn/lexical_case.jsonl', lines=True).head())"
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn --out my_results  # 95.8%
```

Data: one pair per line in `data/jsonl/<latn|cyrl|latn_reformed>/<paradigm>.jsonl` ([format](data/README.md)).

## Citation

```
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
