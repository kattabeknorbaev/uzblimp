"""LaTeX tables for the paper, generated from the benchmark and result files (no hand-copied numbers).

Writes paper/tables/{phenomena,accuracy,scripts,reform}.tex for benchmark version --version.

    python scripts/paper_tables.py --version v1.0
"""
import argparse
import csv
import difflib
import glob
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from eval_report import RUNS, _new_letter_side, paired  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "tables"
# Display names and (source, TurBLiMP/Uzbek) for Table 1, in the order of notes/decisions.md
PHEN = {
    "anaphor_agreement": "Anaphor agreement", "lexical_case": "Lexical case", "ditransitive_dative": "Ditransitive dative",
    "binding": "Binding", "stem_alternation": "Stem alternation (q/k)", "npi_hech": "NPI \\textit{hech}",
    "suspended_affixation": "Suspended affixation", "nominalization": "Nominalization", "person_agreement": "Person agreement",
    "passives": "Passives", "relative_clauses": "Relative clauses", "quantifiers": "Quantifiers (\\textit{har bir})",
    "numeral_no_plural": "Numeral + singular", "postposition_case": "Postposition case",
    "possessive_agreement": "Possessive agreement", "dative_allomorphy": "Dative allomorphy",
}
UZBEK_SPECIFIC = {"numeral_no_plural", "postposition_case", "possessive_agreement", "dative_allomorphy"}


def tex(s):
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_"), ("$", "\\$")):
        s = s.replace(a, b)
    return s


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def phenomena_table(bench):
    reviewed, accepted = defaultdict(int), defaultdict(int)
    for f in glob.glob(str(ROOT / "data" / "pairs_v[12]_*.tsv")):
        for r in read(f):
            if r["status"] != "unchecked":
                reviewed[r["phenomenon"]] += 1
                accepted[r["phenomenon"]] += r["status"] in ("accepted", "edited")
    by = defaultdict(list)
    for r in bench:
        by[r["phenomenon"]].append(r)
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{llp{6.3cm}p{6.3cm}r}", r"\toprule",
             r"Phenomenon & Type & Grammatical & Ungrammatical & Acc.\ rate \\", r"\midrule"]
    for ph, name in PHEN.items():
        corpus = [r for r in by[ph] if r["method"] != "hand-written"] or by[ph]  # examples from corpus sentences
        ex = min(corpus, key=lambda r: (len(r["grammatical"].split()), r["id"]))  # shortest pair as the example
        kind = "Uzbek" if ph in UZBEK_SPECIFIC else "TurBLiMP"
        rate = f"{100 * accepted[ph] / reviewed[ph]:.0f}\\%" if reviewed[ph] else "--"
        lines.append(f"{name} & {kind} & {tex(ex['grammatical'])} & *{tex(ex['ungrammatical'])} & {rate} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{The 16 phenomena of UzBLiMP (150 pairs each), with the shortest corpus pair of each as an example. "
              r"\emph{Type}: TurBLiMP phenomenon (stem alternation fills TurBLiMP's irregular-forms slot) or Uzbek-specific. \emph{Acc.\ rate}: share of reviewed candidate pairs "
              r"accepted by the native-speaker review.}", r"\label{tab:phenomena}", r"\end{table*}"]
    return "\n".join(lines)


