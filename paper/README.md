# Paper

`main.tex` is the paper (ACL format, pdfLaTeX); `uzblimp.pdf` is the compiled preprint version.

| File | What it is | Edit by hand? |
|---|---|---|
| `main.tex` | text of the paper | yes |
| `custom.bib` | references, generated from ACL Anthology metadata and checked against arXiv | add entries, don't retype existing ones |
| `examples.tsv` | the 16 example pairs with morpheme segmentation, glosses and translations | yes; `paper_tables.py` checks them against the benchmark |
| `tables/*.tex` | all tables, and `numbers.tex` with every number the text quotes | **no**: `python scripts/paper_tables.py` |
| `figures/*.pdf` | figures | **no**: `python scripts/paper_figures.py` |
| `acl.sty`, `acl_natbib.bst` | ACL style files (from github.com/acl-org/acl-style-files) | no |

## Numbers in the text

The text never contains a result typed by hand. `\Num{key}` prints the value of `key` from
`tables/numbers.tex`, for example `\Num{acc@tahrirchi-bert@Latin}`; `\Acc{model}{alphabet}` and
`\AccPh{model}{alphabet}{phenomenon}` are shortcuts. A key that does not exist is printed as
**??key??** in the PDF, so search the PDF for `??` after changing the text or the model list.

## Build

```bash
python scripts/paper_tables.py     # tables and numbers from results/
python scripts/paper_figures.py    # figures (needs matplotlib)
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

On Overleaf: upload the whole `paper/` folder, set `main.tex` as the main document and pdfLaTeX as
the compiler. The Cyrillic examples use the T2A font encoding with the Tempora font, both part of
TeX Live.

## Versions

- `\usepackage[preprint]{acl}`: with author names, for arXiv (what `uzblimp.pdf` is).
- `\usepackage[review]{acl}`: anonymous with line numbers, for ACL Rolling Review. Remove the
  repository link in the footnote of the introduction for this version.
- `\usepackage{acl}`: camera-ready.

## Before submitting

Open items after the readiness audit of 22 November 2026 (only the authors can settle them):

1. **Read the whole paper.** The text was drafted with Claude from the project files and results; the
   authors are responsible for every statement in it and must read all of it. The Ethics section states how
   AI assistance was used, as the ACL policy on AI writing assistance asks.
2. ~~Confirm the 143 exclusions~~: done, confirmed by the first author on 22 November 2026.
3. ~~Finish the Cyrillic spot check~~: done on 22 November 2026 (no conversion errors; Section 4.3 updated).
4. ~~Glosses and Appendix A~~: checked and confirmed by a linguist (p09) on 22 November 2026.
5. **Author block**: Javohir Matniyozov stays second author, as an independent researcher (22 November
   2026). Only if you want an affiliation such as Tomaris.ai named (`notes/decisions.md`, decisions 7 and 13),
   change the author block; no Tomaris model or data is evaluated in the paper.
6. ~~Book sentences~~: copies of books publicly available on the internet (first author, 22 November 2026); the Ethics statement says so, and their licence terms stay undocumented with removal on request.
7. ~~Ethics review~~: done; the Ethics statement says that no review was sought and why.

For ACL Rolling Review (deadline 4 January 2027):

- Compile with `[review]`, remove the repository footnote in the introduction, and submit the data and code as
  an anonymous supplementary zip (no git history, without `paper/uzblimp.pdf` and `paper/outreach.md`).
- Fill in the Responsible NLP checklist: draft answers in `arr_checklist.md`.
- All authors need OpenReview profiles. Check the ARR call for the current rules on reviewing duties and on
  preprints. ARR dropped its anonymity period in February 2024 (aclrollingreview.org/anonymity), but one
  copy of the ACL 2027 call still mentions a one-month period; posting the arXiv version before
  4 December 2026 satisfies either rule.
- arXiv asks first-time submitters in cs.CL for an endorsement.

What stays open beyond this submission is named in the Limitations: acceptability ratings (materials in
`human_study/`), validation of the Cyrillic and reformed versions, a check of the full benchmark by a
linguist, and models above 1.5 billion parameters.

Done: the facts about the five annotators in Appendix E were confirmed by the first author on 22 November
2026 (native speakers, anonymous unpaid volunteers, not involved in building or checking the benchmark, one of
them (p09) a linguist).
