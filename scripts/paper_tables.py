"""LaTeX tables and numbers for the paper, generated from the benchmark and result files.

Nothing in the paper is copied by hand: tables go to paper/tables/<name>.tex and every number quoted in
the text is a key in paper/tables/numbers.tex, read in the text with \\Num{key}. The glossed examples come
from paper/examples.tsv and are checked against the benchmark before they are typeset.

    python scripts/paper_tables.py
"""
import csv
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from analysis import PHENOMENA, SLUGS, benchmark, changed_words, holm, paired, read_tsv, wilson  # noqa: E402
from models import ALPHABETS, MODELS, VERSION, load_runs  # noqa: E402
from models import label as model_label  # noqa: E402

# In tables the small TahrirchiBERT sits in the row below the base model, so its name is shortened there.
TABLE_LABEL = {"tahrirchi-bert-small": r"\quad small"}


def label(model):
    key = model if isinstance(model, str) else model["key"]
    return TABLE_LABEL.get(key, model_label(model))
from schema import n_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "tables"
NAME = {p[0]: p[1] for p in PHENOMENA}
NARROW = {k: v.split(" (")[0] for k, v in NAME.items()}  # without the parenthesis, for one-column tables
SHORT = {p[0]: p[2] for p in PHENOMENA}
LAYER = {p[0]: p[3] for p in PHENOMENA}
SIZES = ["5MB", "10MB", "100MB", "full"]
TRAINED = {"latn": "Latin", "cyrl": "Cyrillic", "both": "both", "multi": "multilingual"}
REFORM_GROUPS = [("critical word: both", "Edited word, both members"),
                 ("critical word: grammatical only", "Edited word, grammatical member only"),
                 ("only other words changed", "Other words only"), ("unchanged", "No new letter")]
NUM = {}


def num(key, value, digits=1):
    """Register a number for the text; whole numbers get a thousands separator, negative ones a real minus sign."""
    if not isinstance(value, str):
        value = f"{value:,.0f}" if digits == 0 else f"{value:.{digits}f}"
        if value.startswith("-"):
            value = value[1:] if float(value.replace(",", "")) == 0 else "$-$" + value[1:]
    NUM[key] = value


def sg(value, digits=1):
    """A number with its sign for a table cell: +1.2, a real minus sign for negative values, plain 0.0."""
    text = f"{value:+.{digits}f}"
    return text[1:] if float(text) == 0 else text.replace("-", "$-$")


def pval(p):
    if p < 0.001:
        mant, exp = f"{p:.0e}".split("e")
        return f"${mant}\\times10^{{{int(exp)}}}$"
    return f"{p:.3f}"


def tex(s):
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_"), ("$", "\\$")):
        s = s.replace(a, b)
    return s


def own(model):
    """Alphabet of the model's Uzbek training text; multilingual and mixed models are reported on Latin."""
    return "Cyrillic" if model["trained"] == "cyrl" else "Latin"


def other(model):
    return "Latin" if own(model) == "Cyrillic" else "Cyrillic"


def acc(df, col="correct"):
    # The tiny offset rounds an exact half up (92.25 to 92.3), as scripts/eval.py does for the README and the
    # JSON summaries; without it Python would round it to the even digit.
    return 100 * df[col].astype(str).eq("True").mean() + 1e-9


def ok(df):
    return df.correct.astype(str).eq("True")


def groups(models):
    out = []
    for m in models:
        if not out or out[-1][0] != m["group"]:
            out.append((m["group"], []))
        out[-1][1].append(m)
    return out


# --- examples -------------------------------------------------------------------------------------------

def read_examples(bench):
    ex = read_tsv(ROOT / "paper" / "examples.tsv")
    for e in ex:
        r = bench.loc[e["pair_id"]]
        assert e["morphemes"].replace("-", "").replace("~", " ") == r.grammatical, e["pair_id"]
        good, bad = changed_words(r.grammatical, r.ungrammatical)
        assert e["bad_morphemes"].replace("-", "") == bad[0].strip(".,!?"), e["pair_id"]
        assert len(e["morphemes"].split()) == len(e["gloss"].split()), e["pair_id"]
        e["good_word"], e["bad_word"] = good[0], bad[0]
    assert [e["phenomenon"] for e in ex] == SLUGS
    return ex


def pair_cell(good_sentence, bad_sentence, wrap=lambda s: s):
    """The sentence with the edited word shown as good/*bad."""
    out = []
    for g, b in zip(good_sentence.split(), bad_sentence.split()):
        if g == b:
            out.append(wrap(tex(g)))
        else:
            tail = g[len(g.rstrip(".,!?")):]
            out.append(f"\\textbf{{{wrap(tex(g.rstrip('.,!?')))}}}/\\ungr{{{wrap(tex(b.rstrip('.,!?')))}}}{tail}")
    return " ".join(out)


def phenomena_table(bench, ex):
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{@{}lp{7.2cm}p{5.1cm}@{}}", r"\toprule",
             r"Phenomenon & Minimal pair & Translation of the grammatical sentence \\"]
    for layer, title in (("TurBLiMP", "Categories shared with TurBLiMP"), ("added", "Outside the TurBLiMP inventory")):
        lines += [r"\midrule", rf"\multicolumn{{3}}{{@{{}}l}}{{\textit{{{title}}}}} \\"]
        for e in ex:
            if LAYER[e["phenomenon"]] == layer:
                r = bench.loc[e["pair_id"]]
                lines.append(f"{NAME[e['phenomenon']]} & {pair_cell(r.grammatical, r.ungrammatical)} & "
                             f"`{tex(e['translation'])}' \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{The 16 phenomena of UzBLiMP with one pair each (150 pairs per phenomenon). The grammatical form of the "
              r"edited word is in bold and the ungrammatical form follows the slash. Interlinear glosses are in "
              r"Appendix~\ref{app:phenomena}.}", r"\label{tab:phenomena}", r"\end{table*}"]
    return "\n".join(lines)


def smallcaps(gloss):
    return re.sub(r"(?<![A-Za-z])([0-9]?[A-Z]{2,})(?![a-z])", lambda m: "\\textsc{" + m.group(1).lower() + "}", gloss)


def glosses(ex):
    lines = []
    for e in ex:
        morph = " ".join(f"\\textbf{{{tex(w)}}}" if w.replace("-", "").strip(".,!?") == e["good_word"].strip(".,!?") else tex(w)
                         for w in e["morphemes"].split())
        lines += [r"\begin{exe}", rf"\ex\label{{ex:{e['phenomenon']}}} {NAME[e['phenomenon']]}", r"\gll " + morph + r"\\",
                  smallcaps(tex(e["gloss"])) + r"\\",
                  rf"\glt `{tex(e['translation'])}' \hfill \ungr{{{tex(e['bad_morphemes'])}}} `{smallcaps(tex(e['bad_gloss']))}'",
                  r"\end{exe}"]
    return "\n".join(lines)


def alphabets_table(ex):
    files = {a: {r["id"]: r for r in read_tsv(ROOT / "data/benchmark" / f)} for a, f in
             (("Latin", "uzblimp.tsv"), ("Cyrillic", "uzblimp_cyrl.tsv"), ("Reformed", "uzblimp_reformed.tsv"))}
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{@{}p{4.95cm}p{5.2cm}p{4.95cm}@{}}", r"\toprule",
             r"Current Latin & Cyrillic & Reformed Latin (2026) \\", r"\midrule"]
    for e in ex:
        cells = []
        for a in ("Latin", "Cyrillic", "Reformed"):
            r = files[a][e["pair_id"]]
            cells.append(pair_cell(r["grammatical"], r["ungrammatical"], (lambda s: f"\\cyr{{{s}}}") if a == "Cyrillic" else (lambda s: s)))
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{The example pairs of Table~\ref{tab:phenomena} in the three alphabets of the release, in the same order.}",
              r"\label{tab:alphabets}", r"\end{table*}"]
    return "\n".join(lines)