def accuracy_table(runs, phen):
    cols = [("Goldfish-latn", "Latin"), ("Goldfish-cyrl", "Latin"), ("tahrirchi-bert", "Latin"), ("Qwen2.5-0.5B", "Latin"),
            ("Goldfish-latn", "Cyrillic"), ("Goldfish-cyrl", "Cyrillic"), ("tahrirchi-bert", "Cyrillic"), ("Qwen2.5-0.5B", "Cyrillic"),
            ("tahrirchi-bert", "Reformed"), ("Qwen2.5-0.5B", "Reformed")]
    cols = [c for c in cols if c in runs]
    short = {"Goldfish-latn": "GF-L", "Goldfish-cyrl": "GF-C", "tahrirchi-bert": "BERT", "Qwen2.5-0.5B": "Qwen"}
    groups = [(a, sum(1 for c in cols if c[1] == a)) for a in ("Latin", "Cyrillic", "Reformed") if any(c[1] == a for c in cols)]
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{l" + "r" * len(cols) + "}", r"\toprule",
             " & " + " & ".join(f"\\multicolumn{{{n}}}{{c}}{{{a} text}}" for a, n in groups) + r" \\",
             " ".join(f"\\cmidrule(lr){{{2 + sum(n for _, n in groups[:i])}-{1 + sum(n for _, n in groups[:i + 1])}}}"
                      for i in range(len(groups))),
             "Phenomenon & " + " & ".join(short[m] for m, _ in cols) + r" \\", r"\midrule"]
    for ph in PHEN:
        if ph in phen:
            lines.append(PHEN[ph] + " & " + " & ".join(
                f"{100 * runs[c][runs[c].phenomenon == ph].correct.mean():.1f}" for c in cols) + r" \\")
    lines += [r"\midrule", r"All (2,400) & " + " & ".join(f"\\textbf{{{100 * runs[c].correct.mean():.1f}}}" for c in cols) + r" \\",
              r"\bottomrule", r"\end{tabular}",
              r"\caption{Accuracy (\%) by model, alphabet of the text and phenomenon; chance is 50. GF-L / GF-C: Goldfish "
              r"uzn\_latn\_100mb / uzn\_cyrl\_100mb; BERT: tahrirchi-bert-base (PLL); Qwen: Qwen2.5-0.5B. Goldfish-latn is "
              r"not scored on reformed Latin (82\% of sentences contain an unknown token).}", r"\label{tab:accuracy}", r"\end{table*}"]
    return "\n".join(lines)


def scripts_table(runs):
    tests = [(("Goldfish-latn", "Latin"), ("Goldfish-cyrl", "Cyrillic"), "Matched: GF-L on Latin vs GF-C on Cyrillic"),
             (("Goldfish-latn", "Latin"), ("Goldfish-latn", "Cyrillic"), "GF-L: Latin vs Cyrillic text"),
             (("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Cyrillic"), "BERT: Latin vs Cyrillic text"),
             (("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Reformed"), "BERT: current vs reformed Latin"),
             (("Qwen2.5-0.5B", "Latin"), ("Qwen2.5-0.5B", "Cyrillic"), "Qwen: Latin vs Cyrillic text")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{lrrr}", r"\toprule",
             r"Comparison & $\Delta$ & 95\% CI & $p$ \\", r"\midrule"]
    for x, y, label in tests:
        if x in runs and y in runs:
            d, lo, hi, pv, _ = paired(runs[x].correct, runs[y].correct)
            lines.append(f"{label} & {d:+.1f} & [{lo:+.1f}, {hi:+.1f}] & {pv:.2g} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Paired comparisons on the same 2,400 pairs: accuracy difference (points), bootstrap 95\% CI and "
              r"McNemar's $p$.}", r"\label{tab:scripts}", r"\end{table}"]
    return "\n".join(lines)


def reform_table(runs):
    ref = pd.DataFrame(read(ROOT / "data/benchmark/uzblimp_reformed.tsv")).set_index("id")
    side = ref.apply(lambda r: _new_letter_side(r.grammatical, r.ungrammatical), axis=1)
    cat = ref.reform_category
    groups = [("Critical word: both members", side == "both"),
              ("Critical word: grammatical only", side == "grammatical only"),
              ("Other words only", cat == "only other words changed"),
              ("Unchanged", cat == "unchanged")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{lrrrr}", r"\toprule",
             r"New letters in & $n$ & Current & Reformed & $\Delta$ \\", r"\midrule"]
    cur, rf = runs[("tahrirchi-bert", "Latin")].correct, runs[("tahrirchi-bert", "Reformed")].correct
    for label, mask in groups:
        ids = mask.index[mask]
        d, _, _, _, k = paired(cur.loc[ids], rf.loc[ids])
        lines.append(f"{label} & {k} & {100 * cur.loc[ids].mean():.1f} & {100 * rf.loc[ids].mean():.1f} & {-d + 0.0:+.1f} \\\\")
    lines += [r"\midrule", f"All & {len(cur)} & {100 * cur.mean():.1f} & {100 * rf.mean():.1f} & {100 * (rf.mean() - cur.mean()):+.1f} \\\\",
              r"\bottomrule", r"\end{tabular}",
              r"\caption{tahrirchi-bert on current vs reformed (2026) Latin, by where the new letters (\"o, \u{g}, \c{s}, "
              r"\c{c}) fall. \emph{Grammatical only}: only the grammatical member's changed word contains a new letter "
              r"(e.g.\ \textit{\"ozimni} vs \textit{meni}).}", r"\label{tab:reform}", r"\end{table}"]
    return "\n".join(lines)


