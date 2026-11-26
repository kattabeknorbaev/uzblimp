# TatBLiMP: reading notes

Saetov & Gaynullin, *TatBLiMP: A Benchmark of Linguistic Minimal Pairs for Tatar*, arXiv:2609.20832 (2026). The PDF names no venue. Data: huggingface.co/datasets/ilchats/TatBLiMP (CC BY-NC 4.0). Read 2026-10-08. Section numbers refer to the PDF.

## What they built
- **Size:** 16 phenomena, **1,248 pairs**, 47–88 per phenomenon (about 78 on average) (Abstract, Table 1).
- **Inventory:** 15 phenomena adapted from TurBLiMP, plus **one Tatar-specific: no plural after numerals/quantifiers** (*биш китап / \*биш китаплар*), the same as our row 17 (§4.1).
- **Determiners dropped:** a native-speaker check found no obligatory-*bir* contrast in Tatar (§4.1). We had flagged the same doubt for Uzbek.
- **Table 1 also gives the breaking operation for each phenomenon,** e.g. "reflexive takes the wrong person", "object put in the wrong lexical case".

## How they made the pairs (§4.2)
- **Where the grammatical sentence comes from:**
  - ~32% hand-adapted TurBLiMP items
  - ~26% real sentences from Tatar prose and poetry
  - ~42% hand-composed from corpus-verified vocabulary
  - (The abstract says every grammatical member is an "attested sentence", which doesn't match these shares.)
- **Ungrammatical sentence:** a copy with **exactly one morpheme changed**, mostly using the apertium-tat transducer.
- **Plausibility principle:** the bad sentence must be a **real word form** that's wrong in context (never a made-up word), ideally the kind of error that Russian or English interference produces.
- **Native ratification of every pair.** Items are discarded if the bad sentence is accidentally grammatical or the meaning shifts.
- **Origin gate:** a phenomenon is admitted only if it ports from TurBLiMP with a native verdict, or is a documented calque.
- **Critical region:** each pair marks where the violation is, for targeted scoring.

## Scoring and models (§4.3, §5)
- **Main metric: `acc_norm`, byte-normalised accuracy** (log P / UTF-8 bytes). It removes the length advantage. Raw `acc` is reported too, and the two agreeing is their test that the result isn't a length artifact.
- **Shared BOS prefix** for all models.
- **Models:**
  - trained on Tatar from scratch: TATlit-478M, Goldfish-125M
  - adaptations: Tweety-7B, mGPT-1.3B
  - **"frontier" = open-weight models scored by likelihood:** Gemma-4-31B, Llama-4-Scout, Qwen3-32B, gpt-oss-120b (bf16)

## Results (§6, Table 2)
- **Focused training beats scale.** The Tatar-trained models score ~0.97 acc; frontier models 0.80–0.92; mGPT 0.74. Byte-normalisation widens the gap.
- **Where the difficulty is:** binding, nominalization, islands and relative clauses. Most other phenomena are at ceiling for the Tatar-trained models.

## Limitations they state (§8)
- Recognition, not production.
- Literary register only.
- No separate human judgment study yet.
- **Main one:** the inventory inherited from TurBLiMP misses Tatar's own morphology: vowel harmony, suffix assimilation (*-га/-ка*, *-дан/-тан*), affix order, izafet, postposition case government, converbs. They propose a "native second layer".

## What this means for UzBLiMP
1. **Copy:**
   - a phenomenon table with a breaking operation for each phenomenon
   - one-morpheme changes
   - bad forms that are real words
   - native check of every pair
   - a critical-region column
   - `acc` + `acc_norm`
   - a shared BOS
   - "frontier" meaning open-weight models scored by likelihood
2. **Do better where they say they fall short:** include Uzbek's own morphology from the start. Our q→gʻ stem change (row 7), dative *-ga/-qa/-ka* (row 19), postposition case (row 18) and possessive agreement (row 22) are exactly their proposed "native layer".
3. **Byte normalisation across alphabets needs care.** Cyrillic letters and ʻ take 2 bytes in UTF-8, Latin letters 1. `acc_norm` is fine *within* a pair, since both members use the same alphabet, but per-byte scores can't be compared *across* alphabets.