# --- benchmark statistics ----------------------------------------------------------------------------------

def review_counts():
    reviewed, accepted, reasons, generated = defaultdict(int), defaultdict(int), defaultdict(Counter), defaultdict(int)
    for f in glob.glob(str(ROOT / "data" / "pairs_v[12]_*.tsv")):
        for r in read_tsv(f):
            if r["phenomenon"] not in NAME:
                continue
            generated[r["phenomenon"]] += 1
            if r["status"] != "unchecked":
                reviewed[r["phenomenon"]] += 1
                accepted[r["phenomenon"]] += r["status"] in ("accepted", "edited")
            if r["status"] == "rejected":
                reasons[r["phenomenon"]][r["reason"]] += 1
    return generated, reviewed, accepted, reasons


def stats_table(bench, reviewed, accepted):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.6pt}", r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
             r"Phenomenon & Books & Words & Forms & $\Delta$B & Acc. \\", r"\midrule"]
    for ph in SLUGS:
        d = bench[bench.phenomenon == ph]
        forms = {w.lower().strip(".,!?") for g, u in zip(d.grammatical, d.ungrammatical) for w in changed_words(g, u)[0]}
        rate = 100 * accepted[ph] / reviewed[ph]
        num(f"forms@{ph}", len(forms), 0)
        num(f"dbytes@{ph}", d.dbytes.mean())
        num(f"accept@{ph}", rate, 0)
        lines.append(f"{NARROW[ph]} & {(d.source == 'books').sum()} & {d.words.mean():.1f} & "
                     f"{len(forms)} & {sg(d.dbytes.mean())} & {rate:.0f} \\\\")
    lines += [r"\midrule", f"All & {(bench.source == 'books').sum()} & "
              f"{bench.words.mean():.1f} & & {sg(bench.dbytes.mean())} & {100 * sum(accepted.values()) / sum(reviewed.values()):.0f} \\\\",
              r"\bottomrule", r"\end{tabular}",
              r"\caption{Benchmark statistics per phenomenon (150 pairs each). \emph{Books}: pairs whose sentence comes from "
              r"UzBooks, the others come from our corpus; "
              r"\emph{Words}: mean length of the grammatical sentence; \emph{Forms}: distinct grammatical word forms at the "
              r"edited position; $\Delta$\emph{B}: mean length of the ungrammatical minus the grammatical sentence in UTF-8 "
              r"bytes; \emph{Acc.}: share (\%) of reviewed candidates accepted in the native-speaker review.}",
              r"\label{tab:stats}", r"\end{table}"]
    return "\n".join(lines)


def reasons_table(reasons):
    cols = [("good sentence is unnatural or wrong", "Source"), ("bad sentence is actually grammatical", "Bad OK"),
            ("dialect or colloquial form", "Dialect"), ("change alters meaning, not grammar", "Meaning"),
            ("name or personal data", "Name")]
    shown = cols[:4]  # the fifth reason is rare and goes into the caption
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.4pt}", r"\begin{tabular}{@{}l" + "r" * len(shown) + "@{}}",
             r"\toprule", "Phenomenon & " + " & ".join(c for _, c in shown) + r" \\", r"\midrule"]
    tot = Counter()
    for ph in SLUGS:
        lines.append(NARROW[ph] + " & " + " & ".join(str(reasons[ph][k]) for k, _ in shown) + r" \\")
        tot.update({k: reasons[ph][k] for k, _ in cols})
    n = sum(tot.values())
    for (k, short) in cols:
        num(f"reject@{short}", tot[k], 0)
        num(f"rejectpct@{short}", 100 * tot[k] / n, 0)
    num("reject@all", n, 0)
    names = tot[cols[4][0]]
    lines += [r"\midrule", "All & " + " & ".join(str(tot[k]) for k, _ in shown) + r" \\", r"\bottomrule", r"\end{tabular}",
              r"\caption{Reasons for rejecting candidate pairs in the native-speaker review. \emph{Source}: the corpus "
              r"sentence is unnatural or wrong (mostly OCR errors and typos); \emph{Bad OK}: the ungrammatical member has a "
              r"grammatical reading; \emph{Dialect}: dialectal or colloquial form; \emph{Meaning}: the edit changes the "
              r"meaning rather than the grammaticality. " + (f"{names} further pair{'s were' if names != 1 else ' was'} rejected "
              r"because of a personal name." if names else "") + "}",
              r"\label{tab:reasons}", r"\end{table}"]
    return "\n".join(lines)


# --- results ----------------------------------------------------------------------------------------------

def per_phenomenon_table(runs, pick, caption, ref, extra=(), pairs=None, models=None, digits=1):
    """Rows: models (alphabet given by pick(model)); columns: the 16 phenomena and their mean. extra: rows
    (label, {phenomenon: accuracy}, mean) added after a rule at the end; pairs: only these pair ids."""
    # Rows of human accuracy add 100.0 to columns that have none otherwise, so these tables are set tighter.
    lines = [r"\begin{table*}[t]", r"\centering\footnotesize", rf"\setlength{{\tabcolsep}}{{{1.8 if extra else 2.1}pt}}",
             r"\begin{tabular}{@{}ll" + "r" * 17 + "@{}}", r"\toprule",
             "Model & & " + " & ".join(SHORT[ph] for ph in SLUGS) + r" & Avg. \\"]
    for group, models in groups(models or MODELS):
        rows = []
        for m in models:
            a = pick(m)
            df = runs.get((m["key"], a))
            if df is None:
                continue
            if pairs is not None:
                df = df[df.index.isin(pairs)]
            cells = []
            for ph in SLUGS:
                v = acc(df[df.phenomenon == ph])
                cells.append(f"\\cellcolor{{black!12}}{v:.{digits}f}" if v < 50 else f"{v:.{digits}f}")
            rows.append(f"{label(m)} & {a[0]} & " + " & ".join(cells) + f" & \\textbf{{{acc(df):.1f}}} \\\\")
        if rows:
            lines += [r"\midrule", rf"\multicolumn{{19}}{{@{{}}l}}{{\textit{{{group}}}}} \\"] + rows
    if extra:
        lines.append(r"\midrule")
        for name, values, mean in extra:
            lines.append(f"{name} & & " + " & ".join(f"{values[ph]:.{digits}f}" for ph in SLUGS) + f" & \\textbf{{{mean:.1f}}} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", rf"\caption{{{caption}}}", rf"\label{{{ref}}}", r"\end{table*}"]
    return "\n".join(lines)


# --- larger models (GPU) -----------------------------------------------------------------------------------

def gpu_length_profile(df):
    """Accuracy on pairs whose members have the same number of tokens, and the length gap (as for the CPU runs)."""
    d = df.bad_ntok - df.good_ntok
    good = ok(df)
    return 100 * good[d == 0].mean(), 100 * (good[d > 0].mean() - good[d < 0].mean())


