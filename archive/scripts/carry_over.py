"""Build the results of a new benchmark version from an old one: reuse the scores of pairs whose
text is unchanged and score only the changed pairs with score_pairs.py (same settings).

Valid because per-pair scores don't depend on the other pairs: every pair shared between v0.1,
v0.2 and v1.0 got the same result in all runs (log-probabilities within 0.0002; results/eval_v*.md).

    python scripts/carry_over.py --old v1.0 --new v1.1
"""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from eval_report import RUNS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = {"Latin": "uzblimp.tsv", "Cyrillic": "uzblimp_cyrl.tsv", "Reformed": "uzblimp_reformed.tsv"}
MODELS = {  # label: (model id, score_pairs flags, extra environment)
    "Goldfish-latn": ("goldfish-models/uzn_latn_100mb", [], {}),
    "Goldfish-cyrl": ("goldfish-models/uzn_cyrl_100mb", [], {"HF_HUB_CACHE": "D:/hf_cache"}),
    "tahrirchi-bert": ("tahrirchi/tahrirchi-bert-base", ["--mlm"], {"HF_HUB_CACHE": "D:/hf_cache"}),
    "Qwen2.5-0.5B": ("Qwen/Qwen2.5-0.5B", ["--bos"], {}),
}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    summary_rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for label, alpha, stem in RUNS:
            old_csv = ROOT / "results" / f"{stem.format(v=args.old)}.csv"
            if not old_csv.exists():
                continue
            old = pd.read_csv(old_csv, keep_default_na=False)
            new = pd.read_csv(ROOT / "data" / "benchmark" / DATA[alpha], sep="\t", dtype=str,
                              keep_default_na=False, quoting=csv.QUOTE_NONE)
            known = {(r.id, r.good, r.bad): r for r in old.itertuples(index=False)}
            todo = new[[(i, g, b) not in known for i, g, b in zip(new.id, new.grammatical, new.ungrammatical)]]
            scored = pd.DataFrame()
            if len(todo):
                model, flags, env = MODELS[label]
                tsv = Path(tmp) / f"{stem.format(v=args.new)}.tsv"
                todo.to_csv(tsv, sep="\t", index=False, quoting=csv.QUOTE_NONE)
                subprocess.run([sys.executable, str(ROOT / "scripts" / "score_pairs.py"), "--data", str(tsv),
                                "--good-col", "grammatical", "--bad-col", "ungrammatical", "--model", model, *flags,
                                "--group-col", "phenomenon", "--keep-cols", "id", "--dataset-name", "delta",
                                "--out-dir", tmp], check=True, env={**os.environ, **env},
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                scored = pd.read_csv(Path(tmp) / f"{model.split('/')[-1]}_delta.csv", keep_default_na=False)
            fresh = {(r.id, r.good, r.bad): r for r in scored.itertuples(index=False)}
            rows = [known.get(k) or fresh[k] for k in zip(new.id, new.grammatical, new.ungrammatical)]
            out = pd.DataFrame(rows, columns=old.columns)
            out["pair_id"] = range(len(out))
            out_csv = ROOT / "results" / f"{stem.format(v=args.new)}.csv"
            out.to_csv(out_csv, index=False, encoding="utf-8")
            acc = out.correct.astype(str).eq("True").mean()
            print(f"{label:15} {alpha:9} reused {len(new) - len(todo):5}, scored {len(todo):3} → {out_csv.name}  acc {100 * acc:.1f}")
            summary_rows.append({"timestamp": datetime.now().isoformat(timespec="seconds"), "model": MODELS[label][0],
                                 "dataset": stem.format(v=args.new).split("_", 1)[1], "n_pairs": len(out),
                                 "accuracy": round(acc, 4),
                                 "acc_norm": round(out.correct_norm.astype(str).eq("True").mean(), 4),
                                 "note": f"carried over from {args.old}; {len(todo)} pairs scored"})
    summary = ROOT / "results" / "summary.csv"
    pd.concat([pd.read_csv(summary), pd.DataFrame(summary_rows)]).to_csv(summary, index=False)


if __name__ == "__main__":
    main()
