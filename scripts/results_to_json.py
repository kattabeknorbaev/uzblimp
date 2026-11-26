"""Write the benchmark runs of the model registry into results/json/, in eval.py's format.

Every run listed in scripts/models.py that has a per-pair result file for the current benchmark version
(results/<model>_uzblimp_<version>[_cyrl|_reformed].csv, written by run_models.py with score_pairs.py:
float32 on CPU, a start token for causal LMs, pseudo-log-likelihood for masked LMs; or, for the larger models,
imported from the GPU run by import_gpu_runs.py) gets one JSON file.
make_table.py then lists them in the README next to runs of eval.py. A CSV is used only if it holds exactly
the release's pairs for its alphabet; the JSON points back to it instead of copying the per-pair rows.

    python scripts/results_to_json.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eval import load_pairs, summarize, write_results  # noqa: E402
from models import ALPHABETS, MODELS, RELEASE_SCRIPT, ROOT, VERSION, csv_path  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    release = {a: {q["pair_id"] for q in load_pairs(ROOT / "data" / "jsonl", RELEASE_SCRIPT[a])} for a in ALPHABETS}
    for model in MODELS:
        method = "pll" if model["method"] == "pll" else "logprob"
        for alphabet in ALPHABETS:
            path = csv_path(model, alphabet, VERSION)
            if not path.exists():
                continue
            with open(path, encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            found = {r["id"] for r in rows}
            if found != release[alphabet]:  # a run that is still being scored, or one from before a benchmark change
                print(f"skipped, not complete: {path.name} ({len(found & release[alphabet])}/{len(release[alphabet])} pairs)")
                continue
            pairs = [{"pair_id": r["id"], "paradigm": r["phenomenon"], "correct": r["correct"] == "True",
                      "correct_norm": r["correct_norm"] == "True"} for r in rows]
            if model.get("setup") == "gpu":  # scored on GPUs for the second author (results/gpu_runs/README.txt)
                settings = {"scorer": f"scripts/eval.py (logprob), run on GPUs; see results/gpu_runs/{model.get('record', 'README.txt')}",
                            "dtype": model["dtype"], "device": "cuda", "bos": True, "per_pair": f"results/{path.name}"}
            elif model.get("device") == "gpu":  # run_models.py on a GPU, float32 (results/gpu_runs/README_run3.txt)
                settings = {"scorer": "scripts/score_pairs.py (minicons)" + (" --mlm (pseudo-log-likelihood)" if method == "pll" else "")
                            + ", run on a GPU; see results/gpu_runs/README_run3.txt",
                            "dtype": "float32", "device": "cuda", "bos": True, "per_pair": f"results/{path.name}"}
            else:
                settings = {"scorer": "scripts/score_pairs.py, minicons 0.3.39" + (" --mlm (pseudo-log-likelihood)" if method == "pll" else ""),
                            "dtype": "float32", "device": "cpu", "bos": True, "per_pair": f"results/{path.name}"}
            label = model["key"] + ("" if model.get("held_out", True) else " (not held out)")
            write_results(summarize(pairs, model["hf"], RELEASE_SCRIPT[alphabet], method, settings, label), pairs,
                          ROOT / "results", pairs=False)


if __name__ == "__main__":
    main()