def gpu_block(gruns, cruns, bench):
    """Numbers and the appendix table for the larger models scored on GPUs (results/gpu_runs/README.txt). Tomaris.ai,
    which is not held out, is reported in its own row and kept out of every range and count."""
    gpu = [m for m in MODELS if m.get("setup") == "gpu" and all((m["key"], a) in gruns for a in ALPHABETS)]
    held = [m for m in gpu if m.get("held_out", True)]
    rest = [m for m in gpu if not m.get("held_out", True)]
    both = bench.index[bench.reform_group == "critical word: both"]
    gr = bench.index[bench.reform_group == "critical word: grammatical only"]
    vals = {}
    for m in held + rest:
        L, C, R = (gruns[(m["key"], a)] for a in ALPHABETS)
        v = dict(L=acc(L), C=acc(C), R=acc(R), loss=acc(L) - acc(R),
                 both=acc(L.loc[both]) - acc(R.loc[both]), gr=acc(L.loc[gr]) - acc(R.loc[gr]))
        for a, df in zip(ALPHABETS, (L, C, R)):
            num(f"acc@{m['key']}@{a}", acc(df))
            for ph in SLUGS:
                num(f"accph@{m['key']}@{a}@{ph}", acc(df[df.phenomenon == ph]))
        num(f"ref@{m['key']}@all@loss", v["loss"])
        num(f"ref@{m['key']}@critical word: both@loss", v["both"])
        num(f"ref@{m['key']}@critical word: grammatical only@loss", v["gr"])
        num(f"len@{m['key']}@Latin@gap", gpu_length_profile(L)[1])
        vals[m["key"]] = v
    H = [vals[m["key"]] for m in held]
    num("gpu@n", len(held), 0)
    params = [float(m["params"].rstrip("B")) for m in held]
    num("gpu@params@min", min(params))
    num("gpu@params@max", max(params), 0)
    for k in ("L", "C", "R", "loss", "both", "gr"):
        num(f"gpu@{k}@min", min(v[k] for v in H))
        num(f"gpu@{k}@max", max(v[k] for v in H))
    num("gpu@cyrhigher", sum(v["C"] > v["L"] for v in H), 0)
    num("n@models@all", len({k for k, _ in cruns}) + len(held), 0)
    # The text says that every larger model loses more where only the grammatical member has a new letter.
    assert min(v["gr"] for v in H) > max(v["both"] for v in H), "revise the text on the reform asymmetry of the larger models"
    num("gpu@post", sum(bool(m.get("post")) for m in held), 0)
    num("gpu@bf16", sum(m["dtype"] == "bfloat16" for m in held), 0)
    # The length fallback across the GPU runs, measured as for the CPU runs.
    prof = [gpu_length_profile(gruns[(m["key"], a)]) for m in held for a in ALPHABETS]
    num("lencorr@gpu@rho", float(pd.Series([q[0] for q in prof]).rank().corr(pd.Series([q[1] for q in prof]).rank())), 2)
    num("lencorr@gpu@n", len(prof), 0)
    # Checks of the GPU run: its Qwen2.5-1.5B run against our CPU run (all pairs), our CPU re-scoring of samples,
    # and its float32-against-bfloat16 control on Qwen3.5-9B-Base.
    stem = {"Latin": "latn", "Cyrillic": "cyrl", "Reformed": "latn_reformed"}
    diffs, agree, total = [], 0, 0
    for a in ALPHABETS:
        f = ROOT / "results" / "gpu_runs" / "check" / f"Qwen__Qwen2.5-1.5B__{stem[a]}__logprob.csv"
        if f.exists() and ("Qwen2.5-1.5B", a) in cruns:
            g, c = pd.read_csv(f).set_index("id"), cruns[("Qwen2.5-1.5B", a)]
            c = c.loc[g.index]
            diffs += [(g.good_logprob - c.good_logprob).abs().max(), (g.bad_logprob - c.bad_logprob).abs().max()]
            agree += int((ok(g) == ok(c)).sum())
            total += len(g)
    if diffs:
        num("gpu@check@maxdiff", max(diffs), 3)
        num("gpu@check@agree", agree, 0)
        num("gpu@check@n", total, 0)
    rc = [pd.read_csv(f) for f in sorted((ROOT / "results" / "gpu_runs").glob("cpu_recheck_*.csv"))]
    if rc:
        r = pd.concat(rc)
        dd = pd.concat([(r.good_logprob_cpu - r.good_logprob_gpu).abs(), (r.bad_logprob_cpu - r.bad_logprob_gpu).abs()])
        num("gpu@recheck@maxdiff", dd.max(), 2)
        num("gpu@recheck@n", len(r), 0)
        num("gpu@recheck@agree", int((r.correct_cpu == r.correct_gpu).sum()), 0)
        num("gpu@recheck@models", len(rc), 0)
    flips, accdiff = [], []
    for a in ALPHABETS:
        f = ROOT / "results" / "gpu_runs" / "bf16check" / f"Qwen__Qwen3.5-9B-Base__{stem[a]}__logprob.csv"
        if f.exists() and ("Qwen3.5-9B", a) in gruns:
            b16, f32 = pd.read_csv(f).set_index("id"), gruns[("Qwen3.5-9B", a)]
            f32 = f32.loc[b16.index]
            flips.append(100 * (ok(b16) != ok(f32)).mean())
            accdiff.append(abs(acc(b16) - acc(f32)))
    if flips:
        num("gpu@bf16@flips@min", min(flips))
        num("gpu@bf16@flips@max", max(flips))
        num("gpu@bf16@accdiff@max", max(accdiff))
        # The text says the two precisions give the same accuracy to one decimal.
        assert all(round(d, 6) < 0.05 for d in accdiff), "revise the text on the bfloat16 control"
    # Tomaris.ai: overlap of its pretraining corpus with the benchmark, and its accuracy by source.
    ov = ROOT / "results" / "gpu_runs" / "tomaris_overlap_v1.2.json"
    if ov.exists() and rest:
        seen = set(json.loads(ov.read_text(encoding="utf-8"))["loose_ids"])
        for src, name in (("corpus", "own"), ("books", "books")):
            ids = bench.index[bench.source == src]
            num(f"tom@{name}@n", len(ids), 0)
            num(f"tom@{name}@seen", sum(i in seen for i in ids), 0)
            num(f"tom@{name}@pct", 100 * sum(i in seen for i in ids) / len(ids))
        num("tom@all@pct", 100 * len(seen & set(bench.index)) / len(bench))
        L = gruns[(rest[0]["key"], "Latin")].join(bench[["source"]])
        num("tom@L@own", acc(L[L.source == "corpus"]))
        num("tom@L@books", acc(L[L.source == "books"]))
    # The appendix table.
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\setlength{\tabcolsep}{5pt}", r"\begin{tabular}{@{}lrlrrrrr@{}}", r"\toprule",
             r" & & & & & & \multicolumn{2}{c}{Ref.: change} \\", r"\cmidrule(l){7-8}",
             r"Model & Parameters & Precision & Latin & Cyr. & Ref. & both & gr. \\", r"\midrule"]
    def row(m):
        v = vals[m["key"]]
        name = label(m) + (r"$^\dagger$" if m.get("post") else "")
        prec = {"float32": "fp32", "bfloat16": "bf16"}[m["dtype"]]
        return (f"{name} & {m['params']} & {prec} & {v['L']:.1f} & {v['C']:.1f} & {v['R']:.1f} & "
                f"{sg(-v['both'])} & {sg(-v['gr'])} \\\\")
    lines += [row(m) for m in sorted(held, key=lambda m: -vals[m["key"]]["L"])]
    if rest:
        lines += [r"\midrule", r"\multicolumn{8}{@{}l}{\textit{Not held out: the authors' company's model}} \\"] + [row(m) for m in rest]
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Larger models, scored on GPUs: accuracy (\%) on all 2,400 pairs in current Latin, Cyrillic and reformed "
              r"Latin, and the change in points from current to reformed Latin for pairs whose new letters fall in the edited word "
              r"of \emph{both} members or of the \emph{gr}ammatical member only (as in Table~\ref{tab:reform}). fp32, bf16: 32-bit "
              r"and bfloat16 precision. $^\dagger$: post-trained checkpoint, scored like the others. Tomaris.ai is not comparable "
              r"with the other models (Appendix~\ref{app:large}).}", r"\label{tab:large}", r"\end{table*}"]
    return "\n".join(lines)


