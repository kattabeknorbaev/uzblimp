"""Write the benchmark runs of score_pairs.py into results/json/, in eval.py's format.

The paper's numbers come from these runs: results/<model>_uzblimp_<version>[_cyrl|_reformed][_bos].csv
(float32 on CPU with a start token; tahrirchi-bert by pseudo-log-likelihood). With them in
results/json/, make_table.py lists them next to runs of eval.py. Each CSV must hold exactly the
release's pairs for its alphabet; the JSON points back to it instead of copying the per-pair rows.

    python scripts/results_to_json.py
"""
import argparse
import csv
import sys
from pathlib import Path

from eval import load_pairs, summarize, write_results
from schema import RELEASE_VERSION

ROOT = Path(__file__).resolve().parent.parent
# CSV name ({v} = version), label, alphabet, method: the runs in eval_report.py.
RUNS = [
    ("uzn_latn_100mb_uzblimp_{v}", "Goldfish-latn", "latn", "logprob"),
    ("uzn_cyrl_100mb_uzblimp_{v}", "Goldfish-cyrl", "latn", "logprob"),
    ("tahrirchi-bert-base_uzblimp_{v}", "tahrirchi-bert", "latn", "pll"),
    ("Qwen2.5-0.5B_uzblimp_{v}_bos", "Qwen2.5-0.5B", "latn", "logprob"),
    ("uzn_latn_100mb_uzblimp_{v}_cyrl", "Goldfish-latn", "cyrl", "logprob"),
    ("uzn_cyrl_100mb_uzblimp_{v}_cyrl", "Goldfish-cyrl", "cyrl", "logprob"),
    ("tahrirchi-bert-base_uzblimp_{v}_cyrl", "tahrirchi-bert", "cyrl", "pll"),
    ("Qwen2.5-0.5B_uzblimp_{v}_cyrl_bos", "Qwen2.5-0.5B", "cyrl", "logprob"),
    ("tahrirchi-bert-base_uzblimp_{v}_reformed", "tahrirchi-bert", "latn_reformed", "pll"),
    ("Qwen2.5-0.5B_uzblimp_{v}_reformed_bos", "Qwen2.5-0.5B", "latn_reformed", "logprob"),
]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default=RELEASE_VERSION)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    for name, label, script, method in RUNS:
        path = ROOT / "results" / f"{name.format(v=args.version)}.csv"
        if not path.exists():
            print(f"pending: {path.name}")
            continue
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        release = {q["pair_id"] for q in load_pairs(ROOT / "data" / "jsonl", script)}
        found = {r["id"] for r in rows}
        if found != release:
            sys.exit(f"{path.name}: {len(found - release)} pairs not in data/jsonl/{script}, "
                     f"{len(release - found)} missing")
        pairs = [{"pair_id": r["id"], "paradigm": r["phenomenon"], "correct": r["correct"] == "True",
                  "correct_norm": r["correct_norm"] == "True"} for r in rows]
        settings = {"scorer": "scripts/score_pairs.py, minicons 0.3.39" + (" --mlm (pseudo-log-likelihood)" if method == "pll" else ""),
                    "dtype": "float32", "device": "cpu", "bos": True, "per_pair": f"results/{path.name}"}
        write_results(summarize(pairs, rows[0]["model"], script, method, settings, label), pairs,
                      ROOT / "results", pairs=False)


if __name__ == "__main__":
    main()
