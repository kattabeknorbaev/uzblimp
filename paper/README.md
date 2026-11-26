# Paper

`main.tex` is the paper (ACL format, pdfLaTeX) and `uzblimp.pdf` the compiled preprint. The tables in `tables/`,
including `tables/numbers.tex` with every number quoted in the text, and the figures in `figures/` are generated
from `results/`; they are not edited by hand.

```bash
python scripts/paper_tables.py
python scripts/paper_figures.py
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

In the text, `\Num{key}` prints the value of `key` from `tables/numbers.tex`; a missing key prints as ??key?? in the
PDF. `examples.tsv` holds the glossed example pairs, which `paper_tables.py` checks against the benchmark, and
`custom.bib` the references. For the anonymous version for ACL Rolling Review, use `\usepackage[review]{acl}` and
remove the repository link from the footnote of the introduction.
