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
from schema import n_words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "tables"
NAME = {p[0]: p[1] for p in PHENOMENA}
SHORT = {p[0]: p[2] for p in PHENOMENA}
LAYER = {p[0]: p[3] for p in PHENOMENA}
SIZES = ["5MB", "10MB", "100MB", "full"]
TRAINED = {"latn": "Latin", "cyrl": "Cyrillic", "both": "both", "multi": "multilingual"}
REFORM_GROUPS = [("critical word: both", "Edited word, both members"),
                 ("critical word: grammatical only", "Edited word, grammatical member only"),
                 ("only other words changed", "Other words only"), ("unchanged", "No new letter")]
NUM = {}


def num(key, value, digits=1):
    """Register a number for the text; whole numbers get a thousands separator."""
    NUM[key] = value if isinstance(value, str) else f"{value:,.0f}" if digits == 0 else f"{value:.{digits}f}"


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
    return 100 * df[col].astype(str).eq("True").mean()


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
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{@{}lp{7.7cm}p{5.5cm}@{}}", r"\toprule",
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
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{@{}p{5.1cm}p{5.4cm}p{5.1cm}@{}}", r"\toprule",
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
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r"Phenomenon & Corp. & Books & Words & Forms & $\Delta$B & Acc. \\", r"\midrule"]
    for ph in SLUGS:
        d = bench[bench.phenomenon == ph]
        forms = {w.lower().strip(".,!?") for g, u in zip(d.grammatical, d.ungrammatical) for w in changed_words(g, u)[0]}
        rate = 100 * accepted[ph] / reviewed[ph]
        num(f"forms@{ph}", len(forms), 0)
        num(f"dbytes@{ph}", d.dbytes.mean())
        num(f"accept@{ph}", rate, 0)
        lines.append(f"{NAME[ph]} & {(d.source == 'corpus').sum()} & {(d.source == 'books').sum()} & {d.words.mean():.1f} & "
                     f"{len(forms)} & {d.dbytes.mean():+.1f} & {rate:.0f} \\\\")
    lines += [r"\midrule", f"All & {(bench.source == 'corpus').sum()} & {(bench.source == 'books').sum()} & "
              f"{bench.words.mean():.1f} & & {bench.dbytes.mean():+.1f} & {100 * sum(accepted.values()) / sum(reviewed.values()):.0f} \\\\",
              r"\bottomrule", r"\end{tabular}",
              r"\caption{Benchmark statistics. \emph{Corp./Books}: pairs whose sentence comes from our corpus or from UzBooks; "
              r"\emph{Words}: mean length of the grammatical sentence; \emph{Forms}: distinct grammatical word forms at the "
              r"edited position; $\Delta$\emph{B}: mean length of the ungrammatical minus the grammatical sentence in UTF-8 "
              r"bytes; \emph{Acc.}: share (\%) of reviewed candidates accepted in the native-speaker review.}",
              r"\label{tab:stats}", r"\end{table}"]
    return "\n".join(lines)


def reasons_table(reasons):
    cols = [("good sentence is unnatural or wrong", "Source"), ("bad sentence is actually grammatical", "Bad OK"),
            ("dialect or colloquial form", "Dialect"), ("change alters meaning, not grammar", "Meaning"),
            ("name or personal data", "Name")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}l" + "r" * len(cols) + "@{}}",
             r"\toprule", "Phenomenon & " + " & ".join(c for _, c in cols) + r" \\", r"\midrule"]
    tot = Counter()
    for ph in SLUGS:
        lines.append(NAME[ph] + " & " + " & ".join(str(reasons[ph][k]) for k, _ in cols) + r" \\")
        tot.update({k: reasons[ph][k] for k, _ in cols})
    n = sum(tot.values())
    for (k, short) in cols:
        num(f"reject@{short}", tot[k], 0)
        num(f"rejectpct@{short}", 100 * tot[k] / n, 0)
    num("reject@all", n, 0)
    lines += [r"\midrule", "All & " + " & ".join(str(tot[k]) for k, _ in cols) + r" \\", r"\bottomrule", r"\end{tabular}",
              r"\caption{Reasons for rejecting candidate pairs in the native-speaker review. \emph{Source}: the corpus "
              r"sentence is unnatural or wrong (mostly OCR errors and typos); \emph{Bad OK}: the ungrammatical member has a "
              r"grammatical reading; \emph{Meaning}: the edit changes the meaning rather than the grammaticality.}",
              r"\label{tab:reasons}", r"\end{table}"]
    return "\n".join(lines)


# --- results ----------------------------------------------------------------------------------------------