# --- human validation -------------------------------------------------------------------------------------

def human_judgments():
    """Released counts of the forced-choice validation (human_study/forced_choice_*.csv, written by
    scripts/human_study_report.py from the private sheets): per pair and per annotator; None if not run."""
    f = ROOT / "human_study" / "forced_choice_judgments.csv"
    if not f.exists():
        return None, None
    return pd.read_csv(f).set_index("pair_id"), pd.read_csv(ROOT / "human_study" / "forced_choice_annotators.csv")


def human_rows(judg):
    """Rows for the tables: mean accuracy of the annotators and majority-vote accuracy per phenomenon."""
    by = judg.groupby("phenomenon")
    mean = {ph: 100 * g.correct.sum() / g.annotators.sum() for ph, g in by}
    major = {ph: 100 * (2 * g.correct > g.annotators).mean() for ph, g in by}
    return [("Humans", mean, 100 * judg.correct.sum() / judg.annotators.sum()),
            ("Majority", major, 100 * (2 * judg.correct > judg.annotators).mean())]


def rating_numbers():
    """Size of the rating study (not yet run): pairs per list and per phenomenon, from its key."""
    f = ROOT / "human_study" / "ratings_key.csv"
    if f.exists():
        key = pd.read_csv(f)
        per_list = key.groupby("list").size()
        assert per_list.nunique() == 1, "the two rating lists must have the same length"
        num("rate@pairs", per_list.iloc[0], 0)
        num("rate@perphen", per_list.iloc[0] / key.phenomenon.nunique(), 0)


def human_numbers(judg, ann, runs, bench):
    from human_study_report import krippendorff_nominal
    words = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    NUM["hum@nword"] = words.get(len(ann), str(len(ann)))
    NUM["hum@Nword"] = NUM["hum@nword"].capitalize()
    NUM["hum@majword"] = words.get(len(ann) // 2 + 1, str(len(ann) // 2 + 1))
    assert ann.answered.eq(len(judg)).all() and judg.annotators.eq(len(ann)).all(), "every annotator must answer every pair"
    accs = sorted(100 * ann.correct / ann.answered)
    num("hum@pairs", len(judg), 0)
    num("hum@perphen", len(judg) / judg.phenomenon.nunique(), 0)
    num("hum@pctbench", 100 * len(judg) / len(bench), 0)
    num("hum@judgments", judg.annotators.sum(), 0)
    num("hum@min", accs[0])
    num("hum@max", accs[-1])
    num("hum@mean", 100 * judg.correct.sum() / judg.annotators.sum())
    num("hum@majority", (2 * judg.correct > judg.annotators).sum(), 0)
    wrong = judg.annotators - judg.correct
    # The text says that no pair was misjudged by more than one annotator; stop if the data say otherwise.
    assert wrong.max() <= 1, "a pair was misjudged by two or more annotators: revise the text of the human validation"
    num("hum@errpairs", (wrong > 0).sum(), 0)
    num("hum@unsure", judg.unsure.sum(), 0)
    num("hum@unsurepairs", (judg.unsure > 0).sum(), 0)
    num("hum@unsurewrong", judg.unsure_wrong.sum(), 0)
    other = {"A": "B", "B": "A"}
    units = [[r.grammatical] * r.correct + [other[r.grammatical]] * (r.annotators - r.correct) for r in judg.itertuples()]
    num("hum@alpha", krippendorff_nominal(units), 2)
    agree = [a == b for u in units for i, a in enumerate(u) for b in u[i + 1:]]
    num("hum@agree", 100 * sum(agree) / len(agree))
    low = min(human_rows(judg)[0][1].items(), key=lambda kv: kv[1])
    num("hum@low", low[1])
    for m in MODELS:
        df = runs.get((m["key"], own(m)))
        if df is not None:
            num(f"humacc@{m['key']}", acc(df[df.index.isin(judg.index)]))


def scripts_table(runs, stats):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}llrrr@{}}", r"\toprule",
             r"Model & Uzbek data & Latin & Cyr. & Ref. \\"]
    for group, models in groups(MODELS):
        rows = []
        for m in models:
            if (m["key"], "Latin") not in runs and (m["key"], "Cyrillic") not in runs:
                continue
            cells = []
            for a in ALPHABETS:
                df = runs.get((m["key"], a))
                if df is None:
                    cells.append("--")
                    continue
                v = acc(df)
                num(f"acc@{m['key']}@{a}", v)
                num(f"accnorm@{m['key']}@{a}", acc(df, "correct_norm"))
                lo, hi = wilson(int(ok(df).sum()), len(df))
                num(f"acclo@{m['key']}@{a}", lo)
                num(f"acchi@{m['key']}@{a}", hi)
                num(f"nerr@{m['key']}@{a}", int((~ok(df)).sum()), 0)
                for ph in SLUGS:
                    num(f"accph@{m['key']}@{a}@{ph}", acc(df[df.phenomenon == ph]))
                    num(f"nerrph@{m['key']}@{a}@{ph}", int((~ok(df[df.phenomenon == ph])).sum()), 0)
                cells.append(f"\\textbf{{{v:.1f}}}" if a == own(m) and m["trained"] in ("latn", "cyrl") else f"{v:.1f}")
            rows.append(f"{label(m)} & {TRAINED[m['trained']]} & " + " & ".join(cells) + r" \\")
            s = stats.get(m["key"], {})
            for a in ALPHABETS:
                if a in s:
                    num(f"unk@{m['key']}@{a}", s[a]["unk_pct"], 0)
                    num(f"tpw@{m['key']}@{a}", s[a]["tokens_per_word"], 2)
            if (m["key"], own(m)) in runs and (m["key"], other(m)) in runs:
                d, lo, hi, p, _, _, _ = paired(ok(runs[(m["key"], own(m))]), ok(runs[(m["key"], other(m))]))
                num(f"drop@{m['key']}", d)
                num(f"droplo@{m['key']}", lo)
                num(f"drophi@{m['key']}", hi)
                num(f"dropp@{m['key']}", pval(p))
        if rows:
            lines += [r"\midrule", rf"\multicolumn{{5}}{{@{{}}l}}{{\textit{{{group}}}}} \\"] + rows
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Accuracy (\%) on all 2,400 pairs in current Latin, Cyrillic and reformed Latin (Ref.); chance is 50. "
              r"GF-L, GF-C: Goldfish models trained on Latin-script and Cyrillic-script Uzbek. \emph{Uzbek data}: script of the "
              r"model's Uzbek training text. For models trained on one script the score in that script is in bold. "
              r"Reformed Latin is scored only when the tokenizer produces no unknown token on it "
              r"(Appendix~\ref{app:tokenizers}). The 95\% Wilson interval of a score is at most $\pm$2 points.}",
              r"\label{tab:scripts}", r"\end{table}"]
    return "\n".join(lines)


