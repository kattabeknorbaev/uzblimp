# UzBLiMP phenomena: first pass (DRAFT)

Status: 2026-10-05, drafted by Claude, **not yet checked by a native speaker**. Every Uzbek sentence below is a draft for Kattabek to accept, fix or reject.
Update 2026-10-06: added corpus counts (from `results/corpus_stats.json`) and a first top-10 ranking (bottom of this file). **Kattabek's native check applied 2026-10-06 (rows 1–20).** His input used ASCII ' in oʻ (*Do'konda*, *O'tgan*, *o'tirishini*); normalized to U+02BB. Rows 21–22 not yet checked.

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
| 1. Anaphor agreement | yes | Biz uyni oʻzimiz tozaladik. | *Biz uyni oʻzingiz tozaladik. | The reflexive oʻz- + possessive (oʻzim, oʻzing, oʻzimiz…) works like Turkish kendi-. Keep the subject overt so the person is fixed by two cues. | High; ✓ checked |
| 2. Argument structure (transitive) | yes | Ukam itdan qoʻrqadi. | *Ukam itni qoʻrqadi. | Lexical case: qoʻrqmoq + ablative, ishonmoq + dative (Senga ishonaman / *Seni ishonaman). Avoid qaramoq: colloquial *bolani qarab tur* ("look after the child") makes its accusative acceptable. | High; ✓ checked |
| 3. Argument structure (ditransitive) | yes | Oʻqituvchi oʻquvchilarga yangi mavzuni tushuntirdi. | *Oʻqituvchi oʻquvchilarni yangi mavzuni tushuntirdi. | The indirect object takes dative, and the bad version has two accusatives. Lexical exception to vary on: soʻramoq takes ablative for the person asked (Mendan soʻradi). | High; ✓ checked |
| 4. Binding (Principle B) | yes | Men oʻzimni oynada koʻrdim. | *Men meni oynada koʻrdim. | TurBLiMP uses "feel oneself", which works in Uzbek too (oʻzimni yaxshi his qilyapman) but may be a fixed expression. Mirror-type verbs are cleaner. | High; ✓ checked |
| 5. Determiners (obligatory *bir*) | ? | Oʻtgan hafta onam pishirgan bir shirinlikdan yedim. | *Oʻtgan hafta onam pishirgan shirinchilikdan yedim. | **Kattabek 06-10:** new pair (ablative *-dan* added). ⚠ **Clarify:** the two sentences differ in two places (*bir* dropped and *shirinlik* → *shirinchilik*). Is *shirinchilik* intended? If it's a typo for *shirinlik*, is *…pishirgan shirinlikdan yedim* ("I ate some of the dessert") really bad? | ⚠ clarify |
| 6. Ellipsis (backward gapping) | yes? (Kattabek's word order) | Doʻkonda Lola kurtkani va Jasur shimni tanladi. | *Doʻkonda Lola kurtkani va shimni Jasur tanladi. | **Kattabek 06-10:** my object-first example doesn't exist in Uzbek. With subject-first order the parallelism contrast holds (S-O and S-O vs S-O and O-S). ⚠ RISKY (word order). **Clarify:** did "doesn't exist" mean my example or the whole phenomenon? | ✓ checked; ⚠ clarify |
| 7. Irregular forms (Turkish aorist -Ar/-Ir) | no; analogue proposed | Bu mening oʻrtogʻim. | *Bu mening oʻrtoqim. | Turkish aorist allomorphy has no Uzbek counterpart, since Uzbek -(a)r is regular. Proposed analogue: a final q→gʻ / k→g change before a vowel-initial suffix (oʻrtoq→oʻrtogʻim, yurak→yuragi). Loanwords that don't alternate (huquq→huquqi) supply the "irregular" part. **Alphabet-sensitive:** gʻ is 2 characters in current Latin but 1 in Cyrillic (ғ) and reformed Latin (ğ). Risk: the misspelling "oʻrtoqim" is common online. TurkicNLP's MorphemeTokenizer has no q→gʻ rule (notes/turkicnlp.md). | Medium; ✓ checked |
| 8. Island effects | ? | Doʻkonga nimani olib kelganligi uchun xodim tanbeh eshitdi? | *Doʻkonga nimani olib keganligi uchun xodim tanbeh eshitdi? | **Kattabek 06-10:** new pair. ⚠ **Clarify:** the only difference is *kelganligi* → *keganligi* (the spoken contraction *kegan*, or a typo). That tests spelling/register, not islands. An island version would keep this good sentence and swap the argument question word for an adjunct one: *Doʻkonga uni nega olib kelganligi uchun xodim tanbeh eshitdi? (Claude's suggestion, needs your judgment). | ⚠ clarify |
| 9. Nominalization (suffix choice) | changed | Masalani qayta muhokama qilishni taklif qilaman. | *Masalani qayta muhokama qilganini taklif qilaman. | Uzbek contrasts -ish/-moq with -gan+POSS rather than Turkish -mA/-DIK. We need verbs that allow only one form. Some allow both with different meanings (kelganini / kelishini bilaman = that he came / that he will come). | Low–Medium; ✓ checked |
| 10. NPI licensing | yes | Koʻpchilik oldida qoʻshiq aytdim. | *Koʻpchilik oldida hech qachon qoʻshiq aytdim. | TurBLiMP design: add a negative word to a positive clause. It's the same phenomenon as row 20 with a different design. Here the good sentence is **shorter**, which helps it under the length bias (TurBLiMP App E), so accuracy may be inflated. Questions license *hech* (Hech qachon Samarqandga borganmisiz?), so use statements only. **Corpus:** see row 20. | High; ✓ checked |
| 11. Passives (impersonal + agent phrase) | changed (opposite of Turkish) | Ertalab oʻquvchilar tomonidan maktab hovlisida yugurildi. | *Ertalab maktab hovlisida yugurildi. | **Kattabek 06-10:** I had them swapped. In Uzbek the impersonal passive **without** an agent is the bad one, the opposite of TurBLiMP's Turkish rule. So the phenomenon needs a new description and more examples before we use it. The good sentence is longer (agent phrase), so the length bias works against it. | ✓ checked; contrast differs from Turkish |
| 12. Quantifiers (bare object) | ? | Doʻkonda poyabzalni kiyib koʻrdim. | *Doʻkonda poyabzal kiyib koʻrdim. | **Kattabek 06-10:** edit applied literally (removed *har bir*, added *-ni*). ⚠ **Clarify:** the pair no longer has a quantifier; it now tests accusative *-ni* on the object. Is bare *poyabzal kiyib koʻrdim* ("tried on shoes") really bad? If you meant *har bir poyabzalni* vs *\*har bir poyabzal*, that keeps the quantifier. | ⚠ clarify |
| 13. Relative clauses → case of the person warned | changed | Imtihonda nazoratchi talabaga joyiga oʻtirishini ogohlantirdi. | *Imtihonda nazoratchi talabani joyiga oʻtirishini ogohlantirdi. | **Kattabek 06-10:** new pair. It's no longer a relative clause: it tests the case of the person warned when *ogohlantirmoq* has a clause complement (dative, not a second accusative), which is close to row 3. **Clarify:** relabel it, or merge it with row 3? | ✓ checked; ⚠ clarify label |
| 14. Scrambling (out of an embedded clause) | yes? | Hasanning maqolani yozganini bilaman. | *Hasanning yozganini maqolani bilaman. | ⚠ RISKY (word order). Spoken Uzbek allows material after the verb, and this embedded-clause constraint is unverified. | Low–Medium; ✓ checked |
| 15. Subject agreement (TurBLiMP: SG subject + PL verb) | changed | Shifokorlar bu sharoitda ishlashga majbur emaslar. | *Shifokor bu sharoitda ishlashga majbur emaslar. | ⚠ RISKY (honorific or optional plural). TurBLiMP's design relies on a plural verb being impossible with a singular subject (§4.1). In Uzbek a singular subject can take a plural verb as a sign of respect (Dadam keldilar), and plural subjects often take a singular verb (Ular keldi). So the "bad" sentence may be fine. The 7 SG→PL pairs in MultiBLiMP have the same problem. **Use person agreement instead (row 21).** **Kattabek 06-10:** "yes its good". **Clarify:** does that mean *Shifokor … majbur emaslar* is bad (so the pair works), or that it's acceptable as an honorific (so my risk note is right)? | ⚠ clarify |
| 16. Suspended affixation | yes | Kechqurun qizlar bilan ziyofatga bordik va juda xursand boʻldik. | *Kechqurun qizlar bilan ziyofatga borgan va juda xursand boʻldik. | **Kattabek 06-10:** the bad form is the participle *borgan* without person/tense, not the bare stem *bor*. That also removes the imperative reading. | ✓ checked |

## B. Uzbek-specific candidates

| Phenomenon | Exists in Uzbek? | Grammatical | Ungrammatical | Notes and risks | Confidence |
|---|---|---|---|---|---|
| 17. No plural after numerals | yes | Uchta kitob oldim. | *Uchta kitoblar oldim. | A noun after a numeral stays singular. ⚠ Colloquial and translated forms (ikkita doʻstlar) are common online. The good sentence is shorter, which the length bias favours. *koʻp* + plural is fine (koʻp odamlar), so use numerals only. **Corpus:** 148,735 numeral+*ta* + word matches. Only 2,553 (1.7%) are followed by a *-lar* word, and some of those are false matches (e.g. *dollar*). So the "ungrammatical" form is rare in edited text. | High; ✓ checked |
| 18. Case after postpositions | yes | Darsdan keyin uchrashamiz.<br>Ertalabdan beri yomgʻir yogʻyapti. | *Darsga keyin uchrashamiz.<br>*Ertalabga beri yomgʻir yogʻyapti. | **keyin/oldin are also adverbs** ("later/earlier"). *Darsga keyin boraman* ("I'll go to class later") is grammatical, so dative + keyin is rescued whenever the verb takes a dative. Our sanity pair may be weaker than it looks. *beri* (ablative only) is safer. Others: qadar (dative), bilan/uchun (nominative; pronouns vary: men uchun / uning uchun). **Corpus:** 58,768 sentences with *-dan keyin* (47,289 of 4–30 words). *beri* not counted yet. | Medium (keyin), High (beri); ✓ checked |
| 19. Dative allomorphy -ga/-ka/-qa | yes | Biz qishloqqa bordik.<br>U eshikka qaradi. | *Biz qishloqga bordik.<br>*U eshikga qaradi. | After q the dative is -qa, and after k it is -ka. Words ending in gʻ/g (togʻ → toqqa?) need checking. Risks: (a) reviewers may call this spelling, not grammar; (b) misspellings like "qishloqga" are frequent in web text. Also -gacha/-kacha/-qacha. | Medium–High; ✓ checked |
| 20. *hech* + negation | yes | Hech kim kelmadi. | *Hech kim keldi. | Negative concord: hech kim/narsa/qachon/qayer need a negated verb. Same phenomenon as row 10, so I'd make it **one phenomenon with two paradigms** (adding the negative word vs flipping the polarity). Here the good sentence is **longer** (-ma-), so the length bias works against it. Qwen failed this exact pair (Task 2). Risks: questions license *hech* (Hech kim keldimi?), and some idioms contain it (hech boʻlmasa = "at least"). **Corpus:** 31,152 sentences with *hech* + a *-ma-* verb; 6,570 with *emas*/*yoʻq*; 993 *hech boʻlmasa*; **13,131 (25%) with no negation detected**: questions, misses by my pattern, or real exceptions? This is the key native check (`data/candidates/hech_no_negation.tsv`). | High (statements); open until the 25% is explained; ✓ checked (25% question still open) |
| 21. Subject–verb agreement (person) | yes | Men ertaga kelaman. | *Men ertaga kelasan. | Use 1st/2nd-person mismatches with an **overt** pronoun. Uzbek drops subject pronouns, so without one the "bad" verb is fine (Ertaga kelasan = "you'll come tomorrow"). ⚠ Exclude 3rd-person number (row 15) and avoid mixing sen/siz politeness. MultiBLiMP-uzb already has 43 person pairs (SV-P), so our version adds value through a controlled design. | High; not yet checked |
| 22. Possessive agreement | yes | Mening akam shifokor. | *Mening akang shifokor. | The genitive pronoun and the possessive suffix must match, so the pronoun has to be overt. ⚠ Colloquial *bizning uy* (no suffix) is acceptable, so use mismatches rather than omissions. | High; not yet checked |

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
- **Alphabet-sensitive by construction:** row 7 (q→gʻ) sits exactly on a letter that changes across the three alphabets (gʻ / ğ / ғ). *Correction 2026-10-06:* row 19 doesn't, because q and k are the same in current and reformed Latin. Only its gʻ-final stems (togʻ → toqqa) involve a changing letter.

## Ranking (2026-10-06, updated after Kattabek's check of rows 1–20)

**Criteria:**
- **Clean:** is the violation free of grey zones?
- **Corpus:** sentences available. Only three phenomena have been counted so far; the rest are estimates, marked *est.*
- **Interest:** comparability with TurBLiMP, what's specific to Uzbek, or relevance to the alphabet question.

Kattabek leans towards Uzbek-specific phenomena for novelty (call notes, decision 3).

| Rank | Phenomenon (row) | Checked | Corpus | Interest | Why / open issue |
|---|---|---|---|---|---|
| 1 | No plural after numerals (17) | ✓ | 148,735 matches | Medium | Clear rule, abundant data. The good sentence is shorter, so pair it with a design that has the opposite length effect. |
| 2 | Person agreement, overt pronoun (21) | not yet | *est.* high | Medium | Directly comparable with MultiBLiMP-uzb, but with controlled pairs and no 3rd-person number. |
| 3 | Possessive agreement (22) | not yet | *est.* high | Medium–High | Uzbek-specific agreement inside the noun phrase; use mismatches, not omissions. |
| 4 | *hech* + negation, two designs (20 + 10) | ✓ | 31,152 | High | The two designs have opposite length effects, and Qwen failed it. **Open:** 25% of corpus *hech* sentences show no negation. |
| 5 | Lexical case, transitive (2) | ✓ | *est.* medium | Medium–High | Same as TurBLiMP's phenomenon. qoʻrqmoq + ABL, ishonmoq + DAT; avoid qaramoq. |
| 6 | Anaphor agreement, oʻz- (1) | ✓ | *est.* medium | Medium | Same as TurBLiMP's phenomenon. |
| 7 | Binding, Principle B (4) | ✓ | *est.* medium | Medium | Same as TurBLiMP's phenomenon. Use mirror-type verbs. |
| 8 | Case after postpositions (18) | ✓ | 58,768 (*keyin*) | Medium | Kattabek accepted the *keyin* pair; *beri* not counted yet. |
| 9 | Ditransitive dative (3) | ✓ | *est.* medium | Medium | Same as TurBLiMP's phenomenon. Row 13's new pair is close to this one. |
| 10 | q→gʻ / k→g stem change (7) | ✓ | *est.* high | High (alphabets) | The only top-10 phenomenon whose critical letter changes across alphabets (gʻ / ğ / ғ). Risk: the misspelling is common on the web. |

**Next in line** (checked by Kattabek, could replace a top-10 row):

| Row | Phenomenon | Note |
|---|---|---|
| 16 | Suspended affixation | New bad form *borgan* (participle without person/tense). Clean, and Uzbek-specific in its form. |
| 9 | Nominalization (-ish vs -gan) | Accepted. Still needs a list of verbs that allow only one form. |
| 19 | Dative -ga/-qa/-ka | Accepted. Reviewers may still call it orthography. |
| 14 | Scrambling | Accepted, but ⚠ word order. |
| 6 | Ellipsis | Kattabek's subject-first pair; ⚠ word order; clarify what "doesn't exist" referred to. |
| 11 | Impersonal passive | Contrast is the **opposite** of Turkish (agentless is bad). Interesting, but needs a description and more examples. |

**Needs clarification before ranking:** rows 5 (two differences in the pair), 8 (the pair tests a spelling/contraction, not islands), 12 (no quantifier left), 13 (now a case phenomenon, close to row 3), 15 ("yes its good" is ambiguous).

**Next corpus counts** (a single ~20-min run of an extended `corpus_stats.py`): rows 1, 2, 7, 18 (*beri*), 21, 22. That would replace the *est.* values above.

## Native-check questions

Answered 2026-10-06:
- Q2: row 18 is fine.
- Q4: rows 5, 6, 8, 11, 12, 16 corrected.
- Q5: row 7 is a fair analogue.

Still open:
1. Row 15: does "yes its good" mean *Shifokor … majbur emaslar* is bad (the pair works) or acceptable as an honorific (the pair fails)? Are MultiBLiMP's 7 SG→PL pairs acceptable?
2. Row 19: what do gʻ/g-final words take: togʻga or toqqa, bargga or barkka?
3. Rows 5, 6, 8, 12, 13: the clarifications noted in each row.
4. Row 20: in `data/candidates/hech_no_negation.tsv`, what are the 20 examples: questions, negations my pattern missed, or real non-negated *hech*?
5. Row 17: in `data/candidates/numeral_ta_plural.tsv`, are these real plurals after numerals, typos, or false matches?
6. Rows 21–22: not checked yet.
