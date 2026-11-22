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

- The text was drafted by Claude from the project files and results at Kattabek's request; the
  authors own it and must read all of it. The Ethics section states how AI assistance was used.
- The interlinear glosses in `examples.tsv` and the phenomenon descriptions in Appendix A were
  drafted by Claude and need a check by a native speaker and, ideally, a linguist.
- Confirm the author list, affiliations and e-mail addresses in `main.tex`.
- The limitations name what is still open: acceptability ratings (materials in `human_study/`),
  validation of the Cyrillic and reformed versions, a check of the full benchmark by a linguist, and
  models above 1.5 billion parameters.
- The facts about the five annotators in Appendix E were confirmed by the first author on 22 November 2026:
  native speakers, anonymous unpaid volunteers, not involved in building or checking the benchmark, one of
  them (p09) a linguist. Still to state for the ARR checklist: whether an ethics review was sought or needed.
