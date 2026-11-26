"""Re-score a sample of pairs on CPU for a model that was scored on GPUs, and compare with the imported GPU run.

Uses the same scorer as the GPU run (scripts/eval.py, logprob, float32 on CPU) on a random sample of pairs
(seed 0) in each alphabet and writes results/gpu_runs/cpu_recheck_<model>.csv with both sets of scores.

    python scripts/recheck_gpu_runs.py Qwen3.5-0.8B --pairs 80
"""
import argparse
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import eval as ev  # noqa: E402
from models import ALPHABETS, ROOT, VERSION, by_key, csv_path  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("model", help="registry key of a GPU-scored model")
    p.add_argument("--pairs", type=int, default=80, help="pairs per alphabet")
    p.add_argument("--batch-size", type=int, default=8)
    a = p.parse_args()
    m = by_key(a.model)
    assert m.get("setup") == "gpu", f"{a.model} was not scored on GPUs"
    rows = []
    for alphabet in ALPHABETS:
        gpu = pd.read_csv(csv_path(m, alphabet, VERSION)).set_index("id")
        ids = random.Random(0).sample(sorted(gpu.index), a.pairs)
        sentences = list(gpu.loc[ids, "good"]) + list(gpu.loc[ids, "bad"])
        scores, ntok, _settings, _first = ev.logprob_scores(sentences, m["hf"], "cpu", "float32", a.batch_size, True)
        n = len(ids)
        for k, i in enumerate(ids):
            rows.append({"alphabet": alphabet, "id": i,
                         "good_logprob_cpu": scores[k], "bad_logprob_cpu": scores[n + k],
                         "good_logprob_gpu": gpu.at[i, "good_logprob"], "bad_logprob_gpu": gpu.at[i, "bad_logprob"],
                         "good_ntok_cpu": ntok[k], "bad_ntok_cpu": ntok[n + k],
                         "good_ntok_gpu": gpu.at[i, "good_ntok"], "bad_ntok_gpu": gpu.at[i, "bad_ntok"]})
        print(f"{a.model} {alphabet}: {n} pairs scored", flush=True)
    out = pd.DataFrame(rows)
    out["correct_cpu"] = out.good_logprob_cpu > out.bad_logprob_cpu
    out["correct_gpu"] = out.good_logprob_gpu > out.bad_logprob_gpu
    target = ROOT / "results" / "gpu_runs" / f"cpu_recheck_{m['hf'].split('/')[-1]}.csv"
    out.to_csv(target, index=False)
    diff = pd.concat([(out.good_logprob_cpu - out.good_logprob_gpu).abs(), (out.bad_logprob_cpu - out.bad_logprob_gpu).abs()])
    print(f"wrote {target.relative_to(ROOT)}: judgments agree on {int((out.correct_cpu == out.correct_gpu).sum())}/{len(out)}, "
          f"max |difference| {diff.max():.3f} nats, median {diff.median():.4f}")


if __name__ == "__main__":
    main()
