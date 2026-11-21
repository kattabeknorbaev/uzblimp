# Human validation study (ready to run; not yet run)

UzBLiMP's pairs were judged by one native speaker and checked with three others. Two things are still
missing for publication: judgments from **independent** native speakers, and a **human baseline** to set
beside the models. This folder holds everything needed to collect both. The sheets were drawn from the
benchmark by `scripts/make_human_study.py` (seed 2026); returned sheets are scored by
`scripts/human_study_report.py`.

| Design | Sheet (Latin / Cyrillic) | Size | Time | What it gives |
|---|---|---|---|---|
| **Forced choice** (as in BLiMP) | `forced_choice_latn.csv` / `forced_choice_cyrl.csv` | 320 pairs, 20 per phenomenon | 45–60 min | human accuracy per phenomenon, agreement between annotators, pairs to re-examine |
| **Ratings** (as in TurBLiMP, BLiMP-NL) | `ratings_list1_*.csv`, `ratings_list2_*.csv` | 96 sentences per list, 6 pairs per phenomenon | about 15 min | whether speakers rate the grammatical sentences higher for every phenomenon; correlation with models |

The Latin and Cyrillic sheets contain the same items in the same order, so a participant can use
whichever alphabet they read more easily. `forced_choice_key.csv` and `ratings_key.csv` say which
sentence is the grammatical one: **keep them away from participants.**

## Who

- **Native speakers of Uzbek, adults, who have not seen the benchmark** (so not the authors or the
  people who checked the pairs).
- Forced choice: at least 3 annotators, ideally 5, working independently. Linguists or students of
  Uzbek philology are welcome; note their background.
- Ratings: 20–30 participants, half on each list (TurBLiMP had 30: 17 linguistics students, 13 others).
- If the study is run at a university, follow its procedure for studies with human participants.
  The sheets ask for no names or personal data; give each participant a code (p01, p02, ...). It is
  useful to note for each code: age range, whether they studied linguistics, region, and which
  alphabet they chose.

## How

1. Send each participant one sheet (it opens in Excel, LibreOffice or Google Sheets) with the
   instructions below. Forced choice: fill the `answer` column with **A** or **B** (and an `x` in
   `unsure` when in doubt). Ratings: fill the `rating` column with a number from **1 to 7**.
2. Participants work alone, without dictionaries or the internet, and do not discuss the items.
3. Save each returned sheet as CSV in `human_study/responses/`:
   `fc_<code>.csv` for forced choice, `ratings1_<code>.csv` or `ratings2_<code>.csv` for the lists.
4. Run `python scripts/human_study_report.py`. It writes `results/human_study.md`: accuracy per
   annotator and phenomenon, majority vote, mean pairwise agreement and Krippendorff's alpha, the
   models' accuracy on the same pairs, mean z-scored ratings per phenomenon, and the correlation
   between human and model differences. `--selftest` checks the script on simulated answers.

Pairs on which the majority of annotators disagrees with the benchmark are listed in the report; they
should be re-examined and, if needed, replaced from `data/benchmark/reserve.tsv`.

## Consent text

> This questionnaire is part of a research project on the Uzbek language. Taking part is voluntary and
> you may stop at any time. We do not ask for your name or other personal data; answers are stored
> under a code and published only in aggregate. By continuing you agree to take part.

> Ushbu soʻrovnoma oʻzbek tili boʻyicha ilmiy tadqiqot doirasida oʻtkazilmoqda. Ishtirok etish
> ixtiyoriy, istalgan paytda toʻxtatishingiz mumkin. Ismingiz yoki boshqa shaxsiy maʼlumotlaringiz
> soʻralmaydi; javoblar kod ostida saqlanadi va faqat umumlashtirilgan holda eʼlon qilinadi. Davom
> etish orqali ishtirok etishga rozilik bildirasiz.

## Instructions for participants

