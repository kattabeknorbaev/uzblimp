# ACL Rolling Review: Responsible NLP Research checklist (draft answers)

Draft answers for the checklist in the ARR submission form, with the place in the paper that supports each
one. Items marked **AUTHORS** need a fact or a decision from the authors. Check the wording of the questions
in the form of the current cycle: it changes from time to time.

## A. For every submission

- **A1 Limitations.** Yes: section *Limitations* (human validation, converted alphabets, models, ceiling,
  coverage and validity, contamination).
- **A2 Potential risks.** Yes: *Ethics Statement* (the benchmark is not a measure of a model's overall
  quality; sentences with personal names or personal data were excluded; licences and takedown on request).
  **AUTHORS:** add a sentence if you also want to discuss misuse, e.g. ranking models on a near-ceiling test.

## B. Scientific artifacts (used or created)

- **B1 Citing the creators of artifacts used.** Yes: Sections 2 and 5, Table 8 (models with Hugging Face
  identifiers), Appendix H (software and versions).
- **B2 Licences.** Yes: *Ethics Statement* (data CC BY-SA 4.0, code MIT; evaluated models Apache 2.0 or MIT,
  Table 8; UzBooks MIT; Wikipedia CC BY-SA). **AUTHORS:** the licence of the book sentences of our own corpus is
  not documented (`notes/corpus.md`); the paper says so and offers removal on request.
- **B3 Use consistent with intended use.** Yes: *Ethics Statement* (models and corpora used only to compute
  sentence scores for research; the benchmark is intended for research on language models).
- **B4 Personal information and offensive content.** Partly: sentences with personal names after the first
  word or with personal data were excluded (Section 4.2, *Ethics Statement*). **AUTHORS:** there was no
  separate screen for offensive content; say so, or describe what the native-speaker review covered.
- **B5 Documentation of artifacts.** Yes: Sections 3 and 4, Appendix A (phenomena with glosses), Appendices
  B–D, README and the data card in `README.md`.
- **B6 Statistics of the data.** Yes: Section 4 and Table 5 (150 pairs per phenomenon, lengths, sources);
  the benchmark is a test set only (no train/dev split).

## C. Computational experiments

- **C1 Parameters, compute budget, infrastructure.** Yes: Table 8 (parameters); Appendix H (CPU only, 32-bit
  precision, time per run: minutes for a Goldfish run, ten minutes to three hours for a masked model).
- **C2 Experimental setup and hyperparameters.** Yes: Section 5 (scoring by summed log-probability or
  pseudo-log-likelihood); no model was trained or fine-tuned, so there are no hyperparameters to search.
- **C3 Descriptive statistics.** Yes: Section 5 (Wilson intervals, exact McNemar tests with Holm correction,
  bootstrap intervals); every run is a single deterministic pass, as Appendix H states.
- **C4 Existing packages.** Yes: Appendix H (Python 3.13, PyTorch 2.12.0, Transformers 5.3.0, minicons 0.3.39,
  TurkicNLP 0.4.0, pandas 3.0.3, matplotlib 3.11.2).

## D. Human annotators or participants

- **D1 Instructions.** Yes: Appendix E summarises them; the full texts (consent and instructions in Uzbek and
  English) are in `human_study/README.md` and `human_study/workbook_instructions.json` (supplementary material).
- **D2 Recruitment and payment.** Yes: Appendix E and *Ethics Statement* (five native speakers recruited
  through the first author's contacts; unpaid volunteers).
- **D3 Consent.** Yes: Appendix E and *Ethics Statement* (consent text in Uzbek; answers stored under codes
  and released only in aggregate).
- **D4 Ethics review board.** **AUTHORS:** state whether the study was reviewed by an ethics board or why none
  was needed (no institution; anonymous, voluntary, minimal-risk acceptability judgments), and add the same
  sentence to the *Ethics Statement*.
- **D5 Demographics.** Partly: native speakers of Uzbek, one of them a linguist (Appendix E). No further
  demographic data were collected; say so in the form.

## E. AI assistants

- **E1 Use of AI assistants.** Yes: *Ethics Statement*, second paragraph (candidate phenomena, code, review
  import, model evaluation, audits, human-study materials and transcription, glosses and drafting of the paper;
  the authors reviewed everything and take responsibility). The pilot with chat models (Appendix G) notes that
  Claude models were used to build and audit the benchmark.
