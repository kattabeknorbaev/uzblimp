# TurBLiMP: reading notes

Başar, Padovani, Jumelet, Bisazza (Groningen). *TurBLiMP: A Turkish Benchmark of Linguistic Minimal Pairs*. arXiv:2506.13487v2, 6 Nov 2025. The arXiv PDF doesn't print the venue; our brief says EMNLP 2025. Code and data: github.com/ezgibasar/turblimp (footnote 1). Read 2026-10-05.

Keys: § section, T table, F figure, App appendix. **[code]** = from their `evaluation.py`, not from the paper. **Not in paper** = I looked and didn't find it.

## What they built
- The first Turkish BLiMP-style benchmark: 16 phenomena, one paradigm each, with Argument Structure split into transitive and ditransitive (Abstract, §4.1, T1, Limitations).
- The 16 phenomena (T1): Anaphor Agreement · Arg. Structure Transitive · Arg. Structure Ditransitive · Binding · Determiners · Ellipsis · Irregular Forms · Island Effects · Nominalization · NPI Licensing · Passives · Quantifiers · Relative Clauses · Scrambling · Subject Agreement · Suspended Affixation.
- "Experimental paradigms" on the two Argument Structure sets: all 6 word orders and 4 kinds of subordination (finite, -DIK, -(y)IncA, -(y)ken) (§4.3, App A).
- Human acceptability judgments, released with the benchmark (§5).

## Size
- 16 × 1,000 = **16,000** base pairs (Abstract, §4.2), plus **2,000** experimental pairs: word order 2 × 600, subordination 2 × 400 (§4.3, App A).
- Human study: 216 sentences = 36 categories × 6 (§5).

## How they made the pairs (§4.2)
1. Wrote 10 pairs per phenomenon fully by hand and used them to set guidelines.
2. BERTurk (a masked LM) suggested word replacements at random positions. Each one was checked and fixed by hand, giving **100** pairs per phenomenon.
3. Fully automatic step: BERTurk suggested substitutes in context and Zemberek (Akın & Akın 2007) re-inflected them, giving **1,000** pairs per phenomenon.
- **Not in paper:** whether anyone checked the 900 automatic pairs per phenomenon, who wrote the seed pairs and how many people did, and any inter-annotator agreement. The paper itself admits the augmentation produced some semantic mismatches (§7.2).

## How they validated them (§5, App B–C)
- 30 native speakers (17 linguistics students, 13 non-linguists) took an anonymous Qualtrics survey. They gave informed consent; students received course credit and nobody was paid (§5, App B).
- Ratings used a 7-point Likert scale, following BLiMP-NL, rather than forced choice. Each participant's ratings were converted to z-scores (§5).
- Each category had 6 sentences, 3 acceptable and 3 unacceptable. Two survey versions flipped which was which (§5), so each participant saw only one sentence from each pair.
- Results: acceptable sentences were rated higher for every phenomenon (F1). Island Effects, Passives and Nominalization separated least (F1). Counting participants who rated acceptable above unacceptable on average: Island Effects 26/30, Ellipsis 27/30, Determiners 28/30 (T9).
- **My reading:** about 6 of the 1,000 pairs per phenomenon reached humans. So the survey validates the *phenomena*, not individual pairs. **Not in paper:** the exact number of distinct pairs that were rated.

## Models and scoring (§6, T2)
- 13 models in total:
  - **Monolingual:** Goldfish 5/10/100/1000MB (39M/39M/125M/125M params), BERTurk (185M, masked) and cosmosGPT (774M).
  - **Multilingual, 4–12B:** Gemma 3 4B and 12B, Qwen2.5 7B, Llama 3.1 8B, Aya Expanse 8B (the only instruction-tuned one), Gemma 2 and EuroLLM 9B.
  - The paper gives Gemma 2 three different sizes: 7B (§6), 8B (§7) and 9B (T2). [code] uses `google/gemma-2-9b`.
