# Paper draft (ACL template)

`main.tex` is the first draft; `custom.bib` the references; `tables/*.tex` are generated from the results by
`scripts/paper_tables.py` (don't edit them by hand; rerun the script after new results).

## Put it into Overleaf
1. Open the ACL template (link from Russell): https://www.overleaf.com/latex/templates/association-for-computational-linguistics-acl-conference/jvxskxpnznfj → **Open as Template**.
2. Replace the contents of the template's `acl_latex.tex` with `main.tex` (or upload `main.tex` and make it the main document under Menu → Main document).
3. Replace the template's `custom.bib` with ours, and upload the folder `tables/` (4 files) with the same name.
4. Compiler: **pdfLaTeX** (Menu → Settings), the template default.
5. If the Cyrillic examples fail to compile, tell Claude: the draft uses the T2A font encoding, which covers Russian letters and ў but not қ, ғ, ҳ.

## Versions
- `\usepackage[review]{acl}`: anonymous submission with line numbers (ARR).
- `\usepackage[preprint]{acl}`: arXiv preprint. `\usepackage{acl}`: camera-ready.

## Before anyone else reads it
- Red **TODO** marks are pending work or claims still to check (citations marked "TODO verify" in `custom.bib`).
- The draft was written by Claude from the project files at Kattabek's request; Kattabek owns and revises it. The final paper needs an AI-assistance statement (see the Ethics section).
- Overleaf's free plan allows one collaborator per project.

## Update the tables
```
python scripts/paper_tables.py --version v1.1
```
