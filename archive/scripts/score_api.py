"""Score minimal pairs with chat models through OpenRouter by forced choice.

Each pair is shown twice, once in each order ("1. good / 2. bad" and "1. bad / 2. good"), and the
model answers with the number of the grammatical sentence. Accuracy is the share of correct answers
over both orders, so a fixed preference for "1" or "2" scores 50%; "consistent" counts pairs answered
correctly in both orders. With --explanations the prompt starts with a grammar note (decision 19):
the pair's own phenomenon (--condition explanation) or an unrelated one (--condition control).

The API key is read from .env (OPENROUTER_API_KEY=...) and never printed. Requests ask OpenRouter to
use only providers that don't collect data (provider.data_collection = deny), so benchmark sentences
don't end up in training data. Every answer is cached in data/cache/api/ as it arrives, so an
interrupted run resumes without paying twice.

    python scripts/score_api.py --data data/benchmark/uzblimp.tsv --model google/gemma-3-12b-it \
        --dataset-name uzblimp_v1.1 --per-phenomenon 3 --dry-run      # show one prompt, no calls
    python scripts/score_api.py ... --per-phenomenon 3 --max-cost 0.50  # pilot
"""
import argparse
import concurrent.futures as cf
import csv
import hashlib
import json
import random
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
URL = "https://openrouter.ai/api/v1/chat/completions"
CACHE = ROOT / "data" / "cache" / "api"
SYSTEM = 'You judge the grammaticality of Uzbek sentences. Reply only with "Answer: 1" or "Answer: 2".'
PROMPT = ("{note}Which of the following two Uzbek sentences is grammatically correct? Exactly one of them is.\n\n"
          '1. {s1}\n2. {s2}\n\nReply with "Answer: 1" or "Answer: 2".')


def api_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENROUTER_API_KEY" and value.strip():
                return value.strip().strip('"').strip("'")
    sys.exit("OPENROUTER_API_KEY not found in .env")


def prompt_for(good, bad, order, note):
    s1, s2 = (good, bad) if order == "gb" else (bad, good)
    return PROMPT.format(note=f"Grammar note: {note}\n\n" if note else "", s1=s1, s2=s2)


def parse(text):
    """The last "Answer: N"; else 1 or 2 if exactly one of them appears as a standalone number; else None."""
    tagged = re.findall(r"Answer\W*([12])(?!\d)", text or "", re.I)
    if tagged:
        return int(tagged[-1])
    found = set(re.findall(r"(?<!\d)[12](?!\d)", text or ""))
    return int(found.pop()) if len(found) == 1 else None


def cache_key(pid, order, prompt):
    return f"{pid}|{order}|{hashlib.md5((SYSTEM + prompt).encode()).hexdigest()[:10]}"


