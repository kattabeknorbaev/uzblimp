# UzBLiMP phenomena: first pass (DRAFT)

Status: 2026-10-05, drafted by Claude, **not yet checked by a native speaker**. Every Uzbek sentence below is a draft for Kattabek to accept, fix or reject.

- Rows 1–16 follow TurBLiMP's 16 phenomena in the order of TurBLiMP T1. The Turkish originals are there. Rows 17–22 are Uzbek-specific candidates.
- **Exists in Uzbek?**
  - **yes**: the same contrast exists.
  - **changed**: it exists, but the Turkish design doesn't transfer directly.
  - **no**: the contrast doesn't exist.
  - **?** means I'm unsure.
- **Confidence** says how sure I am that the ungrammatical sentence is clearly bad and the grammatical one is natural:
  - **High**: no rescue reading that I know of.
  - **Medium**: a possible rescue reading or a register issue.
  - **Low**: I don't know whether the contrast exists in Uzbek; the example is mostly a translation of the Turkish design.
- ⚠ **RISKY** marks phenomena where Uzbek allows variation (word order, optional or honorific plural, colloquial forms).
- Spelling: oʻ/gʻ use U+02BB (ʻ). I avoided words with the tutuq belgisi (ʼ) so far.

## A. TurBLiMP phenomena

