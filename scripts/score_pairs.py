"""Score minimal pairs with a causal language model and report accuracy.

Each sentence gets its total log-probability: minicons' IncrementalLMScorer,
sequence_score with a sum reduction (natural log). A pair counts as correct
when the grammatical sentence scores strictly higher than the ungrammatical one.

Writes per-pair scores to <out-dir>/<model>_<dataset>.csv and appends one line
to <out-dir>/summary.csv.

Example:
    python scripts/score_pairs.py --data data/sanity.tsv --good-col good \
        --bad-col bad --model goldfish-models/uzn_latn_100mb --group-col phenomenon
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import torch
from minicons import scorer
from tqdm import tqdm


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--data", required=True, help="TSV file, one minimal pair per row")
    p.add_argument("--good-col", required=True, help="column with the grammatical sentence")
    p.add_argument("--bad-col", required=True, help="column with the ungrammatical sentence")
    p.add_argument("--model", required=True, help="Hugging Face model ID")
    p.add_argument("--dataset-name", help="name used in the output file (default: TSV file name)")
    p.add_argument("--group-col", help="column to break accuracy down by, e.g. phenomenon")
    p.add_argument("--keep-cols", nargs="*", default=[], help="extra columns to copy to the output")
    p.add_argument("--batch-size", type=int, default=16, help="sentences per forward pass")
    p.add_argument("--device", default="auto", help="cpu, cuda, or auto (default)")
    p.add_argument(
        "--dtype",
        default="float32",
        help="weight precision (default float32; bfloat16 is too coarse to compare close scores)",
    )
    p.add_argument(
        "--bos",
        action="store_true",
        help="prepend BOS (or EOS if the model has no BOS) so the first word is scored too; "
        "has no effect if the tokenizer already adds one",
    )
    p.add_argument(
        "--mlm",
        action="store_true",
        help="masked LM (e.g. tahrirchi/tahrirchi-bert-base): pseudo-log-likelihood with "
        "PLL_metric='within_word_l2r', as TurBLiMP scored BERTurk",
    )
    p.add_argument("--limit", type=int, help="score only the first N pairs (quick tests)")
    p.add_argument("--out-dir", default="results")
    return p.parse_args()


def main():
    args = parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    # QUOTE_NONE: sentences may contain quote marks, which are text, not TSV quoting.
    df = pd.read_csv(
        args.data, sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE
    )
    extra_cols = [c for c in [args.group_col, *args.keep_cols] if c]
    missing = [c for c in [args.good_col, args.bad_col, *extra_cols] if c not in df.columns]
    if missing:
        sys.exit(f"Columns not found in {args.data}: {missing}\nAvailable: {list(df.columns)}")
    if args.limit:
        df = df.head(args.limit)

    print(f"Loading {args.model} on {device} ({args.dtype}) ...", flush=True)
    # transformers 5 otherwise loads the stored dtype, e.g. bfloat16 for Qwen2.5.
    Scorer = scorer.MaskedLMScorer if args.mlm else scorer.IncrementalLMScorer
    lm = Scorer(args.model, device=device, dtype=getattr(torch, args.dtype))
    tok = lm.tokenizer
    if args.mlm and not hasattr(tok, "batch_encode_plus"):
        # minicons 0.3.39's MaskedLMScorer calls batch_encode_plus, removed in transformers 5;
        # calling the tokenizer on a list of sentences does the same thing.
        tok.batch_encode_plus = lambda texts, **kw: tok(texts, **kw)
    n_params = sum(p.numel() for p in lm.model.parameters())

    # minicons never scores the first token of the encoded sequence of a causal LM: there
    # is no context to predict it from. If the tokenizer adds a BOS-like token itself,
    # that is what gets dropped; otherwise the first word-piece is dropped.
    # (Masked LMs score every token, so this doesn't apply to them.)
    adds_bos = args.mlm or tok("a").input_ids[0] in tok.all_special_ids
    prefix = (tok.bos_token or tok.eos_token) if args.bos and not adds_bos else ""

    good = [prefix + s for s in df[args.good_col]]
    bad = [prefix + s for s in df[args.bad_col]]
    sentences = good + bad
    extra = {"PLL_metric": "within_word_l2r"} if args.mlm else {}
    scores = []
    for i in tqdm(range(0, len(sentences), args.batch_size), desc="scoring"):
        batch = sentences[i : i + args.batch_size]
        scores += lm.sequence_score(batch, reduction=lambda x: x.sum(0).item(), **extra)
    good_lp, bad_lp = scores[: len(good)], scores[len(good) :]

    ids_good = [tok(s).input_ids for s in good]
    ids_bad = [tok(s).input_ids for s in bad]

    out = df[extra_cols].copy()
    out.insert(0, "pair_id", df.index)
    out["good"] = df[args.good_col]
    out["bad"] = df[args.bad_col]
    out["good_logprob"] = good_lp
    out["bad_logprob"] = bad_lp
    out["diff"] = out.good_logprob - out.bad_logprob
    out["correct"] = out["diff"] > 0
    # Byte-normalized comparison (TatBLiMP's acc_norm): log P / UTF-8 bytes, which removes
    # the advantage a sentence gets from being shorter. Within a pair both sentences use the
    # same alphabet, but per-byte values can't be compared across alphabets (Cyrillic = 2 bytes).
    out["good_bytes"] = [len(s.encode("utf-8")) for s in df[args.good_col]]
    out["bad_bytes"] = [len(s.encode("utf-8")) for s in df[args.bad_col]]
    out["correct_norm"] = out.good_logprob / out.good_bytes > out.bad_logprob / out.bad_bytes
    # Tokens that entered the sum (causal LM: all but the dropped first one; MLM: all but [CLS]/[SEP]).
    drop = 2 if args.mlm else 1
    out["good_ntok"] = [len(ids) - drop for ids in ids_good]
    out["bad_ntok"] = [len(ids) - drop for ids in ids_bad]
    # True where the unscored first token differs, i.e. the pair is not compared fairly.
    out["first_tok_differs"] = [False] * len(out) if args.mlm else [g[0] != b[0] for g, b in zip(ids_good, ids_bad)]
    out["model"] = args.model

    dataset = args.dataset_name or Path(args.data).stem
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.model.split('/')[-1]}_{dataset}.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")

    acc, acc_norm = out.correct.mean(), out.correct_norm.mean()
    print(f"\nModel:    {args.model} ({n_params / 1e6:.0f}M params, {'masked LM, PLL' if args.mlm else 'causal LM'})")
    print(f"Dataset:  {dataset} ({len(out)} pairs)")
    print(f"BOS:      {'n/a (masked LM)' if args.mlm else 'added by tokenizer' if adds_bos else ('prepended ' + repr(prefix)) if prefix else 'none (first word-piece unscored)'}")
    print(f"Accuracy: {acc:.3f} ({out.correct.sum()}/{len(out)})   acc_norm (per byte): {acc_norm:.3f}")
    if args.group_col:
        by_group = out.groupby(args.group_col).agg(acc=("correct", "mean"), acc_norm=("correct_norm", "mean"),
                                                   n=("correct", "size"))
        print(f"\nBy {args.group_col}:\n{by_group.round(3).to_string()}")
    n_unfair = out.first_tok_differs.sum()
    if n_unfair:
        print(f"\nWARNING: {n_unfair} pairs differ in the unscored first token; rerun with --bos.")
    print(f"\nWrote {out_path}")

    summary = out_dir / "summary.csv"
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": args.model,
        "dataset": dataset,
        "n_pairs": len(out),
        "accuracy": round(acc, 4),
        "acc_norm": round(acc_norm, 4),
        "scorer": "mlm-pll" if args.mlm else "causal",
        "bos": bool(adds_bos or prefix),
        "device": device,
        "dtype": str(next(lm.model.parameters()).dtype).removeprefix("torch."),
        "n_params_M": round(n_params / 1e6),
    }
    # Rewrite with the union of columns, so rows written before new columns existed stay aligned.
    rows = pd.concat([pd.read_csv(summary), pd.DataFrame([row])]) if summary.exists() else pd.DataFrame([row])
    rows.to_csv(summary, index=False)


if __name__ == "__main__":
    main()
