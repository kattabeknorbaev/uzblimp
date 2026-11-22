# Human validation study (forced choice: done, November 2026; ratings: not yet run)

UzBLiMP's pairs were judged by one native speaker and checked with three others. Publication needs
judgments from **independent** native speakers and a **human baseline** to set beside the models. This
folder holds the materials for both and the results of the forced-choice study. The sheets were drawn from
the benchmark by `scripts/make_human_study.py` (seed 2026); returned sheets are scored by
`scripts/human_study_report.py`.

## Forced choice: results

Five native speakers of Uzbek (codes p06–p10), recruited through the first author's contacts and not
involved in building or reviewing the benchmark, one of them a linguist, chose the correct sentence of all
320 pairs. Each received an Excel workbook (consent text and instructions in Uzbek and English; the pairs
in a Latin and a Cyrillic tab, of which they filled in one) and sent the answers back as a Telegram
message; the messages were transcribed and checked against screenshots. An earlier round of five sheets
(p01–p05) was discarded because its answers could not be traced to the participants.

| Measure | Result |
|---|---|
| Accuracy over all 1,600 judgments | 99.2% (individual annotators 97.8–100%) |
| Majority vote | agrees with the benchmark on all 320 pairs |
| Agreement between annotators | mean pairwise 98.4%; Krippendorff's α = 0.97 (on the choices of A or B) |
| Pairs misjudged | 13, each by one annotator; none by two or more |
| Answers marked unsure | 9, on 8 pairs; 2 of them (both suspended affixation) chose the ungrammatical sentence |

The 13 misjudged pairs were reread: in each, the benchmark's choice is correct (mostly slips on clear
contrasts such as *qishloqga for qishloqqa), so no pair was replaced. Per-phenomenon accuracy and the models
on the same pairs: [`results/human_study.md`](../results/human_study.md); paper, Appendix E.

**What is released.** The consent text promises that answers are published only in aggregate, so the
individual sheets (`responses/fc_<code>.csv`) are not in the repository (`.gitignore`); the first author
keeps them with the original messages. `scripts/human_study_report.py` reduces them to two files from which
every reported statistic can be recomputed: `forced_choice_judgments.csv` (per pair: annotators, how many
chose the grammatical sentence, how many marked the pair as unsure, and how many of those chose the
ungrammatical one) and `forced_choice_annotators.csv` (per code: answered, correct, unsure).
`forced_choice_key.csv` was in this public repository while the study ran.

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
3. Save each returned sheet as CSV in `human_study/responses/` (git-ignored: keep the sheets private):
   `fc_<code>.csv` for forced choice, `ratings1_<code>.csv` or `ratings2_<code>.csv` for the lists.
4. Run `python scripts/human_study_report.py`. It writes the two released count files (above) and
   `results/human_study.md`: accuracy per annotator and phenomenon, majority vote, mean pairwise agreement
   and Krippendorff's alpha, the models' accuracy on the same pairs (each on the script of its training
   data), mean z-scored ratings per phenomenon, and the correlation between human and model differences.
   `--selftest` checks the script on simulated answers.

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
sheets that participants filled in. The files in this folder belong to the completed forced-choice study
and must not be rebuilt. `ratings_key.csv` is public as well; for the rating study, draw a fresh sample
into a private folder (`--seed <new> --out <folder>`), send those lists, publish the key only after all
sheets are back, and score them with `python scripts/human_study_report.py --study <folder>`.
