"""Score the models of scripts/models.py on the benchmark, one (model, alphabet) run at a time.

For every model: (1) tokenizer statistics for each alphabet (share of sentences with an unknown token,
tokens per sentence and per word), merged into results/tokenizer_stats.json; (2) scoring with
score_pairs.py (minicons, float32, a start token for causal LMs, pseudo-log-likelihood for masked LMs)
on current Latin and Cyrillic, and on reformed Latin only if the tokenizer produces no unknown token
there (notes/decisions.md, decision 8) and the model was not trained on Cyrillic-script Uzbek only.
Masked LMs are scored with the batched scorer of scripts/pll.py, which gives the same scores as
minicons (python scripts/pll.py --selftest).

Runs whose result file already holds every pair are skipped, and a run is saved after every chunk of
pairs, so the script can be stopped and restarted at any time. Pairs whose two sentences are unchanged
keep the scores they already have, from this version's result file or, with --carry-from, from an earlier
version's; only the other pairs are scored. That is exact because a pair's score doesn't depend on the
other pairs (results/eval_v1.1.md).

    python scripts/run_models.py                                  # every model in the registry
    python scripts/run_models.py --only "GF-L 5MB" "GF-C 5MB"     # these, in this order
    python scripts/run_models.py --carry-from v1.1                # reuse v1.1 scores of unchanged pairs
    python scripts/run_models.py --stats-only                     # tokenizer statistics, no scoring
"""
import argparse
import csv
import json
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from models import ALPHABETS, DATA, MODELS, ROOT, VERSION, csv_path, stem  # noqa: E402

STATS = ROOT / "results" / "tokenizer_stats.json"
SUMMARY = ROOT / "results" / "summary.csv"


