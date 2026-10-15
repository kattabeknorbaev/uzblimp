"""Check whether UzBLiMP sentences occur in a model's training data (contamination).

For every grammatical sentence in data/pairs_v*.tsv, test whether it appears
(after normalization) anywhere in each source. Normalization: lowercase,
all apostrophe variants unified, whitespace collapsed, final .!? dropped.

Sources are Hugging Face dataset repos:
- JSONL files: every string value is searched;
- tokenized parquet (an `input_ids` column): decoded with --tokenizer first.

Writes results/overlap_<name>.json (counts and pair ids only, no corpus text).

    set HF_TOKEN=...   (read token; needed for private repos)
    python scripts/check_overlap.py --repo tomaris/tomaris-sft --repo tomaris/phase-d
    python scripts/check_overlap.py --repo tomaris/fullcorpus --tokenizer javohirmat/qwen3.6-uz-expanded
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
APOS = re.compile("[ʻʼ'’‘`´]")
SPACE = re.compile(r"\s+")


def norm(s):
    return SPACE.sub(" ", APOS.sub("'", s.lower())).strip()


def benchmark_sentences():
    """{normalized grammatical sentence: [pair ids]} over all pair files."""
    out = {}
    for f in sorted((ROOT / "data").glob("pairs_v*.tsv")):
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                key = norm(r["grammatical"]).rstrip(".!? ")
                out.setdefault(key, []).append((r["id"], r["status"]))
    return out


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def texts_from_file(path, tokenizer):
    if path.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield from strings(json.loads(line))
    elif path.endswith(".parquet"):
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=512, columns=["input_ids"]):
            ids = batch.column("input_ids").to_pylist()
            yield from tokenizer.batch_decode(ids, skip_special_tokens=True)


def check_repo(repo, sentences, tokenizer):
    api = HfApi()
    files = [f for f in api.list_repo_files(repo, repo_type="dataset") if f.endswith((".jsonl", ".parquet"))]
    hits = {}
    n_chars = 0
    for f in files:
        t0 = time.time()
        local = hf_hub_download(repo, f, repo_type="dataset")
        big = "\n".join(norm(t) for t in texts_from_file(local, tokenizer))
        n_chars += len(big)
        for key in sentences:
            if key in big:
                hits.setdefault(key, []).append(f)
        print(f"  {repo}/{f}: {len(big) / 1e6:.0f}M chars, cumulative hits {len(hits)} ({time.time() - t0:.0f}s)",
              flush=True)
        del big
    return hits, n_chars


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", action="append", required=True)
    p.add_argument("--tokenizer", help="HF tokenizer for tokenized parquet sources")
    p.add_argument("--name", help="output name (default: from the first repo)")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    tok = None
    if args.tokenizer:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.tokenizer)
    sents = benchmark_sentences()
    print(f"{len(sents)} distinct grammatical sentences from data/pairs_v*.tsv")
    report = {"sentences": len(sents), "repos": {}}
    for repo in args.repo:
        hits, n_chars = check_repo(repo, sents, tok)
        ids = sorted(i for k in hits for i, _ in sents[k])
        usable = sorted(i for k in hits for i, st in sents[k] if st in ("accepted", "edited"))
        report["repos"][repo] = {"chars_searched": n_chars, "sentences_found": len(hits),
                                 "pair_ids_found": ids, "usable_pair_ids_found": usable}
        print(f"{repo}: {len(hits)} of {len(sents)} sentences found ({100 * len(hits) / len(sents):.1f}%), "
              f"{len(usable)} of them in accepted pairs")
    name = args.name or args.repo[0].replace("/", "_")
    out = ROOT / "results" / f"overlap_{name}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
