# Presenting UzBLiMP to professors

Two short e-mail templates, one for linguists and NLP researchers in Uzbekistan and one for
international NLP researchers. Attach `paper/uzblimp.pdf` and link the repository. Fill in the
brackets, keep it short, and send each one personally (not as a mass mailing).

Before sending, make sure the paper reflects decisions only the authors can take: the author list
and affiliations, the pairs excluded in the audit (`data/benchmark/excluded.tsv`), and the
interlinear glosses (`paper/examples.tsv`).

## What to ask for

- **Linguists in Uzbekistan:** a check of the phenomena, the glosses and a sample of pairs; help
  running the human validation study (`human_study/`) with three or more native speakers, which is
  what reviewers will ask for first; co-authorship if they contribute substantially.
- **International NLP researchers:** feedback on the evaluation and the analysis, and, if you post
  on arXiv for the first time, an endorsement for the cs.CL category (arXiv asks first-time
  submitters for one; an established author in the category can give it).
- **Deadline to mention:** ACL 2027 via ACL Rolling Review, submission deadline 4 January 2027.

## Template 1: linguists and NLP researchers in Uzbekistan

> Subject: UzBLiMP — a benchmark of Uzbek grammatical minimal pairs (request for feedback)
>
> Dear Professor [name],
>
> My name is Kattabek Norbaev. Together with Javohir Matniyozov I have built UzBLiMP, a benchmark
> that tests whether language models know Uzbek grammar: 2,400 pairs of sentences, each a
> grammatical sentence from a corpus and a copy with one ungrammatical change, covering 16
> phenomena such as case government, agreement, negative concord and the k/q alternation. Every
> pair is given in current Latin, in Cyrillic and in the Latin alphabet of the 2026 reform.
>
> Our main finding is that models learn this grammar equally well from Latin or Cyrillic text, but
> lose much of it when they read the other alphabet or the reformed spelling, and then fall back
> on sentence length and familiar spellings. The draft paper is attached.
>
> Because your work on [their area] is close to this, I would be very grateful for your opinion,
> in particular on [the description of the phenomena / the glosses / a sample of pairs]. We also
> plan a human validation study with native speakers and would welcome your advice or
> participation. If you were interested in contributing, we would be glad to discuss
> co-authorship. We plan to submit to ACL 2027 (deadline 4 January 2027).
>
> With kind regards,
> Kattabek Norbaev
> [e-mail] · https://github.com/kattabeknorbaev/uzblimp

## Template 2: international NLP researchers

> Subject: UzBLiMP: minimal pairs for Uzbek in three alphabets — feedback on a draft
>
> Dear Professor [name],
>
> I am writing because [TurBLiMP / MultiBLiMP / Goldfish / your work on X] shaped a project of
> ours. UzBLiMP is a benchmark of 2,400 Uzbek minimal pairs over 16 phenomena (12 in the
> categories of TurBLiMP), built from attested corpus sentences and reviewed by native speakers,
> and released in current Latin, Cyrillic and the Latin alphabet of Uzbekistan's 2026 reform.
>
> Evaluating [N] models, we find that script-matched models trained on Latin or on Cyrillic Uzbek
> learn the phenomena to the same degree, but lose up to [X] points on the other script; there,
> and under the reformed spelling, their choices follow token counts and orthographic familiarity
> rather than grammar. The draft is attached and the data and code are public.
>
> We would be very grateful for any feedback before we submit to ACL 2027. [If needed: As
> first-time arXiv submitters, we would also need an endorsement for cs.CL, should you be willing
> to give one after reading the draft.]
>
> Best regards,
> Kattabek Norbaev
> [e-mail] · https://github.com/kattabeknorbaev/uzblimp
