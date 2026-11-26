"""Write the results table of results/README.md from results/lm/json/*.json (eval.py, results_to_json.py).

Replaces the lines between <!-- results:start --> and <!-- results:end --> in results/README.md with one
row per model and method and the accuracy (%) per alphabet, and writes results/lm/per_phenomenon.md with
accuracy per phenomenon. Runs on fewer pairs than the full benchmark (pilots) show their n.

    python scripts/make_table.py
"""
import argparse
import json
import sys
from pathlib import Path

from models import MODELS
from schema import RELEASE_PHENOMENA

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- results:start -->", "<!-- results:end -->"
SCRIPT_NAMES = {"latn": "Current Latin", "cyrl": "Cyrillic", "latn_reformed": "Reformed Latin"}
METHOD_ORDER = ["logprob", "pll", "forced-choice"]
FULL = 150 * len(RELEASE_PHENOMENA)


def cell(r):
    if r is None:
        return "—"
    return f"{r['accuracy']:.1f}" + ("" if r["n_pairs"] == FULL else f" (n={r['n_pairs']})")


def runs_by_model(results):
    """{(method, label, model): {script: result}}, in table order."""
    rows = {}
    for r in results:
        rows.setdefault((r["method"], r["label"], r["model"]), {})[r["script"]] = r
    # Models of the registry (scripts/models.py) come first, in its order; other runs follow by method and name.
    order = {m["hf"]: i for i, m in enumerate(MODELS)}
    key = lambda k: (order.get(k[2], len(order)), METHOD_ORDER.index(k[0]) if k[0] in METHOD_ORDER else len(METHOD_ORDER), k[1])
    return dict(sorted(rows.items(), key=lambda kv: key(kv[0])))


def main_table(results):
    lines = ["| Model | Method | " + " | ".join(SCRIPT_NAMES.values()) + " |",
             "|---|---|" + "---:|" * len(SCRIPT_NAMES)]
    for (method, label, model), by_script in runs_by_model(results).items():
        lines.append(f"| {label} (`{model}`) | {method} | " + " | ".join(cell(by_script.get(s)) for s in SCRIPT_NAMES) + " |")
    return lines


def phenomenon_tables(results):
    runs = runs_by_model(results)
    out = ["# Accuracy (%) per phenomenon", "", "Written by `scripts/make_table.py` from `results/lm/json/`.", ""]
    for script, name in SCRIPT_NAMES.items():
        cols = [(k, v[script]) for k, v in runs.items() if script in v]
        if not cols:
            continue
        out += [f"## {name}", "", "| Phenomenon | " + " | ".join(f"{label} ({method})" for (method, label, _), _ in cols) + " |",
                "|---|" + "---:|" * len(cols)]
        for ph in RELEASE_PHENOMENA:
            out.append(f"| {ph} | " + " | ".join(
                f"{r['per_phenomenon'][ph]['accuracy']:.1f}" if ph in r["per_phenomenon"] else "—" for _, r in cols) + " |")
        out += ["| **All** | " + " | ".join(f"**{cell(r)}**" for _, r in cols) + " |", ""]
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--results", default=str(ROOT / "results" / "lm" / "json"))
    p.add_argument("--readme", default=str(ROOT / "results" / "README.md"))
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    results = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(Path(args.results).glob("*.json"))]
    if not results:
        sys.exit(f"no results in {args.results}")
    table = main_table(results)
    readme = Path(args.readme)
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        sys.exit(f"{readme.name} has no {START} ... {END} block")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    readme.write_text(head + START + "\n" + "\n".join(table) + "\n" + END + tail, encoding="utf-8", newline="\n")
    per = ROOT / "results" / "lm" / "per_phenomenon.md"
    per.write_text("\n".join(phenomenon_tables(results)), encoding="utf-8", newline="\n")
    print("\n".join(table))
    print(f"\nUpdated {readme.relative_to(ROOT) if readme.is_relative_to(ROOT) else readme} and "
          f"{per.relative_to(ROOT)} ({len(results)} runs)")


if __name__ == "__main__":
    main()
