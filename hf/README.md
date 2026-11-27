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

A benchmark of 2,400 Uzbek minimal pairs. Each pair is a grammatical sentence and the same sentence with one word made wrong; a good language model should give the grammatical one the higher probability. The pairs cover 16 phenomena and come in all three Uzbek alphabets: current Latin, Cyrillic and the new reformed Latin.

```
✓  Faqat men undan qoʻrqaman.     "Only I am afraid of him."
✗  Faqat men uni qoʻrqaman.       (lexical_case: this verb takes the ablative)
```

<p align="center"><img src="assets/results.svg" width="720" alt="Accuracy of the strongest open models in the three alphabets"></p>

Strongest open models, accuracy (%) on all 2,400 pairs. Native speakers chose the grammatical sentence in 99.2% of 1,600 judgments. More in [results](results/README.md).

## Takeaways

- **Frontier chat models hit the ceiling.** Asked to pick the grammatical sentence, Claude Fable 5.2 and GPT 6.2 Astra get every pair right, in both orders, in all three alphabets and all 16 phenomena (Claude helped build the benchmark, so its score is not independent).
- **Seeing the sentences in training is no shortcut.** Tomaris.ai, from the authors' company, had 1,458 of the 2,400 grammatical sentences in its pretraining data, yet it ties TahrirchiBERT at 98.7% on Latin and does no better on pairs from our corpus, almost all seen (98.2%), than on UzBooks pairs, almost all unseen (99.5%).
- **The new alphabet costs accuracy.** Reformed Latin changes only four letters, yet it lowers every model we scored by likelihood except one near chance; Gemma 4 31B drops from 97.3% to 90.5%.

## Quickstart

```
pip install -r requirements.txt
python -c "import pandas as pd
print(pd.read_json('data/jsonl/latn/lexical_case.jsonl', lines=True).head())"
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn --out my_results
```

The last line scores the 100MB Goldfish model on the Latin pairs: 95.8%, as in the paper. Data: one pair per line in `data/jsonl/<latn|cyrl|latn_reformed>/<paradigm>.jsonl` ([format](data/README.md)).

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
