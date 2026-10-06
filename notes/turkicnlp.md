# TurkicNLP for Uzbek: what works, what doesn't

Tested 2026-10-06: `turkicnlp` 0.4.0 (PyPI, Apache-2.0, "Pre-Alpha"; by Sherzod Hakimov; github.com/turkic-nlp/turkicnlp) on Windows 11 with Python 3.13. The README tests only Python 3.9–3.12. Checks are reproducible with `scripts/check_turkicnlp.py` and `scripts/morph_probe.py`. The expected outputs in the checks are Claude's drafts and still need Kattabek's check.

## Setup notes

- **Core install** (`pip install turkicnlp`) only pulls numpy and regex. The `[transformers]` extra worked with our torch 2.12 / transformers 5.3.
- **Apertium FST morphology (`[hfst]`) can't be used on Windows.** There are no `hfst` wheels for it (README "Platform compatibility"), and WSL isn't installed here.
- **The Glot500 neural morphology** downloads `cis-lmu/glot500-base` (1.6 GB) plus a 154 MB checkpoint into `TURKICNLP_MODELS_DIR`. Without that variable the download goes to `~/.turkicnlp`. By default it fetches *both* weight formats (≈3.3 GB). We pre-fetched only `model.safetensors`.

## Transliteration (`Transliterator("uzb", …)`): 44/55 checks as expected

**Works:**
- **Our 6 test sentences:** all convert Latin → Cyrillic correctly and round-trip to identical Latin.
- **oʻ/gʻ:** handled whether written with ʻ, ', ‘ or ’.
- **Spelling rules:**
  - yoʻ → йў (not ё)
  - sh/ch/ng, all-caps digraphs, mashhur → машҳур
  - e → э at the start of a word, ye → е at the start or after a vowel (yer, poyezd)
  - tutuq → ъ (taʼlim, sheʼr)
  - ц → ts after a vowel (litsey)

**Fails** (failing check → output):

| Direction | Input → output (expected) | Cause | Impact for UzBLiMP |
|---|---|---|---|
| Lat→Cyr | ketsa → **кеца** (кетса), aytsa → **айца** (айтса) | `ts` is always mapped to ц | **High**: every t-stem + -sa / -sin (conditional, jussive) breaks |
| Lat→Cyr | Isʼhoq → Исъҳоқ (Исҳоқ) | tutuq is always ъ; the tutuq that separates s and h should disappear | low (names) |
| Lat→Cyr | obyekt → обйект (объект) | ye after a consonant isn't handled | low–medium (loans) |
| Lat→Cyr | sirk → сирк (цирк), sentabr → сентабр (сентябрь), kompyuter → компютер (компьютер) | Russian loans aren't rule-based | medium: needs an exception list |
| Cyr→Lat | Ўзбекистон → `O'zbekiston` | outputs ASCII ' for oʻ/gʻ and tutuq | fixed in our wrapper (`scripts/alphabets.py`) |
| Cyr→Lat | Исҳоқ → **Ishoq** (Isʼhoq) | the s|h tutuq isn't inserted, so the result reads as "sh" | low (names), but loses information |
| Cyr→Lat | цирк → tsirk (sirk), сентябрь → sentyabr (sentabr), объект → obʼyekt (obyekt) | 1995 rules for ц/loans not implemented | medium |
| Lat→CTS | Oʻzbekiston → Oʻzbekiston (unchanged) | apostrophes are normalised only on the way to Cyrillic, so U+02BB oʻ/gʻ is ignored | bug |
| Both | Latin → Cyrillic first turns ʻ and ʼ into ASCII `'` | the oʻ/gʻ vs tutuq distinction is lost before conversion | low today, but makes the tutuq bugs above harder to fix |

## Reformed 2026 Latin (ö, ğ, ş, ç)

- **Not supported.** The Uzbek tables are the 1995 alphabet ("1995 official Latin alphabet" in `scripts/transliterator.py`), and nothing in the package mentions 2026.
- **The nearest option is Common Turkic (`Script.COMMON_TURKIC`).** It also has ö/ğ/ş/ç, but it is *not* the reform: it also changes ng→ñ, j→c and I→İ, drops the tutuq, and (see above) ignores U+02BB oʻ/gʻ.
- **For now** we use our own 4-rule converter, `scripts/alphabets.py::to_reformed`. Unverified: how the reform treats the tutuq (Isʼhoq), names and loans.
- **Contribution candidate:** an `uzb` reformed-Latin script (Latin-1995 ↔ Latin-2026 ↔ Cyrillic) with tests.

## Morphology: Glot500 neural analyser + MorphemeTokenizer

**Run on:** 7 of our own sentences plus 10 corpus candidates (4 *-dan keyin*, 3 *hech* + negation, 3 numeral + *-ta*). I checked the outputs by hand (Kattabek to confirm). The corpus sentences aren't reproduced here because they stay local. This is a small sample, so read it as indicative.