def matched_table(runs):
    rows, ps = [], []
    for size in SIZES:
        a, b = runs.get((f"GF-L {size}", "Latin")), runs.get((f"GF-C {size}", "Cyrillic"))
        if a is None or b is None:
            continue
        d, lo, hi, p, _, n10, n01 = paired(ok(a), ok(b))
        rows.append((size, acc(a), acc(b), d, lo, hi, p))
        ps.append(p)
    adj = holm(ps)
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
             r"Data & Latin & Cyr. & $\Delta$ & 95\% CI & $p$ \\", r"\midrule"]
    for (size, la, cy, d, lo, hi, p), pa in zip(rows, adj):
        for k, v in (("lat", la), ("cyr", cy), ("diff", d), ("lo", lo), ("hi", hi)):
            num(f"match@{size}@{k}", v)
        num(f"match@{size}@p", pval(pa))
        lines.append(f"{size} & {la:.1f} & {cy:.1f} & {sg(d)} & [{sg(lo)}, {sg(hi)}] & {pval(pa)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Script-matched Goldfish models of the same training-data size: the Latin model on Latin text against "
              r"the Cyrillic model on Cyrillic text, on the same 2,400 pairs. $\Delta$: difference in points with a bootstrap "
              r"95\% interval (not adjusted for multiple comparisons); $p$: exact McNemar test, Holm-adjusted over the four sizes.}",
              r"\label{tab:matched}", r"\end{table}"]
    return "\n".join(lines)


def length_table(runs, conditions, name, caption):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r"Model & Text & fewer & same & more & $\Delta$ \\", r"\midrule"]
    for key, a in conditions:
        df = runs.get((key, a))
        if df is None:
            continue
        dtok = df.bad_ntok - df.good_ntok
        cells = [acc(df[mask]) if mask.sum() else float("nan") for mask in (dtok < 0, dtok == 0, dtok > 0)]
        for k, v, mask in zip(("fewer", "same", "more"), cells, (dtok < 0, dtok == 0, dtok > 0)):
            num(f"len@{key}@{a}@{k}", v)
            num(f"len@{key}@{a}@n{k}", int(mask.sum()), 0)
        gap = cells[2] - cells[0]
        num(f"len@{key}@{a}@gap", gap)
        lines.append(f"{label(key)} & {a} & " + " & ".join("--" if np.isnan(c) else f"{c:.1f}" for c in cells) +
                     (" & --" if np.isnan(gap) else f" & {sg(gap)}") + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", rf"\caption{{{caption}}}", rf"\label{{tab:{name}}}", r"\end{table}"]
    return "\n".join(lines)


def length_all_table(runs):
    """Length effect for every run: one row per model, the three alphabets side by side."""
    lines = [r"\begin{table*}[t]", r"\centering\footnotesize", r"\setlength{\tabcolsep}{3.4pt}",
             r"\begin{tabular}{@{}l" + "rrrr" * len(ALPHABETS) + "@{}}", r"\toprule",
             " & " + " & ".join(rf"\multicolumn{{4}}{{c}}{{{name}}}" for name in ("Current Latin", "Cyrillic", "Reformed Latin")) + r" \\",
             r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}\cmidrule(l){10-13}",
             "Model" + r" & fewer & same & more & $\Delta$" * len(ALPHABETS) + r" \\"]
    for group, models in groups(MODELS):
        rows = []
        for m in models:
            if not any((m["key"], a) in runs for a in ALPHABETS):
                continue
            cells = []
            for a in ALPHABETS:
                df = runs.get((m["key"], a))
                if df is None:
                    cells += ["--"] * 4
                    continue
                dtok = df.bad_ntok - df.good_ntok
                masks = (dtok < 0, dtok == 0, dtok > 0)
                values = [acc(df[mask]) if mask.sum() else float("nan") for mask in masks]
                for k, v, mask in zip(("fewer", "same", "more"), values, masks):
                    num(f"len@{m['key']}@{a}@{k}", v)
                    num(f"len@{m['key']}@{a}@n{k}", int(mask.sum()), 0)
                gap = values[2] - values[0]
                num(f"len@{m['key']}@{a}@gap", gap)
                cells += ["--" if np.isnan(v) else f"{v:.1f}" for v in values] + ["--" if np.isnan(gap) else sg(gap)]
            rows.append(f"{label(m)} & " + " & ".join(cells) + r" \\")
        if rows:
            lines += [r"\midrule", rf"\multicolumn{{13}}{{@{{}}l}}{{\textit{{{group}}}}} \\"] + rows
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Length effect for every scored run: accuracy (\%) on the pairs whose ungrammatical member has fewer, "
              r"the same number of, or more tokens than the grammatical one under the model's own tokenizer, and the difference "
              r"$\Delta$ between \emph{more} and \emph{fewer} (0 means no length effect).}",
              r"\label{tab:lengthall}", r"\end{table*}"]
    return "\n".join(lines)


def models_table(runs):
    kind = {"logprob": "autoregressive", "pll": "masked"}
    scored = {k for k, _ in runs}
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lllrl@{}}", r"\toprule",
             r"Model & Hugging Face identifier & Type & Parameters & Uzbek training text \\"]
    for group, models in groups(MODELS):
        models = [m for m in models if m["key"] in scored]
        if not models:
            continue
        lines += [r"\midrule", rf"\multicolumn{{5}}{{@{{}}l}}{{\textit{{{group}}}}} \\"]
        for m in models:
            name = label(m) + (r"$^\dagger$" if m.get("post") else "")
            lines.append(f"{name} & \\texttt{{{tex(m['hf'])}}} & {kind[m['method']]} & {m['params']} & {TRAINED[m['trained']]} \\\\")
    # Licences, as stated on the models' Hugging Face pages: the most common one, and the exceptions by name.
    lic = Counter(m["license"] for m in MODELS if m["key"] in scored)
    main_lic = lic.most_common(1)[0][0]
    others = defaultdict(list)
    for m in MODELS:
        if m["key"] in scored and m["license"] != main_lic:
            others[m["license"]].append(label(m))
    def names(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
    exceptions = [f"{names(v)} ({k})" for k, v in others.items()]
    licence_note = (f" Licences, as stated on the models' Hugging Face pages: {main_lic}"
                    + (", except " + "; ".join(exceptions) if exceptions else "") + ".")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{The evaluated models. GF-L, GF-C: Goldfish models trained on Latin-script and Cyrillic-script Uzbek. Parameter counts are those given by the models' authors or on the Hugging Face Hub. \emph{Uzbek training "
              r"text}: script of the Uzbek text a model was trained on; multilingual models are trained on many languages in "
              r"several scripts. The larger models were scored on GPUs (Appendix~\ref{app:large}); $^\dagger$: post-trained "
              r"checkpoint, scored like the others." + licence_note + "}", r"\label{tab:models}", r"\end{table*}"]
    return "\n".join(lines)


def reform_table(runs, bench):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.2pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r" & & & \multicolumn{4}{c}{Change in points} \\", r"\cmidrule(l){4-7}",
             r"Model & Cur. & Ref. & both & gr. & other & none \\", r"\midrule"]
    for m in MODELS:
        cur, ref = runs.get((m["key"], "Latin")), runs.get((m["key"], "Reformed"))
        if cur is None or ref is None:
            continue
        cells = []
        for g, _ in REFORM_GROUPS:
            ids = bench.index[bench.reform_group == g]
            c, r = acc(cur.loc[ids]), acc(ref.loc[ids])
            num(f"ref@{m['key']}@{g}@cur", c)
            num(f"ref@{m['key']}@{g}@ref", r)
            num(f"ref@{m['key']}@{g}@delta", r - c)
            num(f"ref@{m['key']}@{g}@loss", c - r)
            cells.append(sg(r - c))
        # The same groups within each phenomenon that has at least ten pairs in the group: the grammatical-only
        # group is mostly binding, so the text compares the groups within stem alternation and nominalisation.
        for g in ("critical word: both", "critical word: grammatical only"):
            for ph, ids in bench[bench.reform_group == g].groupby("phenomenon").groups.items():
                if len(ids) >= 10:
                    c, r = acc(cur.loc[ids]), acc(ref.loc[ids])
                    num(f"refph@{m['key']}@{g}@{ph}@cur", c)
                    num(f"refph@{m['key']}@{g}@{ph}@ref", r)
                    num(f"refph@{m['key']}@{g}@{ph}@loss", c - r)
                    num(f"refphn@{g}@{ph}", len(ids), 0)
        d, lo, hi, p, _, _, _ = paired(ok(cur), ok(ref))
        num(f"ref@{m['key']}@all@delta", -d)
        num(f"ref@{m['key']}@all@loss", d)
        num(f"ref@{m['key']}@all@lo", -hi)
        num(f"ref@{m['key']}@all@hi", -lo)
        num(f"ref@{m['key']}@all@p", pval(p))
        lines.append(f"{label(m)} & {acc(cur):.1f} & {acc(ref):.1f} & " + " & ".join(cells) + r" \\")
    for g, _ in REFORM_GROUPS:
        num(f"refn@{g}", int((bench.reform_group == g).sum()), 0)
    n = [f"{int((bench.reform_group == g).sum()):,}".replace(",", "{,}") for g, _ in REFORM_GROUPS]
    lines += [r"\bottomrule", r"\end{tabular}",
              rf"\caption{{Current against reformed Latin for the models whose tokenizer covers the new letters: accuracy (\%) "
              rf"on all pairs, and the change in points for pairs whose new letters (\"o, \u{{g}}, \c{{s}}, \c{{c}}) fall in "
              rf"the edited word of \emph{{both}} members ($n={n[0]}$), in the edited word of the \emph{{gr}}ammatical member "
              rf"only ($n={n[1]}$), only in \emph{{other}} words ($n={n[2]}$), or nowhere ($n={n[3]}$).}}",
              r"\label{tab:reform}", r"\end{table}"]
    return "\n".join(lines)


