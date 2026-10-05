# UzBLiMP

A benchmark of about 1,000 Uzbek minimal pairs. Each pair is two sentences that differ in one place: one grammatical, one not. A language model passes a pair if it gives the grammatical sentence a higher total log-probability.

**Research question:** does a model's knowledge of Uzbek grammar hold up across Uzbek's three alphabets: Cyrillic, current Latin, and the reformed Latin approved on 10 September 2026 (oʻ→ö, gʻ→ğ, sh→ş, ch→ç)?

Related work: TurBLiMP (Turkish, EMNLP 2025), TatBLiMP (Tatar, 2026), MultiBLiMP 1.0 (101 languages, agreement only, includes Uzbek).

## Layout

| Path | Contents |
|---|---|
| `notes/` | Reading notes, phenomena table, meeting notes |
| `scripts/` | Scoring and data-processing code |
| `data/` | Minimal-pair TSVs (ours and external) |
| `results/` | Per-pair model scores, one CSV per model × dataset |
| `log.md` | Research log: date – task – result – next step |

## Scoring a dataset

```bash
python -m venv .venv && .venv/Scripts/activate   # Colab: skip, just pip install
pip install -r requirements.txt
python scripts/score_pairs.py --data data/multiblimp_uzb.tsv --good-col sen --bad-col wrong_sen \
    --model goldfish-models/uzn_latn_100mb --group-col phenomenon
```

Writes `results/<model>_<dataset>.csv` (one row per pair) and appends to `results/summary.csv`. Weights load in float32 by default; bfloat16 is too coarse for close pairs. `--bos` prepends a start token for models whose tokenizer doesn't add one (e.g. Qwen), so a difference in the first word is also scored.

## Data sources

- `data/multiblimp_uzb.tsv`: MultiBLiMP 1.0, Uzbek split, downloaded 2026-10-05 from `huggingface.co/datasets/jumelet/multiblimp` (`uzb/data.tsv`). Grammatical column `sen`, ungrammatical `wrong_sen`.
- `data/sanity.tsv`: 3 hand-written pairs for testing the pipeline.

## People

Kattabek Norbaev (author), supervised by Yana Veitsman (University of Göttingen).

## Conventions

Uzbek is written in current Latin with oʻ and gʻ using U+02BB (ʻ), never an ASCII apostrophe or U+2018.
