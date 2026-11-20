"""Score the models of scripts/models.py on the benchmark, one (model, alphabet) run at a time.

For every model: (1) tokenizer statistics for each alphabet (share of sentences with an unknown token,
tokens per sentence and per word), merged into results/tokenizer_stats.json; (2) scoring with
score_pairs.py (minicons, float32, a start token for causal LMs, pseudo-log-likelihood for masked LMs)
on current Latin and Cyrillic, and on reformed Latin only if the tokenizer produces no unknown token
there (notes/decisions.md, decision 8). Runs whose result file already holds every pair are skipped,
so the script can be stopped and restarted.

    python scripts/run_models.py                       # every model in the registry
    python scripts/run_models.py --only "GF-L 5MB" "GF-C 5MB"
    python scripts/run_models.py --stats-only          # tokenizer statistics, no scoring
"""
import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from models import ALPHABETS, DATA, MODELS, ROOT, csv_path, stem  # noqa: E402

STATS = ROOT / "results" / "tokenizer_stats.json"


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


def complete(path, n):
    if not path.exists():
        return False
    with open(path, encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f)) == n


def score(model, alphabet, version, batch_size):
    out_name = stem(model, alphabet, version)
    dataset = out_name[len(model["hf"].split("/")[-1]) + 1:]  # score_pairs.py prefixes the model name itself
    cmd = [sys.executable, str(ROOT / "scripts" / "score_pairs.py"),
           "--data", str(ROOT / "data" / "benchmark" / DATA[alphabet]),
           "--good-col", "grammatical", "--bad-col", "ungrammatical", "--model", model["hf"],
           "--group-col", "phenomenon", "--keep-cols", "id", "--dataset-name", dataset,
           "--batch-size", str(batch_size), "--device", "cpu", "--dtype", "float32",
           "--out-dir", str(ROOT / "results")]
    cmd += ["--mlm"] if model["method"] == "pll" else ["--bos"]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    tail = "\n".join(res.stdout.strip().splitlines()[-30:])
    if res.returncode != 0:
        print(f"FAILED {model['key']} | {alphabet} (exit {res.returncode})\n{res.stderr[-3000:]}", flush=True)
        return False
    print(f"done {model['key']} | {alphabet} in {time.time() - t0:.0f}s\n{tail}", flush=True)
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", default="v1.1")
    p.add_argument("--only", nargs="*", help="model keys to run (default: all)")
    p.add_argument("--alphabets", nargs="*", default=list(ALPHABETS), choices=list(ALPHABETS))
    p.add_argument("--stats-only", action="store_true")
    p.add_argument("--force-reformed", action="store_true",
                   help="score reformed Latin even when the tokenizer produces unknown tokens there")
    p.add_argument("--batch-size", type=int, default=16)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    n = len(read_pairs("Latin"))

    for model in MODELS:
        if args.only and model["key"] not in args.only:
            continue
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
            if complete(csv_path(model, alphabet, args.version), n):
                print(f"  have {csv_path(model, alphabet, args.version).name}", flush=True)
                continue
            score(model, alphabet, args.version, args.batch_size)


if __name__ == "__main__":
    main()