def call(session, key, model, prompt, args):
    body = {"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": args.max_tokens, "usage": {"include": True},
            "provider": {"data_collection": "deny"}}
    if args.reasoning:
        body["reasoning"] = {"effort": args.reasoning}
    for attempt in range(6):
        try:
            r = session.post(URL, headers={"Authorization": f"Bearer {key}", "X-Title": "UzBLiMP"},
                             json=body, timeout=120)
        except requests.RequestException as e:
            err = str(e)
        else:
            if r.status_code == 200:
                j = r.json()
                if "choices" in j:
                    msg = j["choices"][0].get("message", {})
                    u = j.get("usage", {})
                    return {"text": msg.get("content") or "", "cost": u.get("cost", 0) or 0,
                            "prompt_tokens": u.get("prompt_tokens", 0), "completion_tokens": u.get("completion_tokens", 0),
                            "provider": j.get("provider", "")}
                err = json.dumps(j)[:300]
            elif r.status_code in (429, 500, 502, 503, 504):
                err = f"HTTP {r.status_code}"
            else:
                return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
        time.sleep(2 ** attempt)
    return {"error": err}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", required=True, help="benchmark TSV (grammatical / ungrammatical / id / phenomenon)")
    p.add_argument("--model", required=True, help="OpenRouter model id, e.g. google/gemma-3-12b-it")
    p.add_argument("--dataset-name", required=True, help="used in the output name, e.g. uzblimp_v1.1_cyrl")
    p.add_argument("--condition", choices=["baseline", "explanation", "control"], default="baseline")
    p.add_argument("--explanations", default=str(ROOT / "data" / "explanations.tsv"))
    p.add_argument("--per-phenomenon", type=int, help="pilot: score only N random pairs per phenomenon (seeded)")
    p.add_argument("--max-cost", type=float, default=1.0, help="stop sending new calls after this many USD (default 1)")
    p.add_argument("--max-tokens", type=int, default=16, help="answer length limit (raise for reasoning models)")
    p.add_argument("--reasoning", choices=["minimal", "low", "medium", "high"], help="reasoning effort, if the model has it")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--dry-run", action="store_true", help="print one prompt and the call count, no API calls")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    df = pd.read_csv(args.data, sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE)
    if args.per_phenomenon:
        df = df.groupby("phenomenon").sample(n=args.per_phenomenon, random_state=0).reset_index(drop=True)
    notes = {}
    if args.condition != "baseline":
        ex = pd.read_csv(args.explanations, sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE)
        text = dict(zip(ex.phenomenon, ex.explanation))
        src = dict(zip(ex.phenomenon, ex.phenomenon if args.condition == "explanation" else ex.control_phenomenon))
        missing = sorted({ph for ph in df.phenomenon if not text.get(src.get(ph, ""), "").strip()})
        if missing:
            sys.exit(f"No {args.condition} text for: {missing}")
        notes = {ph: text[src[ph]].strip() for ph in df.phenomenon.unique()}

    jobs = [(r.id, r.phenomenon, r.grammatical, r.ungrammatical, o, prompt_for(r.grammatical, r.ungrammatical, o, notes.get(r.phenomenon)))
            for r in df.itertuples() for o in ("gb", "bg")]
    if args.dry_run:
        print(f"{len(df)} pairs × 2 orders = {len(jobs)} calls to {args.model} ({args.condition}). Example prompt:\n\n{jobs[0][5]}")
        return

    safe = args.model.replace("/", "__").replace(":", "_")
    cache_file = CACHE / safe / f"{args.dataset_name}_{args.condition}.jsonl"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if cache_file.exists():
        for line in cache_file.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if "error" not in rec:
                done[rec["key"]] = rec
    key = api_key()
    session = requests.Session()
    lock, spent, errors = threading.Lock(), [sum(r.get("cost", 0) for r in done.values())], []
    todo = [j for j in jobs if cache_key(j[0], j[4], j[5]) not in done]
    print(f"{args.model} | {args.dataset_name} | {args.condition}: {len(jobs)} calls, {len(jobs) - len(todo)} cached, "
          f"{len(todo)} to send (cap ${args.max_cost:.2f})", flush=True)

    def work(job):
        pid, ph, good, bad, order, prompt = job
        with lock:
            if spent[0] >= args.max_cost:
                return None
        res = call(session, key, args.model, prompt, args)
        rec = {"key": cache_key(pid, order, prompt), "id": pid, "order": order,
               "time": datetime.now().isoformat(timespec="seconds"), **res}
        with lock:
            spent[0] += rec.get("cost", 0)
            if "error" in rec:
                errors.append(rec["error"])
            with open(cache_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if "error" not in rec:
                done[rec["key"]] = rec
        return rec

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, _ in enumerate(pool.map(work, todo), 1):
            if i % 200 == 0:
                print(f"  {i}/{len(todo)} sent, ${spent[0]:.3f} spent", flush=True)
    if errors:
        print(f"{len(errors)} failed calls, e.g. {errors[0]}")

    rows = []
    for r in df.itertuples():
        ans = {}
        for o in ("gb", "bg"):
            k = cache_key(r.id, o, prompt_for(r.grammatical, r.ungrammatical, o, notes.get(r.phenomenon)))
            ans[o] = parse(done[k]["text"]) if k in done else None
        ok = {"gb": ans["gb"] == 1, "bg": ans["bg"] == 2}
        rows.append({"id": r.id, "phenomenon": r.phenomenon, "good": r.grammatical, "bad": r.ungrammatical,
                     "answer_gb": ans["gb"], "answer_bg": ans["bg"], "correct_gb": ok["gb"], "correct_bg": ok["bg"],
                     "accuracy": (ok["gb"] + ok["bg"]) / 2, "consistent": ok["gb"] and ok["bg"],
                     "invalid": (ans["gb"] is None) + (ans["bg"] is None), "model": args.model, "condition": args.condition})
    out = pd.DataFrame(rows)
    complete = out[out.invalid == 0] if len(out) else out
    name = f"api_{safe}_{args.dataset_name}" + ("" if args.condition == "baseline" else f"_{args.condition}") + \
           (f"_pilot{args.per_phenomenon}" if args.per_phenomenon else "")
    out.to_csv(ROOT / "results" / f"{name}.csv", index=False, encoding="utf-8")
    acc, cons = out.accuracy.mean(), out.consistent.mean()
    first = (out.answer_gb == 1).sum() + (out.answer_bg == 1).sum()
    print(f"\nAccuracy {100 * acc:.1f}% (both orders) | consistent {100 * cons:.1f}% | invalid answers {int(out.invalid.sum())} "
          f"| answered '1' {first}/{int((out.answer_gb.notna()).sum() + out.answer_bg.notna().sum())} | cost ${spent[0]:.4f}")
    print(out.groupby("phenomenon").accuracy.mean().mul(100).round(1).to_string())
    print(f"Wrote results/{name}.csv")
    summary = ROOT / "results" / "summary.csv"
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "model": args.model, "dataset": name.removeprefix(f"api_{safe}_"),
           "n_pairs": len(out), "accuracy": round(acc, 4), "scorer": "api-forced-choice", "condition": args.condition,
           "note": f"consistent {cons:.4f}; invalid {int(out.invalid.sum())}; cost ${spent[0]:.4f}"}
    pd.concat([pd.read_csv(summary), pd.DataFrame([row])]).to_csv(summary, index=False)


if __name__ == "__main__":
    main()