def _bench_df(bench):
    b = pd.DataFrame(bench).set_index("id")
    b["source"] = ["books" if i.split("-")[-1].startswith("2") else "corpus" for i in b.index]
    b["dlen"] = [len(u.encode()) - len(g.encode()) for g, u in zip(b.grammatical, b.ungrammatical)]
    return b


def _changed(g, b):
    tg, tb = g.split(), b.split()
    return [w.lower().strip(".,!?") for o, i1, i2, _, _ in difflib.SequenceMatcher(a=tg, b=tb, autojunk=False).get_opcodes()
            if o != "equal" for w in tg[i1:i2]]


def stats_table(bench):
    b = _bench_df(bench)
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Phenomenon & Corpus & Books & Words & Forms & $\Delta$B \\", r"\midrule"]
    for ph in PHEN:
        d = b[b.phenomenon == ph]
        forms = {w for g, u in zip(d.grammatical, d.ungrammatical) for w in _changed(g, u)}
        lines.append(f"{PHEN[ph]} & {sum(d.source == 'corpus')} & {sum(d.source == 'books')} & {d.grammatical.str.split().str.len().mean():.1f} "
                     f"& {len(forms)} & {d.dlen.mean():+.1f} \\\\")
    lines += [r"\midrule", f"All & {sum(b.source == 'corpus')} & {sum(b.source == 'books')} & "
              f"{b.grammatical.str.split().str.len().mean():.1f} & & {b.dlen.mean():+.1f} \\\\", r"\bottomrule", r"\end{tabular}",
              r"\caption{Benchmark statistics. \emph{Corpus/Books}: pairs from our corpus and from uz-books; \emph{Words}: mean "
              r"length of the grammatical sentence; \emph{Forms}: distinct grammatical word forms at the edited position; "
              r"$\Delta$\emph{B}: mean length difference ungrammatical $-$ grammatical in UTF-8 bytes.}", r"\label{tab:stats}", r"\end{table}"]
    return "\n".join(lines)


def tokens_table(runs):
    short = {"Goldfish-latn": "Goldfish-latn", "Goldfish-cyrl": "Goldfish-cyrl", "tahrirchi-bert": "tahrirchi-bert", "Qwen2.5-0.5B": "Qwen2.5-0.5B"}
    lines = [r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{lrrr}", r"\toprule",
             r"Model & Latin & Cyrillic & Reformed \\", r"\midrule"]
    for m in short:
        cells = []
        for a in ("Latin", "Cyrillic", "Reformed"):
            r = runs.get((m, a))
            cells.append("--" if r is None else f"{pd.concat([r.good_ntok, r.bad_ntok]).mean():.1f}")
        lines.append(f"{short[m]} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Mean number of scored tokens per sentence. Reading the other script roughly doubles the token count "
              r"for tahrirchi-bert.}", r"\label{tab:tokens}", r"\end{table}"]
    return "\n".join(lines)


