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

## The 16 phenomena (Kattabek, 2026-10-08)

| # | Phenomenon (slug) | Row in phenomena.md | Layer | Pairs mostly from | Checked |
|---|---|---|---|---|---|
| 1 | Anaphor agreement (`anaphor_agreement`) | 1 | TurBLiMP | corpus | ✓ |
| 2 | Lexical case, transitive (`lexical_case`) | 2 | TurBLiMP | corpus | ✓ |
| 3 | Ditransitive dative (`ditransitive_dative`) | 3 | TurBLiMP | corpus | ✓ |
| 4 | Binding (`binding`) | 4 | TurBLiMP | corpus / hand | ✓ |
| 5 | q→gʻ / k→g stem change, replacing irregular forms (`stem_alternation`) | 7 | TurBLiMP slot, Uzbek content | corpus | ✓ |
| 6 | *hech* + negation, NPI licensing (`npi_hech`) | 10 + 20 | TurBLiMP | corpus | ✓ |
| 7 | Suspended affixation (`suspended_affixation`) | 16 | TurBLiMP | corpus | ✓ |
| 8 | Nominalization (`nominalization`) | 9 | TurBLiMP | hand (verb list) | ✓ |
| 9 | Person agreement, overt pronoun (`person_agreement`) | 21 | TurBLiMP (subject agreement) | corpus | **not yet** |
| 10 | Ellipsis (`ellipsis`) ⚠ word order | 6 | TurBLiMP | hand | ✓ (clarify) |
| 11 | Scrambling (`scrambling`) ⚠ word order | 14 | TurBLiMP | hand | ✓ |
| 12 | Impersonal passive, reversed in Uzbek (`impersonal_passive`) | 11 | TurBLiMP | hand | ✓ |
| 13 | No plural after numerals (`numeral_no_plural`) | 17 | Uzbek | corpus | ✓ |
| 14 | Case after postpositions (`postposition_case`) | 18 | Uzbek | corpus | ✓ |
| 15 | Possessive agreement (`possessive_agreement`) | 22 | Uzbek | corpus | **not yet** |
| 16 | Dative -ga/-qa/-ka (`dative_allomorphy`) | 19 | Uzbek (morphophonology) | corpus | ✓ |

**Dropped:** determiners (TatBLiMP dropped it too), islands, quantifiers, relative clauses. All four were unclear after the native check.

## Still open

- Check rows 21–22, and resolve the clarifications on rows 5, 8, 12, 13 and 15 (`notes/phenomena.md`).
- Which models exactly (frontier, multilingual), and where to run them. Anything over ~1B needs a cloud GPU.
- SIGTURK and BabyLM deadlines.
- arXiv endorsement route.
- Ethics approval, only if we run a human judgment study.
- Which Tomaris.ai dataset(s), and their terms.
- Licensing for the public release: Wikipedia text is CC BY-SA (attribution, share-alike), and the books' copyright status is not documented in `notes/corpus.md`.
