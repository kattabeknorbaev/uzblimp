"""Import the per-pair results of the larger models scored on GPUs into results/.

The second author had these models scored on rented GPUs with the repository's own scorer (scripts/eval.py,
method logprob; a local patch changed only how the weights are loaded). This script takes the folder of that
run (README.txt, scripts/, run*/logs, run*/results/pairs/<org>__<model>__<alphabet>__logprob.csv), checks every
file against the benchmark, writes each registry model's runs in the format of scripts/run_models.py
(results/<stem>.csv), and keeps the run's record in results/gpu_runs/: its README, logs and scripts, the
float32-against-bfloat16 control of Qwen3.5-9B-Base, and its Qwen2.5-1.5B run, which the paper compares with
our own CPU run of that model. Nothing from the folder is executed.

    python scripts/import_gpu_runs.py <folder>
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from models import DATA, MODELS, ROOT, VERSION, csv_path  # noqa: E402

ALPHA = {"latn": "Latin", "cyrl": "Cyrillic", "latn_reformed": "Reformed"}
PATTERN = re.compile(r"(.+?)__(.+?)__(latn|cyrl|latn_reformed)__logprob\.csv$")
OUT = ROOT / "results" / "gpu_runs"


def benchmark(alphabet):
    b = pd.read_csv(ROOT / "data" / "benchmark" / DATA[alphabet], sep="\t", dtype=str, keep_default_na=False)
    return b.set_index("id")


def convert(path, alphabet, hf, condition):
    d = pd.read_csv(path)
    b = benchmark(alphabet)
    assert len(d) == len(b) == d.pair_id.nunique(), (path, len(d))
    assert set(d.pair_id) == set(b.index), path
    assert (d.good.values == b.loc[d.pair_id, "grammatical"].values).all(), path
    assert (d.bad.values == b.loc[d.pair_id, "ungrammatical"].values).all(), path
    assert ((d.good_logprob > d.bad_logprob) == d.correct.astype(str).eq("True")).all(), path
    out = pd.DataFrame({"phenomenon": d.paradigm, "id": d.pair_id, "good": d.good, "bad": d.bad,
                        "good_logprob": d.good_logprob, "bad_logprob": d.bad_logprob})
    out["diff"] = out.good_logprob - out.bad_logprob
    out["correct"] = out.good_logprob > out.bad_logprob
    out["good_bytes"] = out.good.map(lambda s: len(s.encode("utf-8")))
    out["bad_bytes"] = out.bad.map(lambda s: len(s.encode("utf-8")))
    out["correct_norm"] = out.good_logprob / out.good_bytes > out.bad_logprob / out.bad_bytes
    out["good_ntok"], out["bad_ntok"] = d.good_ntok, d.bad_ntok
    out["model"], out["condition"] = hf, condition
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", help="folder of the GPU run (with README.txt and run*/)")
    folder = Path(p.parse_args().folder)
    by_hf = {m["hf"]: m for m in MODELS if m.get("setup") == "gpu"}
    done = set()
    for f in sorted(folder.glob("run*/results/pairs/*.csv")):
        org, name, script = PATTERN.match(f.name).groups()
        hf, alphabet = f"{org}/{name}", ALPHA[script]
        if hf in by_hf:
            m = by_hf[hf]
            convert(f, alphabet, hf, f"gpu {m['dtype']}").to_csv(csv_path(m, alphabet, VERSION), index_label="pair_id")
            done.add((m["key"], alphabet))
        else:  # the validation run of a model the paper scores on CPU
            target = OUT / "check" / f.name
            target.parent.mkdir(parents=True, exist_ok=True)
            convert(f, alphabet, hf, "gpu float32").to_csv(target, index_label="pair_id")
    for f in sorted(folder.glob("run*/results_bf16check*/pairs/*.csv")):
        org, name, script = PATTERN.match(f.name).groups()
        target = OUT / "bf16check" / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        convert(f, ALPHA[script], f"{org}/{name}", "gpu bfloat16").to_csv(target, index_label="pair_id")
    missing = {(m["key"], a) for m in by_hf.values() for a in ALPHA.values()} - done
    assert not missing, f"no results for {sorted(missing)}"
    # The run's own record, kept as it was handed over.
    shutil.copy2(folder / "README.txt", OUT / "README.txt")
    for f in folder.glob("scripts/*"):
        (OUT / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, OUT / "scripts" / f.name)
    for f in folder.glob("run*/logs/*.log"):
        target = OUT / "logs" / f.parent.parent.name / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
    print(f"imported {len(done)} runs of {len({k for k, _ in done})} models; record in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