def per_phenomenon_table(runs, pick, caption, label, stars=False):
    """Rows: models (alphabet given by pick(model)); columns: the 16 phenomena and their mean."""
    lines = [r"\begin{table*}[t]", r"\centering\footnotesize", r"\setlength{\tabcolsep}{2.6pt}",
             r"\begin{tabular}{@{}ll" + "r" * 17 + "@{}}", r"\toprule",
             "Model & & " + " & ".join(SHORT[ph] for ph in SLUGS) + r" & Avg. \\"]
    for group, models in groups(MODELS):
        rows = []
        for m in models:
            a = pick(m)
            df = runs.get((m["key"], a))
            if df is None:
                continue
            cells = []
            for ph in SLUGS:
                v = acc(df[df.phenomenon == ph])
                cells.append(f"\\cellcolor{{black!12}}{v:.1f}" if v < 50 else f"{v:.1f}")
            rows.append(f"{m['key']} & {a[0]} & " + " & ".join(cells) + f" & \\textbf{{{acc(df):.1f}}} \\\\")
        if rows:
            lines += [r"\midrule", rf"\multicolumn{{19}}{{@{{}}l}}{{\textit{{{group}}}}} \\"] + rows
    lines += [r"\bottomrule", r"\end{tabular}", rf"\caption{{{caption}}}", rf"\label{{{label}}}", r"\end{table*}"]
    return "\n".join(lines)


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
            rows.append(f"{m['key']} & {TRAINED[m['trained']]} & " + " & ".join(cells) + r" \\")
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
              r"\caption{Accuracy (\%) on all 2,400 pairs in each alphabet; chance is 50. \emph{Uzbek data}: script of the "
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
        lines.append(f"{size} & {la:.1f} & {cy:.1f} & {d:+.1f} & [{lo:+.1f}, {hi:+.1f}] & {pval(pa)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Script-matched Goldfish models of the same training-data size: the Latin model on Latin text against "
              r"the Cyrillic model on Cyrillic text, on the same 2,400 pairs. $\Delta$: difference in points with a bootstrap "
              r"95\% interval; $p$: exact McNemar test, Holm-adjusted over the four sizes.}",
              r"\label{tab:matched}", r"\end{table}"]
    return "\n".join(lines)


def length_table(runs, conditions, name, caption):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r" & & \multicolumn{3}{c}{Ungrammatical member has} & \\", r"\cmidrule(lr){3-5}",
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
        lines.append(f"{key} & {a} & " + " & ".join("--" if np.isnan(c) else f"{c:.1f}" for c in cells) +
                     ("" if np.isnan(gap) else f" & {gap:+.1f}") + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", rf"\caption{{{caption}}}", rf"\label{{tab:{name}}}", r"\end{table}"]
    return "\n".join(lines)


def models_table(stats):
    kind = {"logprob": "autoregressive", "pll": "masked"}
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{@{}lllrl@{}}", r"\toprule",
             r"Model & Hugging Face identifier & Type & Parameters & Uzbek training text \\"]
    for group, models in groups(MODELS):
        models = [m for m in models if m["key"] in stats and any((ROOT / "results").glob(f"{m['hf'].split('/')[-1]}_uzblimp_{VERSION}*.csv"))]
        if not models:
            continue
        lines += [r"\midrule", rf"\multicolumn{{5}}{{@{{}}l}}{{\textit{{{group}}}}} \\"]
        for m in models:
            lines.append(f"{m['key']} & \\texttt{{{tex(m['hf'])}}} & {kind[m['method']]} & {m['params']} & {TRAINED[m['trained']]} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{The evaluated models. Parameter counts are those given by the models' authors or on the Hugging Face Hub. \emph{Uzbek training "
              r"text}: script of the Uzbek text a model was trained on; multilingual models are trained on many languages in "
              r"several scripts.}", r"\label{tab:models}", r"\end{table*}"]
    return "\n".join(lines)


def reform_table(runs, bench):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r" & & & \multicolumn{4}{c}{Change by where new letters fall} \\", r"\cmidrule(l){4-7}",
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
            cells.append(f"{r - c:+.1f}")
        d, lo, hi, p, _, _, _ = paired(ok(cur), ok(ref))
        num(f"ref@{m['key']}@all@delta", -d)
        num(f"ref@{m['key']}@all@lo", -hi)
        num(f"ref@{m['key']}@all@hi", -lo)
        num(f"ref@{m['key']}@all@p", pval(p))
        lines.append(f"{m['key']} & {acc(cur):.1f} & {acc(ref):.1f} & " + " & ".join(cells) + r" \\")
    for g, _ in REFORM_GROUPS:
        num(f"refn@{g}", int((bench.reform_group == g).sum()), 0)
    n = [int((bench.reform_group == g).sum()) for g, _ in REFORM_GROUPS]
    lines += [r"\bottomrule", r"\end{tabular}",
              rf"\caption{{Current against reformed Latin for the models whose tokenizer covers the new letters: accuracy (\%) "
              rf"on all pairs, and the change in points for pairs whose new letters (\"o, \u{{g}}, \c{{s}}, \c{{c}}) fall in "
              rf"the edited word of \emph{{both}} members ($n={n[0]}$), in the edited word of the \emph{{gr}}ammatical member "
              rf"only ($n={n[1]}$), only in \emph{{other}} words ($n={n[2]}$), or nowhere ($n={n[3]}$).}}",
              r"\label{tab:reform}", r"\end{table}"]
    return "\n".join(lines)