| Phenomenon | Exists in Uzbek? | Grammatical | Ungrammatical | Notes and risks | Confidence |
|---|---|---|---|---|---|
| 1. Anaphor agreement | yes | Biz uyni oʻzimiz tozaladik. | *Biz uyni oʻzingiz tozaladik. | The reflexive oʻz- + possessive (oʻzim, oʻzing, oʻzimiz…) works like Turkish kendi-. Keep the subject overt so the person is fixed by two cues. | High |
| 2. Argument structure (transitive) | yes | Ukam itdan qoʻrqadi. | *Ukam itni qoʻrqadi. | Lexical case: qoʻrqmoq + ablative, ishonmoq + dative (Senga ishonaman / *Seni ishonaman). Avoid qaramoq: colloquial *bolani qarab tur* ("look after the child") makes its accusative acceptable. | High |
| 3. Argument structure (ditransitive) | yes | Oʻqituvchi oʻquvchilarga yangi mavzuni tushuntirdi. | *Oʻqituvchi oʻquvchilarni yangi mavzuni tushuntirdi. | The indirect object takes dative, and the bad version has two accusatives. Lexical exception to vary on: soʻramoq takes ablative for the person asked (Mendan soʻradi). | High |
| 4. Binding (Principle B) | yes | Men oʻzimni oynada koʻrdim. | *Men meni oynada koʻrdim. | TurBLiMP uses "feel oneself", which works in Uzbek too (oʻzimni yaxshi his qilyapman) but may be a fixed expression. Mirror-type verbs are cleaner. | High |
| 5. Determiners (obligatory *bir*) | ? | Oʻtgan hafta onam pishirgan bir shirinlik yedim. | *Oʻtgan hafta onam pishirgan shirinlik yedim. | The Turkish rule: an object with no case marking, modified by a relative clause, needs *bir*. I don't know whether Uzbek has this rule. The "bad" sentence may be fine. | Low |
| 6. Ellipsis (backward gapping) | yes? | Doʻkonda kurtkani Lola va shimni Jasur tanladi. | *Doʻkonda kurtkani Lola va Jasur shimni tanladi. | ⚠ RISKY (word order). The Turkish parallel-order constraint is unverified for Uzbek, and Uzbek may prefer "…, shimni esa Jasur tanladi". This was the hardest phenomenon for models in TurBLiMP (T2), so it's valuable if it holds. | Low |
| 7. Irregular forms (Turkish aorist -Ar/-Ir) | no; analogue proposed | Bu mening oʻrtogʻim. | *Bu mening oʻrtoqim. | Turkish aorist allomorphy has no Uzbek counterpart, since Uzbek -(a)r is regular. Proposed analogue: a final q→gʻ / k→g change before a vowel-initial suffix (oʻrtoq→oʻrtogʻim, yurak→yuragi). Loanwords that don't alternate (huquq→huquqi) supply the "irregular" part. **Alphabet-sensitive:** gʻ is 2 characters in current Latin but 1 in Cyrillic (ғ) and reformed Latin (ğ). Risk: the misspelling "oʻrtoqim" is common online. | Medium |
| 8. Island effects | ? | Nimani doʻkonga olib kelgan xodim tanbeh eshitdi? | *Uni nega doʻkonga olib kelgan xodim tanbeh eshitdi? | ⚠ RISKY. A question word inside a relative clause may sound odd even in the "good" sentence. Turkish speakers separated this pair least well (F1; 26/30 in T9). | Low |
| 9. Nominalization (suffix choice) | changed | Masalani qayta muhokama qilishni taklif qilaman. | *Masalani qayta muhokama qilganini taklif qilaman. | Uzbek contrasts -ish/-moq with -gan+POSS rather than Turkish -mA/-DIK. We need verbs that allow only one form. Some allow both with different meanings (kelganini / kelishini bilaman = that he came / that he will come). | Low–Medium |
| 10. NPI licensing | yes | Koʻpchilik oldida qoʻshiq aytdim. | *Koʻpchilik oldida hech qachon qoʻshiq aytdim. | TurBLiMP design: add a negative word to a positive clause. It's the same phenomenon as row 20 with a different design. Here the good sentence is **shorter**, which helps it under the length bias (TurBLiMP App E), so accuracy may be inflated. Questions license *hech* (Hech qachon Samarqandga borganmisiz?), so use statements only. | High |
| 11. Passives (impersonal + by-phrase) | yes? | Ertalab maktab hovlisida yugurildi. | *Ertalab oʻquvchilar tomonidan maktab hovlisida yugurildi. | The impersonal passive of an intransitive verb may sound unnatural even in the "good" sentence, so both could be odd. *tomonidan* is formal/written. | Low |
| 12. Quantifiers (bare object) | ? | Doʻkonda poyabzal kiyib koʻrdim. | *Doʻkonda har bir poyabzal kiyib koʻrdim. | Turkish her/çoğu require an accusative object. Uzbek *koʻp* is fine with a bare noun (koʻp kitob oʻqidim), so only *har (bir)* is a candidate. | Low |
| 13. Relative clauses | changed | Imtihonda nazoratchi ogohlantirgan talaba joyiga oʻtirdi. | *Imtihonda nazoratchining ogohlantirgan talaba joyiga oʻtirdi. | Uzbek -gan relatives allow a bare subject (men oʻqigan kitob). A genitive subject needs a possessive on the head noun (…talabasi). The Turkish GEN→ACC swap doesn't transfer, because *nazoratchini ogohlantirgan talaba* is grammatical ("the student who warned the proctor"). | Low–Medium |
| 14. Scrambling (out of an embedded clause) | yes? | Hasanning maqolani yozganini bilaman. | *Hasanning yozganini maqolani bilaman. | ⚠ RISKY (word order). Spoken Uzbek allows material after the verb, and this embedded-clause constraint is unverified. | Low–Medium |
| 15. Subject agreement (TurBLiMP: SG subject + PL verb) | changed | Shifokorlar bu sharoitda ishlashga majbur emaslar. | *Shifokor bu sharoitda ishlashga majbur emaslar. | ⚠ RISKY (honorific or optional plural). TurBLiMP's design relies on a plural verb being impossible with a singular subject (§4.1). In Uzbek a singular subject can take a plural verb as a sign of respect (Dadam keldilar), and plural subjects often take a singular verb (Ular keldi). So the "bad" sentence may be fine. The 7 SG→PL pairs in MultiBLiMP have the same problem. **Use person agreement instead (row 21).** | High that it's risky |
| 16. Suspended affixation | yes? | Kechqurun qizlar bilan ziyofatga bordik va juda xursand boʻldik. | *Kechqurun qizlar bilan ziyofatga bor va juda xursand boʻldik. | The bare stem *bor* is also the 2SG imperative, so the bad sentence has an odd imperative reading. Uzbek usually links clauses with a converb (borib), so the good sentence may sound translated. I don't know whether Uzbek bans suspending the past tense like Turkish does. | Low |

## B. Uzbek-specific candidates

