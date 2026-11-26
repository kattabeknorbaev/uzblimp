# UzBLiMP data

The benchmark: 2,400 minimal pairs, 150 for each of 16 phenomena, in three alphabets. The grammatical sentence of
each pair is a sentence found in a corpus; the ungrammatical one changes it with one controlled edit. The same
`pair_id` names the same pair in all three alphabets.

| Path | Contents |
|---|---|
| `jsonl/<config>/<paradigm>.jsonl` | the release files, one pair per line; `<config>` is `latn`, `cyrl` or `latn_reformed` |
| `benchmark/uzblimp.tsv`, `uzblimp_cyrl.tsv`, `uzblimp_reformed.tsv` | the same pairs as TSV files, read by the scripts |
| `benchmark/reserve.tsv` | 724 further accepted pairs that can replace pairs that fail a later check |
| `benchmark/excluded.tsv` | the 143 pairs removed in the v1.2 audit, with the reason for each |

## Fields

| Field | Meaning |
|---|---|
| `pair_id` | e.g. `stem_alternation-1042`, the same in all alphabets |
| `paradigm`, `phenomenon`, `field` | phenomenon slug, readable name, and `morphology`, `syntax` or `semantics` |
| `sentence_good`, `sentence_bad` | the pair |
| `lexically_identical` | true when both sentences use the same words (false for every pair: each changes one word form) |
| `script` | `latn`, `cyrl` or `latn_reformed` |
| `source`, `source_id` | how the pair was made (`corpus-edit` for every pair) and where the grammatical sentence comes from |
| `verified`, `verifier_id` | checked by a linguist, and by whom: false and null for every pair so far |
| `reviewer` | native speaker who reviewed the pair (`KN`: Kattabek Norbaev) |
| `converted_from` | `cyrl` and `latn_reformed` only: `latn` |
| `reform_category` | `latn_reformed` only: the edited word changed, only other words changed, or nothing changed |

## Phenomena

| Paradigm | Phenomenon | Field | What the grammatical sentence gets right |
|---|---|---|---|
| `anaphor_agreement` | Anaphor agreement | morphology | reflexive oʻz- agrees with the subject in person and number |
| `binding` | Binding | syntax | a reflexive, not a pronoun, inside its binding domain |
| `ditransitive_dative` | Ditransitive dative | syntax | the indirect object takes the dative, not a second accusative |
| `lexical_case` | Lexical case | syntax | the verb assigns a lexical case to its object (qoʻrqmoq + ablative) |
| `nominalization` | Nominalization | syntax | kerak, mumkin, lozim take the verbal noun in -(i)sh, not the participle -gan |
| `npi_hech` | NPI licensing (hech + negation) | semantics | hech- words need a negated predicate |
| `passives` | Passives | syntax | an agent phrase (tomonidan) needs a passive verb |
| `person_agreement` | Subject agreement | morphology | the verb agrees in person and number with an overt pronoun subject |
| `quantifiers` | Quantifiers (har bir + singular) | morphology | the noun after har bir stays singular |
| `relative_clauses` | Relative clauses | syntax | a relative clause verb is a participle (-gan), not a finite verb |
| `stem_alternation` | Stem alternation (q/k → gʻ/g) | morphology | stem-final q/k becomes gʻ/g before a vowel-initial suffix |
| `suspended_affixation` | Suspended affixation | morphology | the first conjunct keeps its finite person and tense suffix |
| `numeral_no_plural` | No plural after numerals | morphology | the noun after a numeral (+ta) stays singular |
| `postposition_case` | Case after postpositions | syntax | a postposition governs a fixed case (-dan keyin, -dan beri) |
| `possessive_agreement` | Possessive agreement | morphology | the possessive suffix agrees with the genitive possessor |
| `dative_allomorphy` | Dative allomorphy (-ga/-qa/-ka) | morphology | the dative is -qa after q, -ka after k, -ga elsewhere |

The first twelve share their category with TurBLiMP; the last four lie outside its inventory. The field follows
BLiMP where BLiMP has the same contrast; the other assignments are ours.

## Alphabets

| Config | Alphabet | How it was made |
|---|---|---|
| `latn` | current Latin | the reviewed pairs |
| `cyrl` | Cyrillic | converted from `latn` with TurkicNLP's transliterator, fixes for its errors, and a table of the Russian loanwords in the benchmark (функция, концерт, пальто) |
| `latn_reformed` | reformed Latin (Law OʻRQ-1184 of 2026, in force from 22 April 2027) | converted from `latn` with the four letter replacements of the reform: oʻ→ö, gʻ→ğ, sh→ş, ch→ç |

In current Latin, oʻ and gʻ are always written with U+02BB (ʻ); the glottal-stop sign (as in *maʼno*) is a
different letter, U+02BC (ʼ). Mixed apostrophes would make a tokenizer split the same word in different ways.

## How the pairs were made and checked

- Sources: 960 pairs come from Javohir Matniyozov's rule-based generator over the UzBooks collection
  (`tahrirchi/uz-books-v2`), 1,440 from Kattabek Norbaev's generator over books, Uzbek Wikipedia and legal codes.
- Review: of 3,800 candidate pairs, 3,729 were reviewed and 3,267 accepted. Every pair was judged by a native
  speaker and checked with three other native speakers (for some phenomena with an AI assistant as a consistency
  check); 150 accepted pairs per phenomenon were selected at random with a fixed seed.
- Audit (v1.2): the selected pairs were screened again, with the help of an AI assistant, for generator errors and
  for spelling and OCR errors in the source sentences; 120 pairs (5.0%) were replaced from the reserve. The
  Cyrillic version was checked three times for Russian loanwords, and 72 word forms are respelled from a table
  (`scripts/alphabets.py`).
- Human validation: five native speakers who had not worked on the benchmark, one of them a linguist, chose the
  grammatical sentence of 320 pairs (20 per phenomenon) in 99.2% of 1,600 judgments, and their majority agreed with
  the benchmark on every pair (`results/human/`).

The candidate pairs with their review decisions, the generators and the review sheets are kept in `archive/`.

## Limitations

- The Cyrillic and reformed versions are converted from Latin, not written natively, and are not validated
  separately. Russian loanwords that were not recognised may remain.
- Every pair was reviewed by one native speaker and checked with three others; the independent validation covers
  320 pairs (13%) as a forced choice, and its answer key was in this public repository while the study ran. No
  linguist has checked the full benchmark.
- With 150 pairs, the 95% interval of a per-phenomenon accuracy is at most ±8 points.

## Authors

Kattabek Norbaev (design, corpus generator, review of every pair, evaluation) and Javohir Matniyozov (rule-based
generator and its pairs). Three native speakers checked the reviewed pairs, and five others took part in the human
validation; none of them is named. AI assistants helped write code, import review decisions, run the evaluation,
audit the selected pairs and the Cyrillic conversion, and draft the paper; the paper's Ethics statement gives the
details.

## Licence

CC BY-SA 4.0 ([`LICENSE`](LICENSE)). Some sentences come from Uzbek Wikipedia (CC BY-SA), so the pairs keep its
share-alike terms. Other sentences are short excerpts from published books, from copies publicly available on the
internet; each pair's `source_id` names its source, and we remove any sentence on request (open an issue).