**Forced choice (English).** Each row has two sentences, A and B, that differ in one word or ending.
One of them is correct standard Uzbek and the other contains an error. Write A or B in the `answer`
column for the correct one. Rely on your own sense of the language: do not use dictionaries or the
internet and do not ask anyone. Answer every row; if you hesitate, still choose the one that seems
better and put an x in the `unsure` column. Judge the language, not the content or the style.

**Majburiy tanlov (oʻzbekcha).** Har bir qatorda ikkita gap berilgan: A va B. Ular bir-biridan faqat
bitta soʻz yoki qoʻshimcha bilan farq qiladi. Gaplardan biri hozirgi oʻzbek adabiy tilida toʻgʻri,
ikkinchisida esa xato bor. Toʻgʻri deb bilgan gapingizni belgilang: `answer` ustuniga A yoki B deb
yozing. Oʻz til sezgingizga tayaning: lugʻatdan, internetdan foydalanmang va hech kimdan soʻramang.
Har bir qatorga javob bering; ikkilansangiz ham, toʻgʻriroq tuyulganini tanlab, `unsure` ustuniga x
belgisini qoʻying. Gapning mazmuni yoki uslubi emas, tilning toʻgʻriligi baholanadi.

**Мажбурий танлов (кирилл ёзувида).** Ҳар бир қаторда иккита гап берилган: A ва B. Улар бир-биридан
фақат битта сўз ёки қўшимча билан фарқ қилади. Гаплардан бири ҳозирги ўзбек адабий тилида тўғри,
иккинчисида эса хато бор. Тўғри деб билган гапингизни белгиланг: `answer` устунига A ёки B деб
ёзинг. Ўз тил сезгингизга таянинг: луғатдан, интернетдан фойдаланманг ва ҳеч кимдан сўраманг.
Ҳар бир қаторга жавоб беринг; иккилансангиз ҳам, тўғрироқ туюлганини танлаб, `unsure` устунига x
белгисини қўйинг. Гапнинг мазмуни ёки услуби эмас, тилнинг тўғрилиги баҳоланади.

**Ratings (English).** Read each sentence and rate how correct and natural it is in standard Uzbek on
a scale from 1 (completely wrong: nobody would say or write this) to 7 (completely correct and
natural). Write the number in the `rating` column. Rely on your own sense of the language; judge the
language, not whether the content is true or pleasant. Do not think long: your first impression counts.

**Baholash (oʻzbekcha).** Har bir gapni oʻqing va uning hozirgi oʻzbek adabiy tilida qanchalik toʻgʻri
va tabiiy ekanini 1 dan 7 gacha baholang: 1 — mutlaqo notoʻgʻri (bunday deyilmaydi va yozilmaydi),
7 — mutlaqo toʻgʻri va tabiiy. Bahoni `rating` ustuniga yozing. Oʻz til sezgingizga tayaning; gapning
mazmuni rost yoki yoqimli ekaniga emas, tilning toʻgʻriligiga eʼtibor bering. Uzoq oʻylamang: birinchi
taassurotingiz muhim.

**Баҳолаш (кирилл ёзувида).** Ҳар бир гапни ўқинг ва унинг ҳозирги ўзбек адабий тилида қанчалик тўғри
ва табиий эканини 1 дан 7 гача баҳоланг: 1 — мутлақо нотўғри (бундай дейилмайди ва ёзилмайди),
7 — мутлақо тўғри ва табиий. Баҳони `rating` устунига ёзинг. Ўз тил сезгингизга таянинг; гапнинг
мазмуни рост ёки ёқимли эканига эмас, тилнинг тўғрилигига эътибор беринг. Узоқ ўйламанг: биринчи
таассуротингиз муҳим.

## Changing the sample

`python scripts/make_human_study.py --forced-choice 30 --ratings 6 --seed 2026` rebuilds the sheets with
another size or seed. Rebuild **before** any sheet is sent out, never after: the keys must match the
sheets that participants filled in.
