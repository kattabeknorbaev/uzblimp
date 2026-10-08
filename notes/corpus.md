# Uzbek corpus: provenance and terms

Status: DRAFT, 2026-10-06. **Verified** = checked from the files themselves. **Kattabek** = still to be filled in from your answers. Corpus text stays on this machine: `data/candidates/` is git-ignored, and only counts go into the repo.

## Copy used

| | |
|---|---|
| File (verified) | `D:/drive-download-20260601T072834Z-3-001.zip`, 201,309,643 bytes, SHA-256 `792e6076…` (full hash in `results/corpus_stats.json`) |
| Older copy (verified) | `D:/drive-download-20260523T151337Z-3-001/uzbek_data/`. All 2,458 of its files are in the zip with identical sizes; the zip adds 533 books. |
| Not corpus (verified) | `legal/test1.pdf`, `legal/Uzbek AI Model Base Selection.pdf` (skipped); `chroma_db/`, `rag_pipeline.py`, `query_local.py` in the older folder (a RAG project) |
| Origin of the Google Drive folder | **Kattabek** |

## Parts

| Part | Verified | Source | Collected (when, how, by whom) | Terms / license | Cleaning applied |
|---|---|---|---|---|---|
| `books/` | 2,971 `.txt`, one work per file. File names give author (Latin + Cyrillic) and genre (hikoya, roman, hajviya). | **Kattabek** | **Kattabek** | **Kattabek** | **Kattabek** |
| `legal/` | 17 `.txt` (codes and laws, e.g. `konstitutsiya.txt`, `soliq_kodeksi.txt`) | **Kattabek** | **Kattabek** | **Kattabek** | **Kattabek** |
| `wiki/` | `wikipedia_uz_deduped.jsonl`, one article per line, fields `text`, `title`, `source`, `doc_id` | **Kattabek** | **Kattabek** (dump date?) | **Kattabek** | "deduped": how? **Kattabek** |

## Properties found by `scripts/corpus_stats.py` (verified, 2026-10-06)

- **Latin only.** 5 Cyrillic letters in about 420M letters, even in books whose file names are Cyrillic. So the books were probably **transliterated** by someone (who, and with what tool? **Kattabek**). This corpus can't supply Cyrillic text.
- **Already normalized.** oʻ/gʻ are written with U+02BB in ≥98% of cases in every part, and the tutuq belgisi uses U+02BC (ʼ, 706k times). That is the official Unicode convention, which suggests deliberate cleaning (by whom? **Kattabek**). We applied **no** further normalization.
- **Wiki articles have no line breaks.** Each article is one line, so paragraph structure is lost.
- **Wiki has 45,373 ö/ğ/ş/ç.** These are probably foreign names (Turkish, German…), but I haven't checked. Either way, there's no evidence of reformed-alphabet Uzbek.

## How we may use it

- **Kattabek, 2026-10-08:** all parts (books, legal, wiki) may be used, both for searching and for building benchmark pairs. Tomaris.ai data on Hugging Face may also be used if needed.
- **Still to settle before the public release:** Wikipedia text is CC BY-SA (attribution, share-alike), and the books' terms are not documented above. Pairs built from corpus sentences record their `source_id`, so they can be traced or swapped if a source turns out not to be releasable.
- **Personal data:** skip sentences with private people's names, phone numbers, addresses or similar.
