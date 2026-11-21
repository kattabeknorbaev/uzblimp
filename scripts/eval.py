"""Evaluate a model on the UzBLiMP release files (data/jsonl/<script>/) and write its results.

Two methods, kept apart in the `method` field of every result:

- logprob: a Hugging Face causal LM. Each sentence gets its total log-probability (natural log, summed
  over its tokens), and a pair is correct when the grammatical sentence scores higher. Scoring follows
  score_pairs.py (minicons): the tokenizer adds its usual special tokens, the first token of the encoded
  sequence is context and isn't scored, and when the tokenizer adds no start token a BOS (or EOS, if
  there is no BOS) is prepended so the first word is scored too. Weights load in float32 unless --dtype
  says otherwise; bfloat16 is too coarse for close pairs, so treat --dtype auto (bfloat16 or float16 on
  a GPU) as a fast first pass, not the reported number.
- forced-choice: chat models without log-probabilities, through OpenRouter. Each pair is shown in both
  orders and the model answers 1 or 2; accuracy counts both orders, so always answering "1" scores 50%,
  and `consistent` is the share of pairs right in both orders. The prompt, answer parsing and cache
  keys are those of score_api.py, so answers either script has cached are not paid for twice. The API
  key is read from OPENROUTER_API_KEY (environment or .env) and never printed; requests ask for
  providers that don't collect data.

Writes results/json/<model>__<script>__<method>.json (accuracy overall and per phenomenon) and
results/pairs/<model>__<script>__<method>.csv (one row per pair). make_table.py turns the JSON files
into the README table.

    python scripts/eval.py --model goldfish-models/uzn_latn_100mb --script latn
    python scripts/eval.py --model Qwen/Qwen2.5-0.5B --script cyrl --device cuda --dtype auto
    python scripts/eval.py --method forced-choice --model google/gemma-3-12b-it --script latn --per-phenomenon 3
    python scripts/eval.py --models-file eval_models.txt --script latn
    python scripts/eval.py --selftest
"""
import argparse
import concurrent.futures as cf
import csv
import hashlib
import json
import os
import random
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from schema import RELEASE_PHENOMENA, RELEASE_VERSION, SCRIPT_FILES

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CACHE = ROOT / "data" / "cache" / "api"
# Same text as score_api.py: keep them identical, or cached answers stop matching.
SYSTEM = 'You judge the grammaticality of Uzbek sentences. Reply only with "Answer: 1" or "Answer: 2".'
PROMPT = ("{note}Which of the following two Uzbek sentences is grammatically correct? Exactly one of them is.\n\n"
          '1. {s1}\n2. {s2}\n\nReply with "Answer: 1" or "Answer: 2".')
# Dataset names score_api.py used for its cache files.
CACHE_DATASET = {"latn": "uzblimp_{v}", "cyrl": "uzblimp_{v}_cyrl", "latn_reformed": "uzblimp_{v}_reformed"}


def load_pairs(folder, script, per_phenomenon=None):
    """Release records for one alphabet, optionally a seeded sample of N pairs per phenomenon."""
    pairs = []
    for path in sorted((Path(folder) / script).glob("*.jsonl")):
        recs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if per_phenomenon:
            recs = random.Random(0).sample(recs, min(per_phenomenon, len(recs)))
        pairs += recs
    if not pairs:
        sys.exit(f"no pairs in {Path(folder) / script}")
    return pairs


def summarize(rows, model, script, method, settings, label=None):
    """rows: per-pair dicts with `paradigm` and `correct` (bool, or 0/0.5/1 for forced choice)."""
    def acc(rs, key="correct"):
        return round(100 * sum(r[key] for r in rs) / len(rs) + 1e-9, 1)  # halves round up, as in the paper's tables

    by = defaultdict(list)
    for r in rows:
        by[r["paradigm"]].append(r)
    out = {"benchmark": "UzBLiMP", "version": RELEASE_VERSION, "model": model,
           "label": label or model.split("/")[-1], "script": script, "method": method,
           "n_pairs": len(rows), "accuracy": acc(rows)}
    if all("correct_norm" in r for r in rows):
        out["accuracy_norm"] = acc(rows, "correct_norm")  # log P per UTF-8 byte (TatBLiMP's acc_norm)
    if method == "forced-choice":
        out["consistent"] = acc(rows, "consistent")
        out["invalid_answers"] = sum(r["invalid"] for r in rows)
    out["per_phenomenon"] = {ph: {"n": len(rs), "correct": sum(r["correct"] for r in rs), "accuracy": acc(rs)}
                             for ph, rs in sorted(by.items())}
    out["settings"] = settings
    out["date"] = date.today().isoformat()
    return out