def length_table(runs, bench):
    b = _bench_df(bench)
    keys = [("tahrirchi-bert", "Latin"), ("tahrirchi-bert", "Cyrillic"), ("tahrirchi-bert", "Reformed"),
            ("Goldfish-latn", "Latin"), ("Goldfish-latn", "Cyrillic"), ("Qwen2.5-0.5B", "Latin")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{llrrr}", r"\toprule",
             r"Model & Text & Longer & Equal & Shorter \\", r"\midrule"]
    for k in keys:
        if k not in runs:
            continue
        j = runs[k].join(b[["dlen"]])
        cells = [f"{100 * j[m].correct.mean():.1f}" for m in (j.dlen > 0, j.dlen == 0, j.dlen < 0)]
        lines.append(f"{k[0]} & {k[1]} & " + " & ".join(cells) + r" \\")
    n = [int((b.dlen > 0).sum()), int((b.dlen == 0).sum()), int((b.dlen < 0).sum())]
    lines += [r"\bottomrule", r"\end{tabular}",
              rf"\caption{{Accuracy (\%) by whether the ungrammatical sentence is longer ($n={n[0]}$), equal ($n={n[1]}$) or "
              r"shorter ($n=" + str(n[2]) + r"$) than the grammatical one in bytes. A preference for shorter sentences lowers "
              r"accuracy in the last column.}", r"\label{tab:length}", r"\end{table}"]
    return "\n".join(lines)


def accnorm_table(runs, phen):
    cols = [c for c in [("Goldfish-latn", "Latin"), ("Goldfish-cyrl", "Latin"), ("tahrirchi-bert", "Latin"), ("Qwen2.5-0.5B", "Latin"),
                        ("Goldfish-latn", "Cyrillic"), ("Goldfish-cyrl", "Cyrillic"), ("tahrirchi-bert", "Cyrillic"),
                        ("Qwen2.5-0.5B", "Cyrillic"), ("tahrirchi-bert", "Reformed"), ("Qwen2.5-0.5B", "Reformed")] if c in runs]
    short = {"Goldfish-latn": "GF-L", "Goldfish-cyrl": "GF-C", "tahrirchi-bert": "BERT", "Qwen2.5-0.5B": "Qwen"}
    alpha = {"Latin": "L", "Cyrillic": "C", "Reformed": "R"}
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{l" + "r" * len(cols) + "}", r"\toprule",
             "Phenomenon & " + " & ".join(f"{short[m]}/{alpha[a]}" for m, a in cols) + r" \\", r"\midrule"]
    for ph in PHEN:
        if ph in phen:
            lines.append(PHEN[ph] + " & " + " & ".join(
                f"{100 * runs[c][runs[c].phenomenon == ph].correct_norm.mean():.1f}" for c in cols) + r" \\")
    lines += [r"\midrule", "All & " + " & ".join(f"\\textbf{{{100 * runs[c].correct_norm.mean():.1f}}}" for c in cols) + r" \\",
              r"\bottomrule", r"\end{tabular}",
              r"\caption{Length-normalised accuracy (\%; log-probability per UTF-8 byte, as in TatBLiMP). L/C/R: Latin, "
              r"Cyrillic and reformed Latin text.}", r"\label{tab:accnorm}", r"\end{table*}"]
    return "\n".join(lines)


