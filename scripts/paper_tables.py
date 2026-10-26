"""LaTeX tables for the paper, generated from the benchmark and result files (no hand-copied numbers).

Writes paper/tables/{phenomena,accuracy,scripts,reform}.tex for benchmark version --version.

    python scripts/paper_tables.py --version v1.0
"""
import argparse
import csv
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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default="v1.0")
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
                       ("scripts", scripts_table(runs)), ("reform", reform_table(runs))):
        (OUT / f"{name}.tex").write_text(text + "\n", encoding="utf-8")
        print(f"wrote paper/tables/{name}.tex")


if __name__ == "__main__":
    main()