def stem(model, script, method):
    return f"{model.replace('/', '__').replace(':', '_')}__{script}__{method}"


def write_results(summary, rows, out_dir, pairs=True):
    """results/json/<name>.json, plus results/pairs/<name>.csv unless the per-pair rows exist elsewhere."""
    name = stem(summary["model"], summary["script"], summary["method"])
    (out_dir / "json").mkdir(parents=True, exist_ok=True)
    (out_dir / "json" / f"{name}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8", newline="\n")
    if pairs:
        (out_dir / "pairs").mkdir(parents=True, exist_ok=True)
        with open(out_dir / "pairs" / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(f"{summary['label']} | {summary['script']} | {summary['method']}: {summary['accuracy']}% of "
          f"{summary['n_pairs']} pairs → results/json/{name}.json")
    for ph, s in summary["per_phenomenon"].items():
        print(f"  {ph:22} {s['accuracy']:5.1f}")


# --- logprob: Hugging Face causal LMs ---------------------------------------------------------------

def logprob_scores(sentences, model_name, device, dtype, batch_size, start_token=True):
    """Total log-probability of each sentence. Returns (scores, scored token counts, settings)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    if dtype == "auto":
        dtype = "float32" if device == "cpu" else ("bfloat16" if torch.cuda.is_bf16_supported() else "float16")
    tok = AutoTokenizer.from_pretrained(model_name)
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=getattr(torch, dtype))
    except TypeError:  # transformers before 4.56 calls it torch_dtype
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=getattr(torch, dtype))
    model.to(device).eval()

    adds_bos = tok("a").input_ids[0] in tok.all_special_ids
    prefix = (tok.bos_token or tok.eos_token) if start_token and not adds_bos else ""
    ids = [tok(prefix + s).input_ids for s in sentences]
    pad = next((t for t in (tok.pad_token_id, tok.eos_token_id) if t is not None), 0)  # masked out anyway
    scores = [0.0] * len(ids)
    order = sorted(range(len(ids)), key=lambda i: len(ids[i]))  # similar lengths per batch, less padding
    with torch.no_grad():
        for k in range(0, len(order), batch_size):
            idx = order[k:k + batch_size]
            n = max(len(ids[i]) for i in idx)
            # Right padding keeps the real tokens at positions 0..len-1; the mask drops the pads.
            x = torch.tensor([ids[i] + [pad] * (n - len(ids[i])) for i in idx], device=device)
            mask = torch.tensor([[1] * len(ids[i]) + [0] * (n - len(ids[i])) for i in idx], device=device)
            logits = model(input_ids=x, attention_mask=mask).logits.float()
            logp = torch.log_softmax(logits[:, :-1], dim=-1).gather(-1, x[:, 1:, None]).squeeze(-1)
            for i, s in zip(idx, (logp * mask[:, 1:]).sum(1).tolist()):
                scores[i] = s
    settings = {"scorer": "scripts/eval.py", "dtype": dtype, "device": device, "batch_size": batch_size,
                "start_token": (prefix or ("tokenizer" if adds_bos else None))}
    return scores, [len(x) - 1 for x in ids], settings, [x[0] for x in ids]


def run_logprob(pairs, model, args):
    good = [p["sentence_good"] for p in pairs]
    bad = [p["sentence_bad"] for p in pairs]
    scores, ntok, settings, first = logprob_scores(good + bad, model, args.device, args.dtype, args.batch_size,
                                                   not args.no_start_token)
    n = len(pairs)
    rows = []
    for k, p in enumerate(pairs):
        g, b = scores[k], scores[n + k]
        gb, bb = len(p["sentence_good"].encode("utf-8")), len(p["sentence_bad"].encode("utf-8"))
        rows.append({"pair_id": p["pair_id"], "paradigm": p["paradigm"], "good": p["sentence_good"],
                     "bad": p["sentence_bad"], "good_logprob": g, "bad_logprob": b, "diff": g - b,
                     "correct": g > b, "correct_norm": g / gb > b / bb, "good_ntok": ntok[k], "bad_ntok": ntok[n + k]})
    if settings["start_token"] is None:
        # The unscored first token differs between the sentences: such a pair isn't compared fairly.
        settings["first_token_differs"] = sum(first[k] != first[n + k] for k in range(n))
    return rows, settings


# --- forced-choice: chat models through OpenRouter ---------------------------------------------------

def api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENROUTER_API_KEY" and value.strip():
                key = value.strip().strip('"').strip("'")
    if not key:
        sys.exit("OPENROUTER_API_KEY not set (environment or .env)")
    return key


def prompt_for(good, bad, order):
    s1, s2 = (good, bad) if order == "gb" else (bad, good)
    return PROMPT.format(note="", s1=s1, s2=s2)


def parse(text):
    """The last "Answer: N"; else 1 or 2 if exactly one of them appears as a standalone number; else None."""
    tagged = re.findall(r"Answer\W*([12])(?!\d)", text or "", re.I)
    if tagged:
        return int(tagged[-1])
    found = set(re.findall(r"(?<!\d)[12](?!\d)", text or ""))
    return int(found.pop()) if len(found) == 1 else None


def cache_key(pid, order, prompt):
    return f"{pid}|{order}|{hashlib.md5((SYSTEM + prompt).encode()).hexdigest()[:10]}"


def call_api(key, model, prompt, max_tokens, reasoning=None):
    body = {"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": max_tokens, "usage": {"include": True},
            "provider": {"data_collection": "deny"}}
    if reasoning:
        body["reasoning"] = {"effort": reasoning}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "UzBLiMP"}
    err = "no attempt"
    for attempt in range(6):
        req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.loads(r.read())
            if "choices" in j:
                usage = j.get("usage", {})
                return {"text": j["choices"][0].get("message", {}).get("content") or "",
                        "cost": usage.get("cost", 0) or 0, "provider": j.get("provider", "")}
            err = json.dumps(j)[:300]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                return {"error": f"HTTP {e.code}: {e.read()[:300]!r}"}
            err = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            err = str(e)
        time.sleep(2 ** attempt)
    return {"error": err}


def run_forced_choice(pairs, model, script, args, caller=call_api, cache_root=CACHE):
    jobs = [(p["pair_id"], o, prompt_for(p["sentence_good"], p["sentence_bad"], o)) for p in pairs for o in ("gb", "bg")]
    cache_file = cache_root / model.replace("/", "__").replace(":", "_") / \
        f"{CACHE_DATASET[script].format(v=RELEASE_VERSION)}_baseline.jsonl"
    done = {}
    if cache_file.exists():
        for line in cache_file.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if "error" not in rec:
                done[rec["key"]] = rec
    todo = [j for j in jobs if cache_key(*j) not in done]
    print(f"{model} | {script}: {len(jobs)} calls, {len(jobs) - len(todo)} cached, {len(todo)} to send "
          f"(cap ${args.max_cost:.2f})", flush=True)
    if todo:
        key = api_key() if caller is call_api else None
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        lock, spent, errors = threading.Lock(), [sum(r.get("cost", 0) for r in done.values())], []

        def work(job):
            pid, order, prompt = job
            with lock:
                if spent[0] >= args.max_cost:
                    return
            res = caller(key, model, prompt, args.max_tokens, args.reasoning)
            rec = {"key": cache_key(*job), "id": pid, "order": order,
                   "time": datetime.now().isoformat(timespec="seconds"), **res}
            with lock:
                spent[0] += rec.get("cost", 0)
                with open(cache_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if "error" in rec:
                    errors.append(rec["error"])
                else:
                    done[rec["key"]] = rec

        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(work, todo))
        if errors:
            print(f"{len(errors)} failed calls, e.g. {errors[0]}")
    rows = []
    for p in pairs:
        ans = {}
        for o in ("gb", "bg"):
            k = cache_key(p["pair_id"], o, prompt_for(p["sentence_good"], p["sentence_bad"], o))
            ans[o] = parse(done[k]["text"]) if k in done else None
        ok_gb, ok_bg = ans["gb"] == 1, ans["bg"] == 2
        rows.append({"pair_id": p["pair_id"], "paradigm": p["paradigm"], "good": p["sentence_good"],
                     "bad": p["sentence_bad"], "answer_gb": ans["gb"], "answer_bg": ans["bg"],
                     "correct": (ok_gb + ok_bg) / 2, "consistent": ok_gb and ok_bg,
                     "invalid": (ans["gb"] is None) + (ans["bg"] is None)})
    settings = {"scorer": "scripts/eval.py (prompt of scripts/score_api.py)", "api": "OpenRouter",
                "temperature": 0, "max_tokens": args.max_tokens, "reasoning": args.reasoning,
                "per_phenomenon": args.per_phenomenon}
    return rows, settings


# --- driver --------------------------------------------------------------------------------------

def read_models_file(path):
    """Lines `<method> <model id> [label]`; # starts a comment."""
    runs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split("#", 1)[0].split()
        if parts:
            if parts[0] not in ("logprob", "forced-choice") or len(parts) < 2:
                sys.exit(f"{path}: expected `<logprob|forced-choice> <model> [label]`, got {line!r}")
            runs.append((parts[0], parts[1], " ".join(parts[2:]) or None))
    return runs


def selftest():
    fails = 0

    def check(name, ok):
        nonlocal fails
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} {name}")

    for text, want in [("Answer: 2", 2), ("answer:1.", 1), ("1 or 2? Answer: 1", 1), ("2", 2), ("1 2", None), ("", None)]:
        check(f"parse({text!r}) == {want}", parse(text) == want)
    pairs = [{"pair_id": f"npi_hech-{i:04d}", "paradigm": "npi_hech", "sentence_good": "Hech kim kelmadi.",
              "sentence_bad": "Hech kim keldi."} for i in range(4)]
    always_one = lambda key, model, prompt, max_tokens, reasoning=None: {"text": "Answer: 1", "cost": 0}
    args = argparse.Namespace(max_cost=1.0, max_tokens=16, reasoning=None, workers=2, per_phenomenon=None)
    with tempfile.TemporaryDirectory() as tmp:
        rows, _ = run_forced_choice(pairs, "test/always-one", "latn", args, caller=always_one, cache_root=Path(tmp))
        s = summarize(rows, "test/always-one", "latn", "forced-choice", {})
        check("answering '1' always scores 50% with 0% consistent", (s["accuracy"], s["consistent"]) == (50.0, 0.0))
        calls = []
        counting = lambda *a, **kw: calls.append(1) or always_one(*a, **kw)
        run_forced_choice(pairs, "test/always-one", "latn", args, caller=counting, cache_root=Path(tmp))
        check("a second run answers from the cache (0 calls)", not calls)
    rows = [{"paradigm": "npi_hech", "correct": c, "correct_norm": c} for c in (True, True, True, False)]
    s = summarize(rows, "m", "latn", "logprob", {})
    check("3 of 4 correct is 75.0%", (s["accuracy"], s["per_phenomenon"]["npi_hech"]["correct"]) == (75.0, 3))
    print(f"\n{fails} failure(s)")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", help="Hugging Face model id (logprob) or OpenRouter model id (forced-choice)")
    p.add_argument("--models-file", help="run every model listed, e.g. eval_models.txt")
    p.add_argument("--method", choices=["logprob", "forced-choice"], default="logprob")
    p.add_argument("--label", help="name for the results table (default: the model id's last part)")
    p.add_argument("--script", choices=list(SCRIPT_FILES), default="latn", help="alphabet to evaluate")
    p.add_argument("--data", default=str(ROOT / "data" / "jsonl"))
    p.add_argument("--out", default=str(ROOT / "results"))
    p.add_argument("--per-phenomenon", type=int, help="pilot: only N seeded random pairs per phenomenon")
    p.add_argument("--device", help="cpu, cuda, cuda:1 ... (default: cuda if available)")
    p.add_argument("--dtype", choices=["float32", "float16", "bfloat16", "auto"], default="float32",
                   help="weight precision; auto = bfloat16/float16 on a GPU, float32 on CPU")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--no-start-token", action="store_true", help="don't prepend BOS/EOS (the first token goes unscored)")
    p.add_argument("--max-cost", type=float, default=1.0, help="forced-choice: stop sending calls after this many USD")
    p.add_argument("--max-tokens", type=int, default=16, help="forced-choice: answer length limit")
    p.add_argument("--reasoning", choices=["minimal", "low", "medium", "high"], help="forced-choice: reasoning effort")
    p.add_argument("--workers", type=int, default=8, help="forced-choice: parallel requests")
    p.add_argument("--selftest", action="store_true", help="check answer parsing and accounting (no model, no API)")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    if bool(args.model) == bool(args.models_file):
        p.error("give --model or --models-file")
    runs = read_models_file(args.models_file) if args.models_file else [(args.method, args.model, args.label)]

    pairs = load_pairs(args.data, args.script, args.per_phenomenon)
    unknown = sorted({q["paradigm"] for q in pairs} - set(RELEASE_PHENOMENA))
    if unknown:
        sys.exit(f"unknown phenomena in {args.data}: {unknown}")
    for method, model, label in runs:
        if method == "logprob":
            rows, settings = run_logprob(pairs, model, args)
        else:
            rows, settings = run_forced_choice(pairs, model, args.script, args)
        write_results(summarize(rows, model, args.script, method, settings, label), rows, Path(args.out))


if __name__ == "__main__":
    main()