def tokenizer_table(stats, runs):
    scored = {k for k, _ in runs}
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r" & \multicolumn{3}{c}{Unknown (\%)} & \multicolumn{3}{c}{Tokens per word} \\", r"\cmidrule(lr){2-4}\cmidrule(l){5-7}",
             r"Model & Lat. & Cyr. & Ref. & Lat. & Cyr. & Ref. \\", r"\midrule"]
    for m in MODELS:
        s = stats.get(m["key"])
        if s and m["key"] in scored:
            lines.append(f"{label(m)} & " + " & ".join(f"{s[a]['unk_pct']:.0f}" for a in ALPHABETS) + " & " +
                         " & ".join(f"{s[a]['tokens_per_word']:.2f}" for a in ALPHABETS) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Tokenizer statistics on the 4,800 sentences of each alphabet: share of sentences with at least one "
              r"unknown token, and mean number of tokens per word.}", r"\label{tab:tokenizers}", r"\end{table}"]
    return "\n".join(lines)


def accnorm_table(runs):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r" & \multicolumn{2}{c}{Latin} & \multicolumn{2}{c}{Cyrillic} & \multicolumn{2}{c}{Reformed} \\",
             r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(l){6-7}", r"Model & acc & norm & acc & norm & acc & norm \\", r"\midrule"]
    for m in MODELS:
        if not any((m["key"], a) in runs for a in ALPHABETS):
            continue
        cells = []
        for a in ALPHABETS:
            df = runs.get((m["key"], a))
            cells += ["--", "--"] if df is None else [f"{acc(df):.1f}", f"{acc(df, 'correct_norm'):.1f}"]
        lines.append(f"{label(m)} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Raw accuracy (acc) and byte-normalised accuracy (norm; log-probability per UTF-8 byte, the main "
              r"metric of TatBLiMP), in \%.}", r"\label{tab:accnorm}", r"\end{table}"]
    return "\n".join(lines)


def pilot_table():
    names = {"anthropic__claude-sonnet-5.5": "Claude Sonnet 5.5", "google__gemini-4-argon": "Gemini 4 Argon",
             "openai__gpt-6.1-sol": "GPT-6.1 Sol", "google__gemma-3-12b-it": "Gemma-3-12B-it",
             "meta-llama__llama-3.3-70b-instruct": "Llama-3.3-70B-Instruct", "qwen__qwen-2.5-7b-instruct": "Qwen2.5-7B-Instruct",
             "meta-llama__llama-3.1-8b-instruct": "Llama-3.1-8B-Instruct"}
    rows = []
    for f in glob.glob(str(ROOT / "results" / "api_*_pilot3.csv")):
        d = pd.read_csv(f)
        key = Path(f).name[len("api_"):].split("_uzblimp")[0]
        rows.append((names.get(key, key), 100 * d.accuracy.mean(), 100 * d.consistent.astype(str).eq("True").mean(), len(d)))
    rows.sort(key=lambda r: -r[1])
    lines = [r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{@{}lrr@{}}", r"\toprule",
             r"Model & Accuracy & Consistent \\", r"\midrule"]
    for name, a, c, n in rows:
        num(f"pilot@{name}", a)
        lines.append(f"{name} & {a:.1f} & {c:.1f} \\\\")
    num("pilot@n", rows[0][3] if rows else 0, 0)
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Forced-choice pilot with chat models on 48 pairs in current Latin (three per phenomenon). Each pair "
              r"is shown in both orders; \emph{Accuracy} counts both orders, \emph{Consistent} the pairs answered correctly in "
              r"both.}", r"\label{tab:pilot}", r"\end{table}"]
    return "\n".join(lines)