- Base models were preferred over instruct models. Gemma 3 4B Instruct averaged "4.4% lower" than the base model (Limitations).
- **Scoring:** whole-sentence log-probability via minicons. Accuracy is the share of pairs where the acceptable sentence scores higher (§6). Human–model agreement is Pearson r over per-phenomenon mean differences (§6, F2), with SLOR as a robustness check (App D).
- [code] `sequence_score(pair, reduction=lambda x: x.sum(0).item())` with **no `bos_token` argument** (the minicons default), one pair per batch and a strict `>`. BERTurk uses PLL `within_word_l2r`.
- **Not in paper or code:** precision/dtype, hardware, confidence intervals or significance tests on accuracy.

## Main findings
- Models score well above chance on most phenomena. **Ellipsis** is hardest (14.9–87.5), then Island Effects, Relative Clauses and Determiners (§7, T2).
- The top average accuracies are all about 93.6–93.8: EuroLLM 93.8, BERTurk 93.7, cosmosGPT 93.6, Gemma 3 12B 93.6. Small monolingual models match multilingual models about 12–65× larger (ratio is my calculation from T2). Qwen2.5 7B is the weakest multilingual model at 87.0 (T2, §8).
- Goldfish improves with training data: 63.3 → 64.5 → 85.1 → 89.1 from 5MB to 1000MB (T2).
- Only BERTurk correlates significantly with humans across phenomena: r = 0.65, p = 0.007 (F2), and r = 0.557 with SLOR (T10).
- On Ellipsis, humans separate the pairs fine but models fail, which points to a real gap in the models (§7).
- **Word order:** accuracy drops in non-canonical orders. EuroLLM transitive falls from 97 (SOV) to 81 (OSV). Model preferences follow written-treebank word-order frequencies more than spoken ones (§7.1, T3, T5).
- **Subordination:** finite and adverbial clauses score below the baseline (§7.2, T4, T6).
- **Length:** autoregressive models prefer shorter sentences, but length and subword-count differences explain little (R² 0.08–0.19). Tokenizer–morpheme alignment doesn't explain the ranking either (App E, F4, T11).

## What we copy
- A phenomenon-based design with a T1-style glossed example for each phenomenon.
- Hand-written seed pairs and guidelines first, then controlled variation of the words.
- Their exact scoring: minicons, sum of log-probs, no BOS argument, strict `good > bad`. `scripts/score_pairs.py` already matches this.
- Base models only, and Goldfish as a data-size ladder. Uzbek Goldfish has 5MB/10MB/100MB/full (145MB) in **both Latin and Cyrillic**; 1000MB doesn't exist (HF Hub, checked 2026-10-05).
- Their human study design: Likert 1–7, z-scores, two flipped survey versions and a "x/30 participants" table per phenomenon. Release the consent text and the raw ratings.
- The App E confound check (length and subword-count differences). We already record token counts.

## What we change for Uzbek
- **Script:** every pair in 3 alphabets. This is our new axis; TurBLiMP has one script. The script-matched Latin and Cyrillic Goldfish models give a clean comparison, but whether their training data covers the same content needs checking.
- **Scale:** about 1,000 pairs in total rather than 16,000, so about 50–100 per phenomenon, **every one checked by a native speaker**.
- **Phenomena:** recheck the Turkish ones for Uzbek and add Uzbek-specific ones (`phenomena.md`).
- **Subject agreement:** TurBLiMP relies on a plural verb being impossible with a singular subject (§4.1). The Uzbek honorific plural may break that rule, so use person mismatches and exclude SG→PL pairs.
- **Tools:** we need Uzbek equivalents of BERTurk (substitutes) and Zemberek (inflection), still to be found. Otherwise we fill templates by hand.
- **Models:** ≤1B parameters (our rule), where they used 4–12B.
- **Report what they leave out:** dtype (float32), BOS choice, token counts and bootstrap confidence intervals. With 50–100 pairs per phenomenon, a 5-point gap can be noise.
- **Normalise oʻ/gʻ to U+02BB before scoring.** MultiBLiMP-uzb mixes three different characters.