def tokenizer_table(stats):
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r" & \multicolumn{3}{c}{Unknown (\%)} & \multicolumn{3}{c}{Tokens per word} \\", r"\cmidrule(lr){2-4}\cmidrule(l){5-7}",
             r"Model & Lat. & Cyr. & Ref. & Lat. & Cyr. & Ref. \\", r"\midrule"]
    for m in MODELS:
        s = stats.get(m["key"])
        if s:
            lines.append(f"{m['key']} & " + " & ".join(f"{s[a]['unk_pct']:.0f}" for a in ALPHABETS) + " & " +
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
        lines.append(f"{m['key']} & " + " & ".join(cells) + r" \\")
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
    # Pairs replaced after the audit: excluded pairs that were in benchmark v1.1 (ids of a v1.1 result file).
    excluded = {r["id"] for r in read_tsv(ROOT / "data/benchmark/excluded.tsv")}
    v11 = set(pd.read_csv(ROOT / "results" / "uzn_latn_100mb_uzblimp_v1.1.csv").id)
    num("n@replaced", len(excluded & v11), 0)
    num("pct@replaced", 100 * len(excluded & v11) / len(bench))
    num("n@excluded", len(excluded), 0)
    norm = bench.grammatical.str.lower().str.replace(r"[^\w]+", " ", regex=True).str.strip()
    dup = bench[norm.duplicated(keep=False)].assign(norm=norm)
    within = sum(g.phenomenon.nunique() == 1 for _, g in dup.groupby("norm"))
    num("n@dupwithin", within, 0)
    num("n@dupacross", dup.norm.nunique() - within, 0)
    num("n@models", len({k for k, _ in runs}), 0)
    num("n@runs", len(runs), 0)
    for name, mask in (("longer", bench.dbytes > 0), ("equal", bench.dbytes == 0), ("shorter", bench.dbytes < 0)):
        num(f"nbytes@{name}", int(mask.sum()), 0)
    mixed = [ph for ph in SLUGS if bench[bench.phenomenon == ph].source.nunique() == 2]
    num("n@mixedphen", len(mixed), 0)
    for key in ("GF-L 100MB", "GF-L full", "tahrirchi-bert", "BERTbek"):
        df = runs.get((key, "Latin"))
        if df is not None:
            d = df[df.phenomenon.isin(mixed)].join(bench[["source"]])
            num(f"source@{key}@corpus", acc(d[d.source == "corpus"]))
            num(f"source@{key}@books", acc(d[d.source == "books"]))
    ties = sum(int((df["diff"] == 0).sum()) for df in runs.values())
    num("n@ties", ties, 0)
    old = {r["id"]: r for r in read_tsv(ROOT / "data/benchmark/uzblimp_cyrl.tsv")}
    strip = ".,!?;:«»\"()…—-"
    num("n@cyrlwords", len({w.strip(strip) for r in old.values() for w in (r["grammatical"] + " " + r["ungrammatical"]).lower().split()} - {""}), 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bench = benchmark()
    runs = load_runs(VERSION)
    stats_file = ROOT / "results" / "tokenizer_stats.json"
    stats = json.loads(stats_file.read_text(encoding="utf-8")) if stats_file.exists() else {}
    ex = read_examples(bench)
    generated, reviewed, accepted, reasons = review_counts()
    selected = [("GF-L full", "Latin"), ("GF-L full", "Cyrillic"), ("GF-C full", "Cyrillic"), ("GF-C full", "Latin"),
                ("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Cyrillic"), ("tahrirchi-bert", "Reformed"),
                ("UzBERT", "Cyrillic"), ("UzBERT", "Latin"), ("XLM-R base", "Latin"), ("XLM-R base", "Cyrillic"),
                ("Qwen2.5-1.5B", "Latin"), ("Qwen2.5-1.5B", "Cyrillic")]
    everything = [(m["key"], a) for m in MODELS for a in ALPHABETS]
    delta_note = r"$\Delta$: accuracy on pairs with more tokens minus accuracy on pairs with fewer; 0 means no length effect."
    tables = {
        "phenomena": phenomena_table(bench, ex),
        "glosses": glosses(ex),
        "alphabets": alphabets_table(ex),
        "stats": stats_table(bench, reviewed, accepted),
        "reasons": reasons_table(reasons),
        "main": per_phenomenon_table(
            runs, own, r"Accuracy (\%) per phenomenon, each model on text in the script of its Uzbek training data "
            r"(L: current Latin, C: Cyrillic; multilingual models on Latin). Cells below chance (50) are shaded. Column "
            r"labels abbreviate the phenomena of Table~\ref{tab:phenomena} in the same order. With 150 pairs per cell, the "
            r"95\% Wilson interval is at most $\pm$8 points.", "tab:main"),
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
        "lengthall": length_table(runs, everything, "lengthall",
                                  r"Length effect for every scored run, as in Table~\ref{tab:length}. " + delta_note),
        "reform": reform_table(runs, bench),
        "models": models_table(stats),
        "tokenizers": tokenizer_table(stats),
        "accnorm": accnorm_table(runs),
        "pilot": pilot_table(),
    }
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