def misc_numbers(bench, runs, generated, reviewed, accepted):
    num("n@pairs", len(bench), 0)
    num("n@generated", sum(generated.values()), 0)
    num("n@reviewed", sum(reviewed.values()), 0)
    num("n@accepted", sum(accepted.values()), 0)
    num("pct@accepted", 100 * sum(accepted.values()) / sum(reviewed.values()))
    rates = [100 * accepted[ph] / reviewed[ph] for ph in SLUGS]
    num("accept@min", min(rates), 0)
    num("accept@max", max(rates), 0)
    num("n@reserve", len(read_tsv(ROOT / "data/benchmark/reserve.tsv")), 0)
    num("n@corpus", int((bench.source == "corpus").sum()), 0)
    num("n@books", int((bench.source == "books").sum()), 0)
    words = bench.grammatical.map(n_words)  # word tokens, without punctuation
    num("words@mean", words.mean())
    num("words@min", int(words.min()), 0)
    num("words@max", int(words.max()), 0)
    # Pairs replaced since benchmark v1.1 (ids of a v1.1 result file), and the excluded pairs by the pass
    # that found them: the audit of generator errors and the screen for spelling errors in source sentences.
    excluded = read_tsv(ROOT / "data/benchmark/excluded.tsv")
    v11 = set(pd.read_csv(ROOT / "results" / "uzn_latn_100mb_uzblimp_v1.1.csv").id)
    replaced = len(v11 - set(bench.index))
    num("n@replaced", replaced, 0)
    num("pct@replaced", 100 * replaced / len(bench))
    num("n@excluded", len(excluded), 0)
    spelling = sum("spelling" in r["flagged_by"] for r in excluded)
    num("n@excluded@spelling", spelling, 0)
    num("n@excluded@audit", len(excluded) - spelling, 0)
    num("n@excluded@reserve", len(excluded) - replaced, 0)
    # Pairs that at least three of the six strongest runs (each model on its own script) judge wrong.
    strongest = [("tahrirchi-bert", "Latin"), ("GF-L full", "Latin"), ("GF-L 100MB", "Latin"),
                 ("GF-C full", "Cyrillic"), ("GF-C 100MB", "Cyrillic"), ("UzRoBERTa", "Cyrillic")]
    if all(k in runs for k in strongest):
        wrong = sum((~ok(runs[k])).astype(int) for k in strongest)
        hard = bench.loc[wrong.index[wrong >= 3]]
        num("hard@n", len(hard), 0)
        num("hard@none", int((wrong == 0).sum()), 0)
        morph = int(hard.phenomenon.isin(["dative_allomorphy", "stem_alternation"]).sum())
        num("hard@morph", morph, 0)
        num("hard@binding", int((hard.phenomenon == "binding").sum()), 0)
        rest = hard[~hard.phenomenon.isin(["dative_allomorphy", "stem_alternation", "binding"])]
        num("hard@other", len(rest), 0)
        num("hard@otherphen", rest.phenomenon.nunique(), 0)
        num("hard@all", int((wrong == len(strongest)).sum()), 0)
        assert list(wrong.index[wrong == len(strongest)]) == ["dative_allomorphy-1028"]  # the example named in the text
    norm = bench.grammatical.str.lower().str.replace(r"[^\w]+", " ", regex=True).str.strip()
    dup = bench[norm.duplicated(keep=False)].assign(norm=norm)
    within = sum(g.phenomenon.nunique() == 1 for _, g in dup.groupby("norm"))
    num("n@dupwithin", within, 0)
    num("n@dupacross", dup.norm.nunique() - within, 0)
    num("n@models", len({k for k, _ in runs}), 0)
    num("n@runs", len(runs), 0)
    num("accnorm@maxchange", max(abs(acc(df, "correct_norm") - acc(df)) for df in runs.values()), 0)
    for name, mask in (("longer", bench.dbytes > 0), ("equal", bench.dbytes == 0), ("shorter", bench.dbytes < 0)):
        num(f"nbytes@{name}", int(mask.sum()), 0)
    # Length alone as a baseline: always prefer the member with fewer (or more) bytes; ties split evenly.
    longer, equal, shorter = (int(m.sum()) for m in (bench.dbytes > 0, bench.dbytes == 0, bench.dbytes < 0))
    num("base@shorter", 100 * (longer + equal / 2) / len(bench))
    num("base@longer", 100 * (shorter + equal / 2) / len(bench))
    cyr = {r["id"]: len(r["ungrammatical"].encode()) - len(r["grammatical"].encode())
           for r in read_tsv(ROOT / "data/benchmark/uzblimp_cyrl.tsv")}
    db = pd.Series(cyr)
    num("base@shorter@Cyrillic", 100 * (int((db > 0).sum()) + int((db == 0).sum()) / 2) / len(db))
    num("base@longer@Cyrillic", 100 * (int((db < 0).sum()) + int((db == 0).sum()) / 2) / len(db))
    mixed = [ph for ph in SLUGS if bench[bench.phenomenon == ph].source.nunique() == 2]
    num("n@mixedphen", len(mixed), 0)
    for key in ("GF-L 100MB", "GF-L full", "tahrirchi-bert", "BERTbek"):
        df = runs.get((key, "Latin"))
        if df is not None:
            d = df[df.phenomenon.isin(mixed)].join(bench[["source"]])
            num(f"source@{key}@corpus", acc(d[d.source == "corpus"]))
            num(f"source@{key}@books", acc(d[d.source == "books"]))
    # Uzbek models trained on one script: what they lose on the other script, and the best score in each script.
    single = [m for m in MODELS if m["trained"] in ("latn", "cyrl") and (m["key"], own(m)) in runs and (m["key"], other(m)) in runs]
    drops = [acc(runs[(m["key"], own(m))]) - acc(runs[(m["key"], other(m))]) for m in single]
    num("n@single", len(single), 0)
    num("drop@min", min(drops))
    num("drop@max", max(drops))
    for a in ("Latin", "Cyrillic"):
        num(f"best@{a}", max(acc(df) for (key, alphabet), df in runs.items() if alphabet == a))
    # Length effect against competence across runs: accuracy on pairs whose members have the same number of
    # tokens (no length cue) against the gap (accuracy where the ungrammatical member has more tokens minus
    # where it has fewer); Spearman correlation over all complete runs, with and without the binding pairs,
    # whose ungrammatical member is shorter in every Latin pair.
    def length_profile(df):
        d = df.bad_ntok - df.good_ntok
        good = ok(df)
        return 100 * good[d == 0].mean(), 100 * (good[d > 0].mean() - good[d < 0].mean())

    def spearman(x, y):
        return float(pd.Series(x).rank().corr(pd.Series(y).rank()))

    for name, keep in (("all", lambda df: df), ("nobind", lambda df: df[df.phenomenon != "binding"]),
                       ("nobn", lambda df: df[~df.phenomenon.isin(["binding", "npi_hech"])])):
        prof = [length_profile(keep(df)) for df in runs.values()]
        num(f"lencorr@{name}@rho", spearman([p[0] for p in prof], [p[1] for p in prof]), 2)
    num("lencorr@n", len(runs), 0)
    for key, a in (("tahrirchi-bert", "Cyrillic"), ("tahrirchi-bert", "Reformed"), ("GF-L full", "Cyrillic"),
                   ("UzBERT", "Cyrillic"), ("XLM-R base", "Latin"), ("mBERT", "Latin")):
        if (key, a) in runs:
            df = runs[(key, a)]
            num(f"lennb@{key}@{a}@gap", length_profile(df[df.phenomenon != "binding"])[1])
            num(f"lennbn@{key}@{a}@gap", length_profile(df[~df.phenomenon.isin(["binding", "npi_hech"])])[1])
    # Byte normalisation and the length gap: the gap in byte-normalised accuracy for every run, and how often
    # normalisation shrinks or reverses a gap of more than ten points.
    big = shrunk = reversed_ = stillbig = 0
    for (key, a), df in runs.items():
        d = df.bad_ntok - df.good_ntok
        raw, nrm = ok(df), df.correct_norm.astype(str).eq("True")
        g_raw = 100 * (raw[d > 0].mean() - raw[d < 0].mean())
        g_nrm = 100 * (nrm[d > 0].mean() - nrm[d < 0].mean())
        num(f"lennorm@{key}@{a}@gap", g_nrm)
        if g_raw > 10:
            big += 1
            shrunk += int(abs(g_nrm) < g_raw)
            reversed_ += int(g_nrm < 0)
            stillbig += int(abs(g_nrm) > 10)
    num("lennorm@n@big", big, 0)
    num("lennorm@n@shrunk", shrunk, 0)
    num("lennorm@n@reversed", reversed_, 0)
    num("lennorm@n@stillbig", stillbig, 0)
    ties = sum(int((df["diff"] == 0).sum()) for df in runs.values())
    num("n@ties", ties, 0)
    old = {r["id"]: r for r in read_tsv(ROOT / "data/benchmark/uzblimp_cyrl.tsv")}
    strip = ".,!?;:«»\"()…—-"
    num("n@cyrlwords", len({w.strip(strip) for r in old.values() for w in (r["grammatical"] + " " + r["ungrammatical"]).lower().split()} - {""}), 0)
    # Distinct word forms of the benchmark whose Cyrillic spelling comes from the loanword tables of the audit.
    from alphabets import to_cyrillic
    latin = {w.strip(strip) for r in bench.itertuples() for w in (r.grammatical + " " + r.ungrammatical).split()} - {""}
    fixed = {w for w in latin if to_cyrillic(w) != to_cyrillic(w, loan_tables=False)}
    num("n@loanforms", len({w.lower() for w in fixed}), 0)


