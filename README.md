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

## People

Kattabek Norbaev (author), supervised by Yana Veitsman (University of Göttingen).

## Conventions

Uzbek is written in current Latin with oʻ and gʻ using U+02BB (ʻ), never an ASCII apostrophe or U+2018.
