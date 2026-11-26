# UzBLiMP hand-check guide

Each row has a **good** sentence, copied from a book, and a **bad** sentence where exactly one word was changed (the `changed_word` column, shown as good → bad).

Fill in:
- **good_ok**: Y if the good sentence is normal, grammatical Uzbek (ignore style or old-fashioned wording). N if it is broken or garbled.
- **bad_is_wrong**: Y if the bad sentence is clearly ungrammatical *because of the changed word*. N if it is still acceptable, even if odd.
- **fixed_bad**: optional. If bad_is_wrong = N, write a better bad version that changes the same word.
- **comment**: anything else.
- **mlm_suspicious = YES** means the language model scored the bad sentence as likely or more likely than the good one. Check these rows extra carefully.

Rule per category: what should make the bad sentence wrong.
- **subject_verb_agreement**: the verb no longer agrees with the subject (men … *qildik).
- **anaphor_agreement**: the reflexive no longer matches the subject's person or number (men … *oʻzini).
- **binding**: a plain pronoun is used where the reflexive is required (men *meni his qildim instead of oʻzimni).
- **argument_structure_transitive**: the direct object has dative -ga instead of accusative -ni (*kitobga oʻqidi).
- **argument_structure_ditransitive**: the recipient has -ni instead of -ga, so there are two -ni objects (*unga kitobni berdi → uni kitobni berdi).
- **npi_licensing**: "hech kim/hech narsa/hech qachon" with no negation on the verb (*hech kim keldi).
- **passives**: "X tomonidan" with an active verb instead of a passive one (*tomonidan yozgan).
- **numeral_noun_number**: plural -lar after a number (*ikki kitoblar). Mark N if it is a set phrase or poetic and still OK.
- **vowel_glide_y**: the y glide is missing in a vowel-stem verb (*oʻylaamiz for oʻylaymiz).
- **determiners**: plural after "har bir" (*har bir odamlar).
- **nominalization**: a -gan form where an -ish/-sh verbal noun is required (*borgan kerak).
- **relative_clauses**: a finite verb is used inside the noun-modifying clause (*oʻqidi kitob instead of oʻqigan kitob).
- **suspended_affixation**: the case suffix sits on the first noun instead of the last (*kitobni va daftar instead of kitob va daftarni).
- **postposition_order**: the postposition comes before its noun (*bilan doʻsti).
- **quantifiers** (exploratory): plural after "bir necha" (*bir necha kitoblar). Mark N if you find it acceptable; many speakers do.
