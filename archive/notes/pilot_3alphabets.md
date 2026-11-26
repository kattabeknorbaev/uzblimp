# Three-alphabet mini-pilot (2026-10-06)

**This is a sanity check of the pipeline, not a finding.** It has 13 pairs, and the Uzbek sentences are unchecked drafts. With n = 13, one pair is 7.7 accuracy points, so no difference below is statistically meaningful.

## Setup

- **Data:** `data/pilot_3alphabets.tsv`, built by `scripts/make_pilot.py`. It has the 3 sanity pairs plus one pair per top-10 phenomenon (`notes/phenomena.md`).
- **Conversion:**
  - Cyrillic: TurkicNLP 0.4.0 via `scripts/alphabets.py`.
  - Reformed Latin: our 4 rules (oʻ→ö, gʻ→ğ, sh→ş, ch→ç).
- **Checks:**
  - All 26 sentences round-trip Cyrillic → Latin unchanged.
  - Claude read every Cyrillic sentence and found no errors (Kattabek to confirm).
  - None of the pairs contains the known TurkicNLP failure cases (t+s, Russian loans).
  - t02 contains no oʻ/gʻ/sh/ch, so it's identical in current and reformed Latin.
- **Scoring:** `scripts/score_pairs.py` (sum of log-probs, float32). No pair differs in the unscored first token.

## Results (correct / 13)

| Model | Current Latin | Cyrillic | Reformed Latin |
|---|---|---|---|
| goldfish-models/uzn_latn_100mb | 13/13 | – | **9/13** ⚠ |
| goldfish-models/uzn_cyrl_100mb | – | 13/13 | – |
| Qwen/Qwen2.5-0.5B | 6/13 | 7/13 | 7/13 |

- ⚠ **The Goldfish reformed drop is mostly a tokenizer artifact.** The Latin Goldfish vocabulary has no tokens for **ğ, ş, ç** (ö exists), so they become `<unk>`. That happens in 15/26 reformed sentences.
  - 3 of its 4 reformed failures (s2, t09, t10) contain `<unk>`.
  - In t10 (*oʻrtogʻim/oʻrtoqim*) the tested letter itself becomes `<unk>`, so the model is comparing `<unk>` with `q`.
  - The 4th failure, t07, has no `<unk>` but a small margin (−0.94).
- **Script-matched Goldfish models never produce `<unk>`** (0/26) and get every pair right. The smallest margins are +2.66 for Latin and +2.42 for Cyrillic.
- **Qwen (byte-level BPE, no `<unk>`) is near chance in every alphabet.** It gives the same verdict in all three alphabets on 7/13 pairs, and is wrong in all three on s2 (*hech*), t05 (lexical case), t07 (binding) and t08 (*beri*).
  - Its MultiBLiMP score (82%) was probably helped by the odd "wrong" verb forms there.
  - t04 (NPI insertion) is "won" by a huge margin (+30 to +36) because the grammatical sentence is 4–7 tokens shorter. That's the length confound.
- **Mean tokens per sentence** (cost of each alphabet):

| Model | Current Latin | Reformed Latin | Cyrillic |
|---|---|---|---|
| Goldfish-latn | 7.7 | 9.0 | – |
| Goldfish-cyrl | – | – | 6.2 |
| Qwen | 11.5 | 10.6 | 14.0 |

  Reformed Latin saves Qwen tokens because ʻ costs a token in current Latin.

## What this means for the design (for the call, not conclusions)

1. **A reformed-Latin condition can't be read off models that have never seen ö/ğ/ş/ç.** For vocabulary-based tokenizers, it mostly measures tokenizer coverage. Options:
   - restrict that condition to byte-level models;
   - report `<unk>` rates next to accuracy;
   - add a control that changes letters without changing grammar.
2. **Script-matched monolingual models (Goldfish latn vs cyrl) are the cleanest Latin-vs-Cyrillic comparison.** It's not yet known whether their training data cover the same content.
3. **A 0.5B multilingual model may be too weak to show anything.** Qwen is at chance even in current Latin.

## Converted sentences (for Kattabek to check)

