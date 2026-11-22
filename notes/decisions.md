# Decisions

Each decision gives its source and date: **Kattabek** = his decision; **feedback** = external feedback received on the 2026-10-07 call (reviewer not named, at their request). Anything not settled is under "Still open".

## Settled

| # | Decision | Source | What it changes |
|---|---|---|---|
| 1 | **Independent project.** No supervisor; the feedback reviewer is not named anywhere in project materials. | Kattabek, 2026-10-08 | README updated. Correction emails go to the professors who were told otherwise. |
| 2 | **Framing: a benchmark**, released as an arXiv preprint for feedback. | Kattabek, 2026-10-06 | The paper follows the benchmark-paper format (TurBLiMP, TatBLiMP). |
| 3 | **150 pairs per phenomenon.** | feedback | About ±6 points of precision per phenomenon. More per phenomenon than TatBLiMP (≈78) or TurBLiMP's hand-validated 100. |
| 4 | **16 phenomena → 2,400 pairs**, matching TurBLiMP/TatBLiMP row for row. | Kattabek, 2026-10-08 | 12 TurBLiMP slots kept, 4 weak ones replaced by Uzbek phenomena (list below). |
| 5 | **Structure similar to TurBLiMP and TatBLiMP.** | feedback | Phenomenon table with breaking operations, one-morpheme changes, real-word bad forms, native check of every pair, `acc` + `acc_norm` (`notes/tatblimp.md`). |
| 6 | **Target venues: SIGTURK and BabyLM.** | feedback | Deadlines not yet checked. |
| 7 | **Models: 1 frontier, 1 monolingual, 1 multilingual.** | feedback | "Frontier" must be open-weight, because scoring needs sentence log-probabilities; TatBLiMP did the same. Monolingual: Goldfish (Latin + Cyrillic), possibly Tomaris.ai's model (Kattabek co-founded it, so this must be disclosed). |
| 8 | **Alphabets:** Latin vs Cyrillic is the main comparison; reformed Latin is a small extra, run only on models with 0 `<unk>`, with token counts reported. | Kattabek, 2026-10-06 | Each model is screened for `<unk>` before it enters the reformed condition. |
| 9 | **Corpus: all parts may be used** (books, legal, wiki), plus Tomaris.ai data on Hugging Face if needed. | Kattabek, 2026-10-08 | Corpus-edit pairs can start. Personal data is still skipped. |
| 10 | **Build on TurkicNLP and contribute back.** | Kattabek (agreed with its author, Sherzod Hakimov) | Use its analyser where it's reliable (segmenter ABL/NEG); keep the code modular. |
| 11 | **Local professors who help publish and verify get credit.** | Kattabek, 2026-10-06 | Authorship vs acknowledgment is agreed with each person before they start. |
| 12 | **Targets:** ≥600 checked pairs by the checkpoint, ~1,000 by 1 November; preprint mid-December. Kattabek expects corpus extraction to make this faster. | Kattabek (day-3/4 briefs, 2026-10-08) | Re-plan from the measured acceptance rate after the first review round (Task 4). |
| 13 | **Team: Javokhir Matniyazov** (Tomaris.ai co-founder) helps build the dataset. | Kattabek, 2026-10-08 | Proposed roles: second native annotator on a 15–20% sample (inter-annotator agreement), hand-written pairs for the harder phenomena, model runs on Tomaris GPUs. Authorship and the Tomaris disclosure still to agree. |
| 14 | **Corpus text policy updated:** corpus sentences may pass through the Claude chat (to debug the generator), and `pairs_v1_*.tsv` files with corpus sentences are committed to the private GitHub repo. Raw candidates (`data/candidates/`) and caches stay git-ignored. | Kattabek, 2026-10-08 | Javokhir can access the pair files through GitHub. |
| 15 | **Exactly 150 pairs per phenomenon in the benchmark** (seeded random choice among accepted pairs, as balanced as TatBLiMP); accepted pairs beyond 150 form a **reserve** that replaces pairs failing the second annotator's check. | Kattabek, 2026-10-08 | `scripts/progress.py` counts toward 150 and reserve; the final freeze happens when the benchmark is built. |
| 16 | **Phenomenon list revised:** ellipsis, scrambling and impersonal passive dropped (word order / hand-written / unclear); **passives** (agent phrase needs a passive verb), **relative clauses** (participle, not a finite verb) and **quantifiers** (*har bir* + singular) added from Javokhir's pairs. Optional extras: **vowel glide** (*ishlayman*, not *ishlaaman*) and **postposition order**. | Kattabek, 2026-10-15 | Still 16 core phenomena; extras are reported separately. |
| 17 | **Javokhir's pairs (`uzblimp_v11.json`, 4,500 pairs, rule-based, from `tahrirchi/uz-books-v2`, MIT)** are used for 8 phenomena after our filters (≤15 words, no names/quotes/dialogue, one place) and native review. | Kattabek, 2026-10-15 | `data/pairs_v2_*.tsv`; method credited to JM in the paper. His generator code is still to be added to the repo. |
| 18 | **Models:** add *tahrirchi-bert-base* (Uzbek-only masked LM, Apache-2.0), scored with pseudo-log-likelihood as TurBLiMP did for BERTurk. | Kattabek, 2026-10-15 | One more monolingual model, the masked-LM counterpart of Goldfish. |
| 19 | **Extra experiment: grammar prompting** (Russell Scheinberg's Idea 1): does a stated rule help when the learned pattern is weak? Per pair: baseline, the pair's own explanation, and an unrelated phenomenon's explanation (control). Explanations drafted by Claude from grammar sources (`source` column of `data/explanations.tsv`) at Kattabek's request (2026-10-19) and checked by him as a native speaker; the paper must say so (not "native-written"). |
| 20 | **How the v2 phenomena were reviewed (2026-10-25).** `anaphor_agreement`: `review.py`, pair by pair. `binding`, `person_agreement`, `nominalization`, `ditransitive_dative`, `passives`, `quantifiers`: KN supplied his decisions as lists (a full status table for binding; reject lists with reasons, grouped and commented, for the others; every unlisted pair accepted), imported by Claude into `data/pairs_v2_*.tsv` (and the `pairs_v1_*` top-ups of relative_clauses and nominalization). **Procedure (KN, 2026-10-25):** KN judges first, then double-checks with his co-founder (a second native speaker) and with an AI assistant before finalising. So these are consensus labels; if the co-founder is JM, KN's labels are not independent of JM's and the 86.4% KN–JM figure cannot be reported as inter-annotator agreement. **Update 2026-10-27 (KN):** the check was with three other native speakers (friends); expert review by local university linguists is planned. Paper wording: first pass by KN, checked with three other native speakers; the AI consistency check on some phenomena is disclosed in the AI-assistance statement. IAA to come from an independent blind sample. | Kattabek, 2026-10-25 | The methods section must describe the review procedure accurately, including any AI assistance in preparing the lists. |
| 21 | **Benchmark v1.1: corpus sentences only.** The 12 hand-written seed pairs (`pairs_v0.tsv`, drafted by Claude on day 1 and corrected by KN) are skipped after the seeded shuffle, so only their 12 slots change (next corpus pair in the same order). v1.1 results reuse v1.0 scores for the 2,388 unchanged pairs and score the 12 new ones (`scripts/carry_over.py`). | Kattabek, 2026-10-27 | The paper can say every pair comes from an attested corpus sentence. | Kattabek, 2026-10-18 | Design in `notes/grammar_prompting.md`. Needs instruction-tuned models that are above chance but below ceiling (baseline check first) and a GPU/API budget. Russell's role and credit to agree first (decision 11). |

## The 16 phenomena (revised 2026-10-15)

| # | Phenomenon (slug) | Layer | Pairs from | Status |
|---|---|---|---|---|
| 1 | Anaphor agreement (`anaphor_agreement`) | TurBLiMP | Javokhir v11 | to review |
| 2 | Lexical case, transitive (`lexical_case`) | TurBLiMP | our generator | ✅ 216 |
| 3 | Ditransitive dative (`ditransitive_dative`) | TurBLiMP | Javokhir v11 | to review |
| 4 | Binding (`binding`) | TurBLiMP | Javokhir v11 | to review |
| 5 | q→gʻ / k→g stem change, replacing irregular forms (`stem_alternation`) | TurBLiMP slot, Uzbek content | our generator | ✅ 226 |
| 6 | *hech* + negation, NPI licensing (`npi_hech`) | TurBLiMP | our generator | ✅ 233 |
| 7 | Suspended affixation, verbal *-gan* (`suspended_affixation`) | TurBLiMP | generator to write | – |
| 8 | Nominalization (`nominalization`) | TurBLiMP | Javokhir v11 | to review |
| 9 | Person agreement (`person_agreement`) | TurBLiMP (subject agreement) | Javokhir v11 | to review |
| 10 | Passives: *tomonidan* needs a passive verb (`passives`) | TurBLiMP | Javokhir v11 | to review |
| 11 | Relative clauses: participle, not finite verb (`relative_clauses`) | TurBLiMP | Javokhir v11 | to review |
| 12 | Quantifiers: *har bir* + singular (`quantifiers`) | TurBLiMP | Javokhir v11 | to review |
| 13 | No plural after numerals (`numeral_no_plural`) | Uzbek | our generator | ✅ 234 |
| 14 | Case after postpositions (`postposition_case`) | Uzbek | our generator | ✅ 230 |
| 15 | Possessive agreement (`possessive_agreement`) | Uzbek | generator to write | row 22 not yet checked |
| 16 | Dative -ga/-qa/-ka (`dative_allomorphy`) | Uzbek (morphophonology) | our generator | ✅ 230 |

**Extras** (reported separately): vowel glide `vowel_glide` (*ishlayman / \*ishlaaman*), postposition order `postposition_order` (*jamiyat haqida / \*haqida jamiyat*), both from Javokhir v11.

**Dropped:** determiners, islands, ellipsis, scrambling, impersonal passive (seed pairs for the last three stay in `pairs_v0.tsv` but aren't counted).

## Still open

- Check rows 21–22, and resolve the clarifications on rows 5, 8, 12, 13 and 15 (`notes/phenomena.md`).
- Which models exactly (frontier, multilingual), and where to run them. Anything over ~1B needs a cloud GPU.
- SIGTURK and BabyLM deadlines.
- arXiv endorsement route.
- Ethics approval: settled 2026-11-22 for the forced-choice validation (five anonymous unpaid volunteers; consent text, no names, aggregate release): no ethics review was sought, and the paper says why. Decide again before the rating study.
- Which Tomaris.ai dataset(s), and their terms.
- Licensing for the public release: Wikipedia text is CC BY-SA (attribution, share-alike). The books of our corpus are copies publicly available on the internet (Kattabek, 2026-11-22); their licence terms are not documented, so the release keeps a source identifier per pair and removes sentences on request.
