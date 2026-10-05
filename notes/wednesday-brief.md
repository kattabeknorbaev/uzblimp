# Brief for the call on 7 October 2026

1. **Works:** the repo is up. `scripts/score_pairs.py` scores pairs the same way as TurBLiMP's code (minicons, summed log-probs, float32) and gives the same results at any batch size. TurBLiMP notes and a 22-row phenomena draft are in `notes/`.
2. **MultiBLiMP-uzb (50 agreement pairs):** Goldfish uzn_latn_100mb 50/50 (100%), Qwen2.5-0.5B 41/50 (82%). The set is tiny and Goldfish is already at 100%. Some "wrong" verbs also change tense, and the SG→PL pairs may be acceptable honorific plurals.
3. **Phenomena (draft, native check pending):** strongest are numeral + plural, person agreement, possessive agreement, oʻz- agreement, lexical case and hech + negation. Riskiest are 3rd-person number (honorific plural), ellipsis, scrambling and islands (word order), and determiners/quantifiers (may not exist in Uzbek).
4. **Q1:** frame the paper as a benchmark or as a research question? Uzbek Goldfish exists in Latin *and* Cyrillic, which makes a clean script comparison possible.
5. **Q2:** keep the alphabet comparison in, or cut it?
6. **Q3:** which phenomena first?
7. **Q4:** can we involve Uzbek linguists, and how should credit work?
