"""Score the models of scripts/models.py on the benchmark, one (model, alphabet) run at a time.

For every model: (1) tokenizer statistics for each alphabet (share of sentences with an unknown token,
tokens per sentence and per word), merged into results/tokenizer_stats.json; (2) scoring with
score_pairs.py (minicons, float32, a start token for causal LMs, pseudo-log-likelihood for masked LMs)
on current Latin and Cyrillic, and on reformed Latin only if the tokenizer produces no unknown token
there (notes/decisions.md, decision 8) and the model was not trained on Cyrillic-script Uzbek only.
Masked LMs are scored with the batched scorer of scripts/pll.py, which gives the same scores as
minicons (python scripts/pll.py --selftest).

Runs whose result file already holds every pair are skipped, so the script can be stopped and restarted.
With --carry-from, pairs whose two sentences are unchanged since an earlier benchmark version keep their
scores from that version's result file and only the changed pairs are scored. That is exact because a
pair's score doesn't depend on the other pairs (results/eval_v1.1.md).

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
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from models import ALPHABETS, DATA, MODELS, ROOT, VERSION, csv_path, stem  # noqa: E402

STATS = ROOT / "results" / "tokenizer_stats.json"
SUMMARY = ROOT / "results" / "summary.csv"


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


def score(model, data_path, dataset, out_dir, batch_size):
    """Run score_pairs.py; returns the per-pair DataFrame or None if it failed."""
    cmd = [sys.executable, str(ROOT / "scripts" / "score_pairs.py"), "--data", str(data_path),
           "--good-col", "grammatical", "--bad-col", "ungrammatical", "--model", model["hf"],
           "--group-col", "phenomenon", "--keep-cols", "id", "--dataset-name", dataset,
           "--batch-size", str(batch_size), "--device", "cpu", "--dtype", "float32", "--out-dir", str(out_dir)]
    cmd += ["--mlm", "--fast-pll"] if model["method"] == "pll" else ["--bos"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED {model['key']} ({dataset}), exit {res.returncode}\n{res.stderr[-3000:]}", flush=True)
        return None
    info = [line for line in res.stdout.splitlines() if line.startswith(("Model:", "BOS:", "Accuracy:"))]
    print("  " + " | ".join(info), flush=True)
    return pd.read_csv(Path(out_dir) / f"{model['hf'].split('/')[-1]}_{dataset}.csv", keep_default_na=False)


def run(model, alphabet, version, previous, batch_size):
    rows = read_pairs(alphabet)
    target = csv_path(model, alphabet, version)
    if complete(target, rows):
        print(f"  have {target.name}", flush=True)
        return
    name = stem(model, alphabet, version)
    dataset = name[len(model["hf"].split("/")[-1]) + 1:]  # score_pairs.py puts the model name in front itself
    old_file = csv_path(model, alphabet, previous) if previous else None
    t0 = time.time()
    if old_file is None or not old_file.exists():
        out = score(model, ROOT / "data" / "benchmark" / DATA[alphabet], dataset, ROOT / "results", batch_size)
        if out is not None:
            print(f"done {model['key']} | {alphabet}: scored {len(out)} pairs in {time.time() - t0:.0f}s, "
                  f"accuracy {100 * out.correct.astype(str).eq('True').mean():.1f}", flush=True)
        return
    old = pd.read_csv(old_file, keep_default_na=False)
    known = {(r.id, r.good, r.bad): r for r in old.itertuples(index=False)}
    todo = [r for r in rows if (r["id"], r["grammatical"], r["ungrammatical"]) not in known]
    fresh = {}
    if todo:
        with tempfile.TemporaryDirectory() as tmp:
            tsv = Path(tmp) / "changed.tsv"
            with open(tsv, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(todo[0]), delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
                w.writeheader()
                w.writerows(todo)
            scored = score(model, tsv, "changed", tmp, batch_size)
        if scored is None:
            return
        fresh = {(r.id, r.good, r.bad): r for r in scored.itertuples(index=False)}
    merged = [known.get(k) or fresh[k] for k in ((r["id"], r["grammatical"], r["ungrammatical"]) for r in rows)]
    out = pd.DataFrame(merged, columns=old.columns)
    out["pair_id"] = range(len(out))
    out.to_csv(target, index=False, encoding="utf-8")
    acc = out.correct.astype(str).eq("True").mean()
    note = f"carried over from {previous}; {len(todo)} pairs scored"
    print(f"done {model['key']} | {alphabet}: {note} in {time.time() - t0:.0f}s, accuracy {100 * acc:.1f}", flush=True)
    summary = pd.DataFrame([{"timestamp": datetime.now().isoformat(timespec="seconds"), "model": model["hf"],
                             "dataset": dataset, "n_pairs": len(out), "accuracy": round(acc, 4),
                             "acc_norm": round(out.correct_norm.astype(str).eq("True").mean(), 4), "note": note}])
    pd.concat([pd.read_csv(SUMMARY), summary]).to_csv(SUMMARY, index=False)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default=VERSION)
    p.add_argument("--carry-from", help="earlier version whose scores are reused for unchanged pairs, e.g. v1.1")
    p.add_argument("--only", nargs="*", help="model keys to run, in this order (default: all)")
    p.add_argument("--alphabets", nargs="*", default=list(ALPHABETS), choices=list(ALPHABETS))
    p.add_argument("--stats-only", action="store_true")
    p.add_argument("--force-reformed", action="store_true",
                   help="score reformed Latin even when the tokenizer produces unknown tokens there")
    p.add_argument("--batch-size", type=int, default=16)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    unknown = [k for k in args.only or [] if k not in {m["key"] for m in MODELS}]
    if unknown:
        p.error(f"not in scripts/models.py: {unknown}")
    queue = [m for k in args.only for m in MODELS if m["key"] == k] if args.only else MODELS
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
            run(model, alphabet, args.version, args.carry_from, args.batch_size)


if __name__ == "__main__":
    main()