<!-- generated from data/pilot_3alphabets.tsv -->
| id | phenomenon | | Current Latin | Cyrillic | Reformed Latin | OK? |
|---|---|---|---|---|---|---|
| s1 | postposition_case_keyin | ✓ | Darsdan keyin uchrashamiz. | Дарсдан кейин учрашамиз. | Darsdan keyin uçraşamiz. | |
|  |  | * | Darsga keyin uchrashamiz. | Дарсга кейин учрашамиз. | Darsga keyin uçraşamiz. | |
| s2 | hech_negation_polarity | ✓ | Hech kim kelmadi. | Ҳеч ким келмади. | Heç kim kelmadi. | |
|  |  | * | Hech kim keldi. | Ҳеч ким келди. | Heç kim keldi. | |
| s3 | numeral_no_plural | ✓ | Uchta kitob oldim. | Учта китоб олдим. | Uçta kitob oldim. | |
|  |  | * | Uchta kitoblar oldim. | Учта китоблар олдим. | Uçta kitoblar oldim. | |
| t01 | numeral_no_plural | ✓ | Ikkita bola oʻynayapti. | Иккита бола ўйнаяпти. | Ikkita bola öynayapti. | |
|  |  | * | Ikkita bolalar oʻynayapti. | Иккита болалар ўйнаяпти. | Ikkita bolalar öynayapti. | |
| t02 | person_agreement | ✓ | Men ertaga kelaman. | Мен эртага келаман. | Men ertaga kelaman. | |
|  |  | * | Men ertaga kelasan. | Мен эртага келасан. | Men ertaga kelasan. | |
| t03 | possessive_agreement | ✓ | Mening akam shifokor. | Менинг акам шифокор. | Mening akam şifokor. | |
|  |  | * | Mening akang shifokor. | Менинг аканг шифокор. | Mening akang şifokor. | |
| t04 | hech_npi_insertion | ✓ | Koʻpchilik oldida qoʻshiq aytdim. | Кўпчилик олдида қўшиқ айтдим. | Köpçilik oldida qöşiq aytdim. | |
|  |  | * | Koʻpchilik oldida hech qachon qoʻshiq aytdim. | Кўпчилик олдида ҳеч қачон қўшиқ айтдим. | Köpçilik oldida heç qaçon qöşiq aytdim. | |
| t05 | lexical_case | ✓ | Ukam itdan qoʻrqadi. | Укам итдан қўрқади. | Ukam itdan qörqadi. | |
|  |  | * | Ukam itni qoʻrqadi. | Укам итни қўрқади. | Ukam itni qörqadi. | |
| t06 | anaphor_agreement | ✓ | Biz uyni oʻzimiz tozaladik. | Биз уйни ўзимиз тозаладик. | Biz uyni özimiz tozaladik. | |
|  |  | * | Biz uyni oʻzingiz tozaladik. | Биз уйни ўзингиз тозаладик. | Biz uyni özingiz tozaladik. | |
| t07 | binding | ✓ | Men oʻzimni oynada koʻrdim. | Мен ўзимни ойнада кўрдим. | Men özimni oynada kördim. | |
|  |  | * | Men meni oynada koʻrdim. | Мен мени ойнада кўрдим. | Men meni oynada kördim. | |
| t08 | postposition_case_beri | ✓ | Ertalabdan beri yomgʻir yogʻyapti. | Эрталабдан бери ёмғир ёғяпти. | Ertalabdan beri yomğir yoğyapti. | |
|  |  | * | Ertalabga beri yomgʻir yogʻyapti. | Эрталабга бери ёмғир ёғяпти. | Ertalabga beri yomğir yoğyapti. | |
| t09 | ditransitive_dative | ✓ | Oʻqituvchi oʻquvchilarga yangi mavzuni tushuntirdi. | Ўқитувчи ўқувчиларга янги мавзуни тушунтирди. | Öqituvçi öquvçilarga yangi mavzuni tuşuntirdi. | |
|  |  | * | Oʻqituvchi oʻquvchilarni yangi mavzuni tushuntirdi. | Ўқитувчи ўқувчиларни янги мавзуни тушунтирди. | Öqituvçi öquvçilarni yangi mavzuni tuşuntirdi. | |
| t10 | stem_q_to_gh | ✓ | Bu mening oʻrtogʻim. | Бу менинг ўртоғим. | Bu mening örtoğim. | |
|  |  | * | Bu mening oʻrtoqim. | Бу менинг ўртоқим. | Bu mening örtoqim. | |