SMALL = {"GF-L 5MB", "GF-L 10MB", "GF-L 100MB", "GF-C 5MB", "GF-C 10MB", "GF-C 100MB"}  # in the appendix table only
MAIN_CAPTION = (r"Accuracy (\%) per phenomenon, each model on text in the script of its Uzbek training data "
                r"(L: current Latin, C: Cyrillic). GF-L, GF-C: Goldfish models trained on Latin-script and "
                r"Cyrillic-script Uzbek. Cells below chance (50) are shaded. Column "
                r"labels abbreviate the phenomena of Table~\ref{tab:phenomena} in the same order. With 150 pairs per cell, the "
                r"95\% Wilson interval is at most $\pm$8 points. The Goldfish models trained on less data and the multilingual "
                r"models are in Table~\ref{tab:ownall} in the appendix.")
TRAINED_BY_KEY = {m["key"]: m["trained"] for m in MODELS}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bench = benchmark()
    runs = load_runs(VERSION)
    # The paper reports a model only when both its Latin and its Cyrillic run are complete.
    both = {k for k, a in runs if a == "Latin"} & {k for k, a in runs if a == "Cyrillic"}
    left_out = sorted({k for k, _ in runs} - both)
    runs = {key: df for key, df in runs.items() if key[0] in both}
    # The larger models scored on GPUs have their own table and numbers; every other table and number is about
    # the models we scored on CPU.
    gpu_keys = {m["key"] for m in MODELS if m.get("setup") == "gpu"}
    all_runs = runs
    gpu_runs = {key: df for key, df in runs.items() if key[0] in gpu_keys}
    runs = {key: df for key, df in runs.items() if key[0] not in gpu_keys}
    if left_out:
        print(f"left out until both the Latin and the Cyrillic run are complete: {', '.join(left_out)}")
    stats_file = ROOT / "results" / "tokenizer_stats.json"
    stats = json.loads(stats_file.read_text(encoding="utf-8")) if stats_file.exists() else {}
    ex = read_examples(bench)
    generated, reviewed, accepted, reasons = review_counts()
    selected = [("GF-L full", "Latin"), ("GF-L full", "Cyrillic"), ("GF-C full", "Cyrillic"), ("GF-C full", "Latin"),
                ("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Cyrillic"), ("tahrirchi-bert", "Reformed"),
                ("UzBERT", "Cyrillic"), ("UzBERT", "Latin"), ("XLM-R base", "Latin"), ("XLM-R base", "Cyrillic"),
                ("Qwen2.5-0.5B", "Latin"), ("Qwen2.5-0.5B", "Cyrillic")]
    delta_note = r"$\Delta$: accuracy on pairs with more tokens minus accuracy on pairs with fewer; 0 means no length effect."
    tables = {
        "phenomena": phenomena_table(bench, ex),
        "glosses": glosses(ex),
        "alphabets": alphabets_table(ex),
        "stats": stats_table(bench, reviewed, accepted),
        "reasons": reasons_table(reasons),
        "main": per_phenomenon_table(
            {k: v for k, v in runs.items() if k[0] not in SMALL and TRAINED_BY_KEY[k[0]] != "multi"}, own,
            MAIN_CAPTION, "tab:main"),
        "ownall": per_phenomenon_table(
            runs, own, r"Accuracy (\%) per phenomenon for every model, each on text in the script of its Uzbek training "
            r"data (L: current Latin, C: Cyrillic; multilingual models on Latin), as in Table~\ref{tab:main}. Cells below "
            r"chance are shaded.", "tab:ownall"),
        "otherscript": per_phenomenon_table(
            runs, other, r"Accuracy (\%) per phenomenon on the \emph{other} script: Cyrillic text for models trained on "
            r"Latin-script Uzbek and for multilingual models, Latin text for models trained on Cyrillic. Cells below chance "
            r"are shaded.", "tab:otherscript"),
        "reformedphen": per_phenomenon_table(
            runs, lambda m: "Reformed", r"Accuracy (\%) per phenomenon on reformed Latin (R), for the models whose "
            r"tokenizer covers the new letters. Cells below chance are shaded.", "tab:reformedphen"),
        "scripts": scripts_table(runs, stats),
        "matched": matched_table(runs),
        "length": length_table(runs, selected, "length",
                               r"Accuracy (\%) by whether the ungrammatical member has fewer, the same number of, or more "
                               r"tokens than the grammatical one under the model's own tokenizer. " + delta_note),
        "lengthall": length_all_table(runs),
        "reform": reform_table(runs, bench),
        "models": models_table(all_runs),
        "tokenizers": tokenizer_table(stats, runs),
        "accnorm": accnorm_table(runs),
        "pilot": pilot_table(),
    }
    rating_numbers()
    if gpu_runs:
        tables["large"] = gpu_block(gpu_runs, runs, bench)
    judg, ann = human_judgments()
    if judg is not None:
        human_numbers(judg, ann, runs, bench)
        main_models = [m for m in MODELS if m["key"] not in SMALL and m["trained"] != "multi"]
        tables["main"] = per_phenomenon_table(
            {k: v for k, v in runs.items() if k[0] not in SMALL and TRAINED_BY_KEY[k[0]] != "multi"}, own,
            MAIN_CAPTION + rf" \emph{{Humans}}: mean accuracy of {NUM['hum@nword']} native speakers on a sample of "
            rf"{NUM['hum@perphen']} pairs per phenomenon (\S\ref{{sec:creation}}).", "tab:main",
            extra=human_rows(judg)[:1])
        rows = human_rows(judg)
        unanimous = rows[1][2] == 100  # the majority chose the grammatical sentence in every pair: say so instead of a row of 100s
        majority = (rf" The majority of the annotators (at least {NUM['hum@majword']}) chose the grammatical sentence in every pair."
                    if unanimous else rf" \emph{{Majority}}: share of pairs on which at least {NUM['hum@majword']} annotators "
                    r"chose the grammatical sentence.")
        tables["human"] = per_phenomenon_table(
            runs, own, rf"Human validation: accuracy (\%) on the {NUM['hum@pairs']} pairs judged by the annotators, "
            rf"{NUM['hum@perphen']} per phenomenon. \emph{{Humans}}: mean accuracy of the {NUM['hum@nword']} "
            r"annotators; models of Table~\ref{tab:main} on the same pairs, each on text in the script of its Uzbek "
            r"training data (L: current Latin, C: Cyrillic)." + majority,
            "tab:human", extra=rows[:1] if unanimous else rows, pairs=set(judg.index), models=main_models,
            digits=0)  # 20 pairs and 100 human judgments per phenomenon: every cell is a whole number
    misc_numbers(bench, runs, generated, reviewed, accepted)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in tables.items():
        (OUT / f"{name}.tex").write_text(text + "\n", encoding="utf-8")
    lines = ["% Generated by scripts/paper_tables.py; read in the text with \\Num{key}.", r"\makeatletter"]
    lines += [f"\\@namedef{{uzb@{k}}}{{{v}}}" for k, v in sorted(NUM.items())]
    lines.append(r"\makeatother")
    (OUT / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for old in ("accuracy", "examples", "tokens", "reformphen"):  # tables of the earlier draft
        (OUT / f"{old}.tex").unlink(missing_ok=True)
    print(f"wrote {len(tables)} tables and {len(NUM)} numbers to paper/tables/ ({len(runs)} runs, benchmark {VERSION})")


if __name__ == "__main__":
    main()
