# UzBLiMP

[Paper](paper/uzblimp.pdf) · [Data](data/) · [Results](results/README.md) · [Citation](#citation)

A benchmark of 2,400 Uzbek minimal pairs for testing whether a language model prefers the grammatical sentence.

2,400 pairs · 16 phenomena · 3 alphabets (current Latin, Cyrillic, reformed Latin) · validated by native speakers

## Example

Only I am afraid of him (`lexical_case`; the verb takes the ablative, not the accusative):

```
✓  Faqat men undan qoʻrqaman.
✗  Faqat men uni qoʻrqaman.
```

## Results

Accuracy (%) on all 2,400 pairs.

| Model | Latin | Cyrillic | Reformed |
|---|---:|---:|---:|
| Gemma 4 31B | 97.3 | 98.1 | 90.5 |
| TahrirchiBERT | 98.7 | 76.8 | 87.3 |
| Goldfish Latin (full) | 96.7 | 91.7 | – |

Humans: 99.2% of 1,600 judgments. Full tables in [results](results/README.md).

## Quickstart

```bash
pip install -r requirements.txt
python -c "import pandas as pd; print(pd.read_json('data/jsonl/latn/lexical_case.jsonl', lines=True).head())"
python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn --out my_results
```

This model scores 95.8%, as in the paper.

## Data

One pair per line in `data/jsonl/<latn|cyrl|latn_reformed>/<paradigm>.jsonl`. Details in [data/README.md](data/README.md).

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