@contextmanager
def locked(path):
    """Hold a lock while a shared file is read, changed and written back, so that several copies of this
    script can run side by side (one per model). Without fcntl (Windows) nothing is locked."""
    try:
        import fcntl
    except ImportError:
        yield
        return
    with open(Path(tempfile.gettempdir()) / f"uzblimp_{path.name}.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def read_pairs(alphabet):
    with open(ROOT / "data" / "benchmark" / DATA[alphabet], encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def tokenizer_stats(model):
    """Per alphabet: % of sentences with an unknown token, tokens per sentence, tokens per word."""
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model["hf"])
    out = {}
    for alphabet in ALPHABETS:
        rows = read_pairs(alphabet)
        sents = [r["grammatical"] for r in rows] + [r["ungrammatical"] for r in rows]
        ids = [tok(s, add_special_tokens=False).input_ids for s in sents]
        unk = tok.unk_token_id
        n_unk = sum(unk is not None and unk in i for i in ids)
        n_tok = sum(len(i) for i in ids)
        n_words = sum(len(s.split()) for s in sents)
        out[alphabet] = {"sentences": len(sents), "unk_sentences": n_unk,
                         "unk_pct": round(100 * n_unk / len(sents), 1),
                         "tokens_per_sentence": round(n_tok / len(sents), 2),
                         "tokens_per_word": round(n_tok / n_words, 3)}
    return out


def save_stats(key, hf, stats):
    with locked(STATS):
        all_stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
        all_stats[key] = {"model": hf, **stats}
        STATS.write_text(json.dumps(all_stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def complete(path, rows):
    """True if the result file holds exactly the benchmark's pairs with the benchmark's sentences."""
    if not path.exists():
        return False
    with open(path, encoding="utf-8", newline="") as f:
        have = {(r["id"], r["good"], r["bad"]) for r in csv.DictReader(f)}
    return have == {(r["id"], r["grammatical"], r["ungrammatical"]) for r in rows}


def score(model, pairs, batch_size):
    """Run score_pairs.py on a list of benchmark rows; returns (per-pair DataFrame, its summary row) or None."""
    with tempfile.TemporaryDirectory() as tmp:
        tsv = Path(tmp) / "pairs.tsv"
        with open(tsv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(pairs[0]), delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
            w.writeheader()
            w.writerows(pairs)
        cmd = [sys.executable, str(ROOT / "scripts" / "score_pairs.py"), "--data", str(tsv),
               "--good-col", "grammatical", "--bad-col", "ungrammatical", "--model", model["hf"],
               "--group-col", "phenomenon", "--keep-cols", "id", "--dataset-name", "part",
               "--batch-size", str(batch_size), "--device", "cpu", "--dtype", "float32", "--out-dir", tmp]
        cmd += ["--mlm", "--fast-pll"] if model["method"] == "pll" else ["--bos"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FAILED {model['key']}, exit {res.returncode}\n{res.stderr[-3000:]}", flush=True)
            return None
        scored = pd.read_csv(Path(tmp) / f"{model['hf'].split('/')[-1]}_part.csv", keep_default_na=False)
        return scored, pd.read_csv(Path(tmp) / "summary.csv").iloc[-1].to_dict()


def run(model, alphabet, version, previous, batch_size):
    """Bring one run up to date: reuse every pair whose two sentences are unchanged, score the others in
    chunks and save after each chunk, so that an interrupted run loses at most one chunk."""
    rows = read_pairs(alphabet)
    keys = [(r["id"], r["grammatical"], r["ungrammatical"]) for r in rows]
    target = csv_path(model, alphabet, version)
    if complete(target, rows):
        print(f"  have {target.name}", flush=True)
        return
    name = stem(model, alphabet, version)
    dataset = name[len(model["hf"].split("/")[-1]) + 1:]
    # Scores to reuse: an earlier (possibly partial or outdated) result file for this version and the
    # result file of the previous version.
    sources = [f for f in (target, csv_path(model, alphabet, previous) if previous else None) if f is not None and f.exists()]
    known, columns = {}, None
    for f in reversed(sources):
        old = pd.read_csv(f, keep_default_na=False)
        columns = list(old.columns)
        for r in old.itertuples(index=False):
            known[(r.id, r.good, r.bad)] = r
    todo = [r for r, k in zip(rows, keys) if k not in known]
    reused = len(rows) - len(todo)
    chunk = 200 if model["method"] == "pll" else 1200
    t0, meta = time.time(), {}
    for start in range(0, len(todo), chunk):
        result = score(model, todo[start:start + chunk], batch_size)
        if result is None:
            return
        scored, meta = result
        columns = columns or list(scored.columns)
        for r in scored[columns].itertuples(index=False):
            known[(r.id, r.good, r.bad)] = r
        out = pd.DataFrame([known[k] for k in keys if k in known], columns=columns)
        out["pair_id"] = [i for i, k in enumerate(keys) if k in known]
        out.to_csv(target, index=False, encoding="utf-8")
        print(f"  {model['key']} | {alphabet}: {len(out)}/{len(rows)} pairs after {time.time() - t0:.0f}s", flush=True)
    out = pd.DataFrame([known[k] for k in keys], columns=columns)
    out["pair_id"] = range(len(out))
    out.to_csv(target, index=False, encoding="utf-8")
    acc = out.correct.astype(str).eq("True").mean()
    note = f"{len(todo)} pairs scored" + (f"; {reused} carried over from {' and '.join(f.name for f in sources)}" if reused else "")
    print(f"done {model['key']} | {alphabet}: {note} in {time.time() - t0:.0f}s, accuracy {100 * acc:.1f}", flush=True)
    row = {k: meta.get(k) for k in ("bos", "device", "dtype", "n_params_M", "scorer", "condition")}
    row.update({"timestamp": datetime.now().isoformat(timespec="seconds"), "model": model["hf"], "dataset": dataset,
                "n_pairs": len(out), "accuracy": round(acc, 4),
                "acc_norm": round(out.correct_norm.astype(str).eq("True").mean(), 4), "note": note})
    with locked(SUMMARY):
        pd.concat([pd.read_csv(SUMMARY), pd.DataFrame([row])]).to_csv(SUMMARY, index=False)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default=VERSION)
    p.add_argument("--carry-from", help="earlier version whose scores are reused for unchanged pairs, e.g. v1.1")
    p.add_argument("--only", nargs="*", help="model keys to run, in this order (default: all)")
    p.add_argument("--alphabets", nargs="*", default=list(ALPHABETS), choices=list(ALPHABETS))
    p.add_argument("--stats-only", action="store_true")
    p.add_argument("--repair", action="store_true",
                   help="only runs that already have a result file for this version: rescore the pairs whose text "
                   "has changed since (after a change to the benchmark)")
    p.add_argument("--force-reformed", action="store_true",
                   help="score reformed Latin even when the tokenizer produces unknown tokens there")
    p.add_argument("--batch-size", type=int, default=16)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    unknown = [k for k in args.only or [] if k not in {m["key"] for m in MODELS}]
    if unknown:
        p.error(f"not in scripts/models.py: {unknown}")
    # The larger models of the registry were scored on GPUs (setup "gpu", scripts/import_gpu_runs.py); they run
    # here only when named with --only.
    queue = [m for k in args.only for m in MODELS if m["key"] == k] if args.only else [m for m in MODELS if m.get("setup") != "gpu"]
    for model in queue:
        print(f"\n=== {model['key']} ({model['hf']}, {model['method']}) ===", flush=True)
        try:
            stats = tokenizer_stats(model)
        except Exception as e:  # a model that cannot be downloaded or loaded must not stop the queue
            print(f"SKIPPED {model['key']}: tokenizer failed: {type(e).__name__}: {str(e)[:500]}", flush=True)
            continue
        save_stats(model["key"], model["hf"], stats)
        for a, s in stats.items():
            print(f"  {a:9} unknown-token sentences {s['unk_pct']:5.1f}%  tokens/sentence {s['tokens_per_sentence']:6.2f}"
                  f"  tokens/word {s['tokens_per_word']:.2f}", flush=True)
        if args.stats_only:
            continue
        for alphabet in args.alphabets:
            if alphabet == "Reformed" and stats["Reformed"]["unk_sentences"] and not args.force_reformed:
                print(f"  skip Reformed: {stats['Reformed']['unk_pct']}% of sentences contain an unknown token", flush=True)
                continue
            if alphabet == "Reformed" and model["trained"] == "cyrl" and not args.force_reformed:
                print("  skip Reformed: the model was trained on Cyrillic-script Uzbek only", flush=True)
                continue
            if args.repair and not csv_path(model, alphabet, args.version).exists():
                continue
            run(model, alphabet, args.version, args.carry_from, args.batch_size)


if __name__ == "__main__":
    main()
