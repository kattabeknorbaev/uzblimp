# UzBLiMP data format

## Pair files

One minimal pair per row, tab-separated, UTF-8, with a header line. Names:
- `pairs_v0.tsv`: seed pairs
- `pairs_v1_<phenomenon>.tsv`: generated candidates (`scripts/make_pairs.py`)
- `pairs_v2_<phenomenon>.tsv`: candidates from Javohir Matniyozov's rule-based generator over `tahrirchi/uz-books-v2` (`scripts/jm_generator/`, imported from `external/`); `postposition_order` and `vowel_glide` are not in the benchmark

Check every file with `python scripts/validate_pairs.py <file>`.

### Required columns

| Column | Meaning | Allowed values |
|---|---|---|
| `id` | Unique pair id: `<phenomenon>-<4 digits>`, e.g. `numeral_no_plural-0007` | unique within the dataset |
| `phenomenon` | One of the 16 phenomenon slugs | see `scripts/schema.py` and `notes/decisions.md` |
| `grammatical` | The grammatical sentence, current Latin, oʻ/gʻ with U+02BB | non-empty |
| `ungrammatical` | The same sentence with **exactly one place** changed | non-empty |
| `method` | How the pair was made | `corpus-edit`, `template`, `hand-written` |
| `source_id` | Where the grammatical sentence comes from: corpus file + line/doc id, or e.g. `phenomena.md row 17` | empty for templates |
| `status` | Review state | `unchecked`, `accepted`, `rejected`, `edited` |
| `notes` | Free text: the breaking operation, doubts | may be empty |

### Optional columns (written by the review tool)

| Column | Meaning |
|---|---|
| `reviewer` | Initials of the native speaker who checked the pair (`KN` Kattabek Norbaev, `JM` Javohir Matniyozov) |
| `reviewed_at` | ISO timestamp of the decision |
| `reason` | Short reason for a rejection |

### Rules (checked by the validator)

- **One place only:** the two sentences differ in exactly one contiguous stretch of words. Changing one word, or inserting or deleting adjacent words (*hech qachon*), counts as one place.
- **Word-order phenomena** (`ellipsis`, `scrambling`; dropped, not in the benchmark): both sentences use the same words in a different order.
- **One script per sentence:** no Latin and Cyrillic letters mixed in one sentence.
- **oʻ/gʻ use U+02BB (ʻ) only.** Other apostrophe variants after o/g are errors.
- **Length:** 4–15 words preferred. Longer or shorter sentences are warnings, empty ones are errors.
- **No duplicates:** no repeated ids or pairs, and no pair whose two sentences are identical. Reusing the same grammatical sentence gives a warning.
- **Personal data:** phone numbers and e-mail addresses give a warning. Names of private people can't be detected automatically; the reviewer rejects those.

### `status` lifecycle

`unchecked` → the reviewer sets `accepted`, `rejected` (with a `reason`), or `edited`. `edited` means the reviewer changed a sentence, and the edited pair counts as accepted. Only `accepted` and `edited` pairs go into the benchmark.

## Other files

| File | What it is |
|---|---|
| `benchmark/` | The benchmark: `uzblimp.tsv` (2,400 pairs in current Latin), `uzblimp_cyrl.tsv` and `uzblimp_reformed.tsv` (the same pairs in Cyrillic and reformed Latin), `reserve.tsv` (724 accepted pairs that can replace failing ones) and `excluded.tsv` (143 pairs removed in the v1.2 audit, with reasons) |
| `external/` | Javohir Matniyozov's generated pair sets (`uzblimp_v11.json`, `uzblimp_v12.json`) |
| `explanations.tsv` | Short grammar explanations per phenomenon, prepared for a later prompting experiment (`notes/grammar_prompting.md`) |
| `sanity.tsv` | 3 hand-written test pairs (day 1) |
| `multiblimp_uzb.tsv` | MultiBLiMP 1.0 Uzbek split (50 pairs), for comparison |
| `pilot_3alphabets.tsv` | 13-pair three-alphabet pilot (day 2) |
| `candidates/` | Corpus sentences found by `scripts/corpus_stats.py`. **Git-ignored; stays on this machine.** |
| `jsonl/` | Release files, one per phenomenon and alphabet, written from `benchmark/` by `scripts/export_jsonl.py` and checked by `scripts/validate.py`; fields in the top-level README |