**Setup problems:**
- **The default Uzbek tokenizer is Stanza's.** It needs `[stanza]`; we passed `tokenize_backend="rule"` instead.
- **Bug: the backbone downloads twice.** `_ensure_backbone()` saves Glot500 as a plain folder, but the model loads it with `from_pretrained("cis-lmu/glot500-base", cache_dir=…)`, which expects the HF cache layout. It therefore starts a second 1.6 GB download. Workaround in `scripts/morph_probe.py`: point `BACKBONE_NAME` at the local folder. After that it runs offline in about a minute on CPU.

| Target | Neural UD features (`morph_neural`) | MorphemeTokenizer labels |
|---|---|---|
| Ablative *-dan* (7 words) | `Case=Abl` on **2/7**; 1 false `Abl` on a dative (*-ga*) | `ABL` on **6/7**, 0 false (missed *-idan* after a possessive) |
| Negation *-ma-* (5 verbs) | `Polarity=Neg` on **1/5**; *kelmadi* and *keldi* get identical features | `NEG` on **5/5**, 0 false |
| Plural *-lar* (10 words) | `Number=Plur` on **10/10** | `PLUR` on **10/10** |
| Numerals (*uchta*, *bitta*…) | `NUM`, `NumType=Card` on all | numeral and *-ta* not analysed (`ta/?`) |

**Other errors seen:**
- **Neural case is unreliable in general.** It got Gen→Acc, Loc→Gen, Acc→Dat and Acc→Nom wrong. Features are sometimes malformed (`Case=Gen|Case=Nom`). Lemmas are sometimes wrong (*sotmaydigan* → `s`, *talab* → `tala`). Tense is sometimes wrong (*qoʻrqadi* → `Past`).
- **The segmenter over-splits stems that end in suffix-like letters:**
  - *madrasa* → `madras+a/PRS`
  - *talab* → `tala+b/PST.3SG`
  - *hammom* → `hammo+m/POSS.1SG`
  - *taʼlim* → `taʼl+im/POSS.1SG`
- **Other segmenter errors:**
  - Genitive *-ing* (*mening, uning*) is labelled `POSS.2SG`.
  - Converbs *-(i)b* are labelled `PST.3SG`.
  - Possessive + case clusters (*-ini, -idan, -ining*) are left unlabelled.
  - *keyin* → `ke+yin/?`.
  - Stems with gʻ aren't restored to q (*oʻrtogʻim* stays as the stem); the Uzbek alternation table has `p→b, k→g` but no `q→gʻ`.
- **Tokenizer:** dialogue dashes break tokens. *-Bizdan* was lost, and *boshqa,-dedi* became one token. Dialogue like this is common in our books part.

**Verdict:**
- **Finding sentences:** the segmenter's `ABL`/`NEG` labels are about as good as our regexes and could serve as a second filter. The neural UD features aren't reliable enough for case or negation.
- **Editing sentences** (making the ungrammatical member): only with a human check. Over-split stems mean an automatic suffix swap would sometimes corrupt the stem.

## Sketch: a minimal-pair component I could contribute (not built)

1. **Input:** a sentence (any script) and an edit rule per phenomenon, e.g. `ABL→DAT on the dependent of keyin`, `remove NEG in a hech clause`, `add PLUR after NUM+ta`.
2. **Analyse:** `scripts.detector` + `Transliterator` (work in Latin), rule `tokenizer`, `MorphemeTokenizer` segments, Glot500 UPOS to pick the target word.
3. **Edit:** swap, insert or delete exactly one labelled morpheme using the existing suffix allomorph tables (e.g. -ga/-ka/-qa), leaving every other token untouched. Refuse when the target segment is unlabelled (`?`).
4. **Output:** a record of good, bad, phenomenon, token index and morphemes before/after, in Latin-1995, Cyrillic and reformed Latin, marked `needs_review`.
5. **New pieces it needs:** the reformed-Latin `uzb` table, the fixes below, and a `MinimalPairGenerator` processor with per-phenomenon rules and a review export.

## Smaller contribution candidates (bugs found today)

1. Lat→Cyr: `ts` → ц should not apply at t+s morpheme boundaries (*ketsa*, *aytsa*, *ketsin*).
2. Cyr→Lat: an option to output U+02BB/U+02BC instead of ASCII `'`. Keep the s|h tutuq (*Isʼhoq*) and handle *ъе* (*obyekt*).
3. Lat→CTS: apply the same apostrophe normalisation as Lat→Cyr.
4. Glot500 backbone downloaded twice (local_dir vs cache_dir).
5. MorphemeTokenizer `uzb`: add `q→gʻ`; label genitive *-(n)ing*, converb *-(i)b* and possessive + case clusters.
6. Tokenizer: dialogue dashes (`-Word`, `word,-dedi`).