| Phenomenon | Exists in Uzbek? | Grammatical | Ungrammatical | Notes and risks | Confidence |
|---|---|---|---|---|---|
| 17. No plural after numerals | yes | Uchta kitob oldim. | *Uchta kitoblar oldim. | A noun after a numeral stays singular. ⚠ Colloquial and translated forms (ikkita doʻstlar) are common online. The good sentence is shorter, which the length bias favours. *koʻp* + plural is fine (koʻp odamlar), so use numerals only. | High |
| 18. Case after postpositions | yes | Darsdan keyin uchrashamiz.<br>Ertalabdan beri yomgʻir yogʻyapti. | *Darsga keyin uchrashamiz.<br>*Ertalabga beri yomgʻir yogʻyapti. | **keyin/oldin are also adverbs** ("later/earlier"). *Darsga keyin boraman* ("I'll go to class later") is grammatical, so dative + keyin is rescued whenever the verb takes a dative. Our sanity pair may be weaker than it looks. *beri* (ablative only) is safer. Others: qadar (dative), bilan/uchun (nominative; pronouns vary: men uchun / uning uchun). | Medium (keyin), High (beri) |
| 19. Dative allomorphy -ga/-ka/-qa | yes | Biz qishloqqa bordik.<br>U eshikka qaradi. | *Biz qishloqga bordik.<br>*U eshikga qaradi. | After q the dative is -qa, and after k it is -ka. Words ending in gʻ/g (togʻ → toqqa?) need checking. Risks: (a) reviewers may call this spelling, not grammar; (b) misspellings like "qishloqga" are frequent in web text. Also -gacha/-kacha/-qacha. | Medium–High |
| 20. *hech* + negation | yes | Hech kim kelmadi. | *Hech kim keldi. | Negative concord: hech kim/narsa/qachon/qayer need a negated verb. Same phenomenon as row 10, so I'd make it **one phenomenon with two paradigms** (adding the negative word vs flipping the polarity). Here the good sentence is **longer** (-ma-), so the length bias works against it. Qwen failed this exact pair (Task 2). Risks: questions license *hech* (Hech kim keldimi?), and some idioms contain it (hech boʻlmasa = "at least"). | High |
| 21. Subject–verb agreement (person) | yes | Men ertaga kelaman. | *Men ertaga kelasan. | Use 1st/2nd-person mismatches with an **overt** pronoun. Uzbek drops subject pronouns, so without one the "bad" verb is fine (Ertaga kelasan = "you'll come tomorrow"). ⚠ Exclude 3rd-person number (row 15) and avoid mixing sen/siz politeness. MultiBLiMP-uzb already has 43 person pairs (SV-P), so our version adds value through a controlled design. | High |
| 22. Possessive agreement | yes | Mening akam shifokor. | *Mening akang shifokor. | The genitive pronoun and the possessive suffix must match, so the pronoun has to be overt. ⚠ Colloquial *bizning uy* (no suffix) is acceptable, so use mismatches rather than omissions. | High |

## Summary of the first pass

- **TurBLiMP's 16 in Uzbek:**
  - 5 yes (1, 2, 3, 4, 10)
  - 4 yes? (6, 11, 14, 16)
  - 3 changed (9, 13, 15)
  - 3 unknown (5, 8, 12)
  - 1 no, with an analogue proposed (7)
- **Strongest** (high confidence, little variation): 17 numerals, 21 person agreement, 22 possessive agreement, 1 anaphor agreement, 2 lexical case, 4 binding, 10/20 *hech*.
- **Riskiest:**
  - 15: 3rd-person number (honorific/optional plural)
  - 6, 8, 14: word order (ellipsis, islands, scrambling)
  - 5, 12: determiners, quantifiers (may not exist)
  - 11, 16: odd even in the "good" sentence
  - 18: *keyin* (rescued by the adverb reading)
- **Length confound:** the good sentence is shorter in 10 and 17 and longer in 20. Record this for each phenomenon and balance it by design where possible (TurBLiMP App E).
- **Alphabet-sensitive by construction:** 7 (gʻ) and 19 (-qa/-ka) sit exactly on letters that change across the three alphabets.

## Questions for the native check

1. Row 15: is *Shifokor … majbur emaslar* acceptable as honorific? Are MultiBLiMP's 7 SG→PL pairs acceptable?
2. Row 18: is *Darsga keyin uchrashamiz* fully bad, or does "we'll meet later (for class)" rescue it?
3. Row 19: what do gʻ/g-final words take: togʻga or toqqa, bargga or barkka?
4. Rows 5, 6, 8, 11, 12, 16: does the contrast exist at all?
5. Row 7: are k/q → g/gʻ alternations a fair "irregular forms" analogue, or too close to spelling?