def reform_phen_table(runs):
    ref = pd.DataFrame(read(ROOT / "data/benchmark/uzblimp_reformed.tsv")).set_index("id")
    side = ref.apply(lambda r: _new_letter_side(r.grammatical, r.ungrammatical), axis=1)
    cur, rf = runs[("tahrirchi-bert", "Latin")], runs[("tahrirchi-bert", "Reformed")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Phenomenon & Both & Gr.\ only & Other & Current & Reformed \\", r"\midrule"]
    for ph in PHEN:
        ids = cur.index[cur.phenomenon == ph]
        s = side.loc[ids]
        other = int((ref.loc[ids].reform_category == "only other words changed").sum())
        lines.append(f"{PHEN[ph]} & {int((s == 'both').sum())} & {int((s == 'grammatical only').sum())} & {other} & "
                     f"{100 * cur.loc[ids].correct.mean():.1f} & {100 * rf.loc[ids].correct.mean():.1f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{tahrirchi-bert on current vs reformed Latin by phenomenon, with the number of pairs whose new letters "
              r"fall in both members' changed words, only in the grammatical member's, or only in other words.}",
              r"\label{tab:reformphen}", r"\end{table}"]
    return "\n".join(lines)


def reasons_table():
    reasons = defaultdict(lambda: defaultdict(int))
    for f in glob.glob(str(ROOT / "data" / "pairs_v[12]_*.tsv")):
        for r in read(f):
            if r["status"] == "rejected" and r["phenomenon"] in PHEN:
                reasons[r["phenomenon"]][r["reason"]] += 1
    cols = [("good sentence is unnatural or wrong", "Source"), ("bad sentence is actually grammatical", "Bad OK"),
            ("dialect or colloquial form", "Dialect"), ("change alters meaning, not grammar", "Meaning"),
            ("name or personal data", "Name")]
    lines = [r"\begin{table}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{l" + "r" * len(cols) + "}",
             r"\toprule", "Phenomenon & " + " & ".join(c for _, c in cols) + r" \\", r"\midrule"]
    tot = defaultdict(int)
    for ph in PHEN:
        lines.append(PHEN[ph] + " & " + " & ".join(str(reasons[ph][k]) for k, _ in cols) + r" \\")
        for k, _ in cols:
            tot[k] += reasons[ph][k]
    lines += [r"\midrule", "All & " + " & ".join(str(tot[k]) for k, _ in cols) + r" \\", r"\bottomrule", r"\end{tabular}",
              r"\caption{Reasons for rejecting candidate pairs in the native-speaker review. \emph{Source}: the grammatical "
              r"sentence is unnatural or wrong (mostly OCR errors and typos); \emph{Bad OK}: the ungrammatical member has a "
              r"grammatical reading; \emph{Meaning}: the edit changes meaning rather than grammaticality.}",
              r"\label{tab:reasons}", r"\end{table}"]
    return "\n".join(lines)


def examples_table(bench):
    ref = {r["id"]: r for r in read(ROOT / "data/benchmark/uzblimp_reformed.tsv")}
    by = defaultdict(list)
    for r in bench:
        by[r["phenomenon"]].append(r)
    lines = [r"\begin{table*}[t]", r"\centering\small", r"\begin{tabular}{lp{6.6cm}p{6.6cm}}", r"\toprule",
             r"Phenomenon & Current Latin & Reformed Latin (2026) \\", r"\midrule"]
    for ph in PHEN:
        pairs = sorted(by[ph], key=lambda r: (len(r["grammatical"].split()), r["id"]))
        r = next((p for p in pairs if p["grammatical"] != ref[p["id"]]["grammatical"]), pairs[0])  # one that shows the reform
        f = ref[r["id"]]
        lines.append(f"{PHEN[ph]} & {tex(r['grammatical'])} / *{tex(r['ungrammatical'])} & "
                     f"{tex(f['grammatical'])} / *{tex(f['ungrammatical'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{One pair per phenomenon in current and reformed Latin (the shortest pair whose reformed spelling "
              r"differs). The Cyrillic versions are in the released data.}", r"\label{tab:examples}", r"\end{table*}"]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default="v1.1")
    args = p.parse_args()
    runs = {}
    for label, alpha, stem in RUNS:
        f = ROOT / "results" / f"{stem.format(v=args.version)}.csv"
        if f.exists():
            runs[(label, alpha)] = pd.read_csv(f).set_index("id")
    bench = read(ROOT / "data/benchmark/uzblimp.tsv")
    phen = {r["phenomenon"] for r in bench}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in (("phenomena", phenomena_table(bench)), ("accuracy", accuracy_table(runs, phen)),
                       ("scripts", scripts_table(runs)), ("reform", reform_table(runs)), ("stats", stats_table(bench)),
                       ("tokens", tokens_table(runs)), ("length", length_table(runs, bench)),
                       ("accnorm", accnorm_table(runs, phen)), ("reformphen", reform_phen_table(runs)),
                       ("reasons", reasons_table()), ("examples", examples_table(bench))):
        (OUT / f"{name}.tex").write_text(text + "\n", encoding="utf-8")
        print(f"wrote paper/tables/{name}.tex")


if __name__ == "__main__":
    main()
