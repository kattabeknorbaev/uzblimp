"""Forced choice with chat models through OpenRouter, with the prompts and batches of the Claude runs.

Every request sends the prompt of scripts/claude_fc.py unchanged (150 numbered pairs, the same batches, both orders,
the same question and instructions) as the user message, and asks for the answers in the same structure through
the response_format of the API (a JSON schema). Temperature 0 and reasoning effort low, as in the API pilot
(scripts/score_api.py); only providers that do not train on prompts and that support every parameter are used.
Every response is cached in results/api_fc/responses/ (git-ignored), so a rerun never pays twice, and the run
stops before the budget is spent.

    python scripts/api_fc.py trial                 # one request per model: batch 1, pass A, current Latin
    python scripts/api_fc.py run --budget 10.5     # the requests of PLAN below
    python scripts/api_fc.py collect               # per-pair files in results/api_fc/

Each model is pinned to an endpoint that runs it in 8-bit or higher precision (PROVIDERS), and fallbacks are
limited to such endpoints. The run of November 2026 asks every pair once, in the order of pass A of the Claude runs
(half of each batch with the grammatical sentence first), to stay within its budget; DeepSeek V4 Pro, the most
expensive, is asked a subset of four batches per alphabet, which DeepSeek V4 Flash also answers in full.

The key is read from OPENROUTER_API_KEY or a .env file. In a cloud session whose network proxy adds the key,
no key is needed: the placeholder sent here is replaced by the proxy.
"""
import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import claude_fc as fc  # noqa: E402

ROOT = fc.ROOT
OUT = ROOT / "results" / "api_fc"
CACHE = OUT / "responses"
URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = {"deepseek-v4-flash": "deepseek/deepseek-v4-flash-0731", "deepseek-v4-pro": "deepseek/deepseek-v4-pro-0813",
          "kimi-k3.1-pro": "moonshotai/kimi-k3.1-pro", "glm-5.3": "z-ai/glm-5.3",
          "minimax-m3.1-flash": "minimax/minimax-m3.1-flash", "seed-2.1-turbo": "bytedance-seed/seed-2-1-turbo"}
# The cheapest endpoint that serves the model in 8-bit or higher precision and supports every parameter used here
# (OpenRouter endpoint tags, November 2026).
PROVIDERS = {"deepseek-v4-flash": "deepinfra/fp8/flex", "deepseek-v4-pro": "deepinfra/fp8/flex",
             "kimi-k3.1-pro": "morph/fp8", "glm-5.3": "novita/fp8", "minimax-m3.1-flash": "parasail/fp8",
             "seed-2.1-turbo": "seed/fp8"}
PRECISE = ["fp8", "bf16", "fp16", "fp32"]
# What the run asks: (model, passes, batches); every model in all three alphabets.
PLAN = [(alias, "A", range(16)) for alias in ("seed-2.1-turbo", "kimi-k3.1-pro", "glm-5.3", "deepseek-v4-flash",
                                              "minimax-m3.1-flash")] + [("deepseek-v4-pro", "A", range(4))]
EFFORT = "low"
MAX_TOKENS = 32000
ATTEMPTS = 3
LOCK = threading.Lock()
# Money spent on this evaluation so far (cached responses included, so the budget covers every run), the number of
# requests in flight, and the most expensive request so far: a request is sent only if the budget still covers it
# and every request in flight at that price.
SPENT = {"usd": 0.0, "in_flight": 0, "max_cost": 0.10}


def api_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "OPENROUTER_API_KEY" and value.strip():
                return value.strip().strip('"').strip("'")
    return "proxy-injected"  # the cloud session's proxy replaces it with the saved key


def body(alias, prompt):
    return {"model": MODELS[alias], "messages": [{"role": "user", "content": prompt}], "temperature": 0,
            "max_tokens": MAX_TOKENS, "reasoning": {"effort": EFFORT},
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "answers", "strict": True, "schema": fc.SCHEMA}},
            "provider": {"order": [PROVIDERS[alias]], "allow_fallbacks": True, "quantizations": PRECISE,
                         "data_collection": "deny", "require_parameters": True}, "usage": {"include": True}}


def parse(content):
    """The answers of a response as a string of N digits, or None if the list is not complete and unambiguous."""
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    try:
        obj = json.loads(text[start:end + 1])
    except (ValueError, TypeError):
        return None
    answers = obj.get("answers") if isinstance(obj, dict) else None
    if not isinstance(answers, list) or len(answers) != fc.N:
        return None
    out = [0] * fc.N
    for a in answers:
        if not isinstance(a, dict) or not isinstance(a.get("item"), int) or not 1 <= a["item"] <= fc.N:
            return None
        if out[a["item"] - 1] or a.get("answer") not in (1, 2):
            return None
        out[a["item"] - 1] = a["answer"]
    return "".join(map(str, out))


def call(alias, alphabet, pass_, b, attempt, prompt, budget):
    """One request, from the cache if it was made before. Returns the parsed answers and the response record."""
    f = CACHE / f"{alias}_{alphabet}_{pass_}{b + 1}_try{attempt}.json"
    if f.exists():
        rec = json.loads(f.read_text(encoding="utf-8"))
    else:
        with LOCK:
            if SPENT["usd"] + (SPENT["in_flight"] + 1) * SPENT["max_cost"] > budget:
                return None, {"skipped": "budget"}
            SPENT["in_flight"] += 1
        rec = {}
        for wait in (0, 10, 30, 60, 120, 240):
            time.sleep(wait)
            try:
                r = requests.post(URL, headers={"Authorization": f"Bearer {api_key()}", "X-Title": "UzBLiMP"},
                                  json=body(alias, prompt), timeout=1800)
            except requests.RequestException as e:
                rec = {"error": str(e)}
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                rec = {"error": f"HTTP {r.status_code}", "text": r.text[:500]}
                continue
            try:
                data = r.json()
            except ValueError:
                rec = {"error": f"HTTP {r.status_code}, not JSON", "text": r.text[:500]}
                continue
            rec = {"status": r.status_code, "response": data, "chars": len(prompt), "model_id": MODELS[alias],
                   "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            break
        if rec.get("status") == 200 and "error" not in rec.get("response", {}):  # errors are not cached
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        with LOCK:
            SPENT["in_flight"] -= 1
    data = rec.get("response") or {}
    usage = data.get("usage") or {}
    cost = float(usage.get("cost") or 0)
    with LOCK:
        SPENT["usd"] += cost
        SPENT["max_cost"] = max(SPENT["max_cost"], cost)
    choice = (data.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content")
    return parse(content), {"usage": usage, "provider": data.get("provider"), "finish": choice.get("finish_reason"),
                            "error": data.get("error") or rec.get("error")}


def run_one(alias, alphabet, pass_, b, plan, budget):
    prompt = fc.render(fc.items(plan, alphabet, b), pass_)
    info = {}
    for attempt in range(1, ATTEMPTS + 1):
        ans, info = call(alias, alphabet, pass_, b, attempt, prompt, budget)
        if ans:
            return {"pass": pass_, "batch": b, "attempts": attempt, "chars": len(prompt), "answers": ans,
                    "usage": info["usage"], "provider": info["provider"]}
        if info.get("skipped"):
            break
    return {"pass": pass_, "batch": b, "attempts": attempt, "chars": len(prompt), "answers": None,
            "usage": info.get("usage"), "error": info.get("error") or info.get("skipped") or info.get("finish")}


def key(plan, b, pass_):
    return "".join("1" if (it["first_in_A"] == "grammatical") == (pass_ == "A") else "2" for it in plan["batches"][b])


def trial(budget):
    plan = fc.load_plan()
    with ThreadPoolExecutor(len(MODELS)) as ex:
        futs = {alias: ex.submit(run_one, alias, "latn", "A", 0, plan, budget) for alias in MODELS}  # noqa: B023
    k = key(plan, 0, "A")
    for alias, fut in futs.items():
        r = fut.result()
        u = r.get("usage") or {}
        det = u.get("completion_tokens_details") or {}
        acc = sum(a == b for a, b in zip(r["answers"], k)) / fc.N if r["answers"] else None
        print(f"{alias:20} valid={bool(r['answers'])} attempts={r['attempts']} accuracy={acc if acc is None else round(100 * acc, 1)} "
              f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} reasoning={det.get('reasoning_tokens')} "
              f"cost=${float(u.get('cost') or 0):.4f} provider={r.get('provider')} {r.get('error') or ''}")
    print(f"trial spent ${SPENT['usd']:.4f}")


def run(budget, workers):
    plan = fc.load_plan()
    jobs = [(alias, a, p, b) for alias, passes, batches in PLAN for a in fc.FILES for p in passes for b in batches]
    results = {}
    with ThreadPoolExecutor(workers) as ex:
        futs = {j: ex.submit(run_one, *j, plan, budget) for j in jobs}
        for n, (j, fut) in enumerate(futs.items(), 1):
            results[j] = fut.result()
            if n % 20 == 0 or n == len(jobs):
                done = sum(1 for r in results.values() if r["answers"])
                print(f"{n}/{len(jobs)} requests, {done} valid, ${SPENT['usd']:.2f} spent", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for alias, passes, batches in PLAN:
        for a in fc.FILES:
            res = {"model": alias, "model_id": MODELS[alias], "endpoint": PROVIDERS[alias], "alphabet": a,
                   "effort": EFFORT, "results": [results[(alias, a, p, b)] for p in passes for b in batches]}
            (OUT / "runs").mkdir(parents=True, exist_ok=True)
            (OUT / "runs" / f"{alias}_{a}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    bad = [j for j, r in results.items() if not r["answers"]]
    print(f"done: {len(jobs) - len(bad)} of {len(jobs)} requests valid, ${SPENT['usd']:.2f} spent")
    for j in bad[:20]:
        print("  missing:", j, results[j].get("error"))


def collect():
    """One row per pair and order asked (results/api_fc/<model>_<alphabet>.csv), in benchmark order."""
    import pandas as pd
    plan = fc.load_plan()
    for f in sorted((OUT / "runs").glob("*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        missing = sum(not r["answers"] for r in res["results"])
        if missing:
            print(f"{f.name}: {missing} requests without a valid answer; not collected")
            continue
        d = fc.bench(res["alphabet"]).set_index("id")
        rows = []
        for r in res["results"]:
            pairs = fc.items(plan, res["alphabet"], r["batch"])
            assert r["chars"] == len(fc.render(pairs, r["pass"])), f"{f.name}: the prompt differs from render()"
            for i, it in enumerate(plan["batches"][r["batch"]]):
                good_first = (it["first_in_A"] == "grammatical") == (r["pass"] == "A")
                ans = int(r["answers"][i])
                rows.append({"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"], "good": d.at[it["id"], "grammatical"],
                             "bad": d.at[it["id"], "ungrammatical"], "batch": r["batch"] + 1, "item": i + 1,
                             "order": "gb" if good_first else "bg", "answer": ans, "correct": ans == (1 if good_first else 2),
                             "attempts": r["attempts"], "provider": r.get("provider"), "model": res["model"],
                             "model_id": res["model_id"], "alphabet": res["alphabet"], "effort": res["effort"]})
        df = pd.DataFrame(rows).set_index("id")
        df = df.loc[[i for i in fc.bench(res["alphabet"]).id if i in df.index]].reset_index()
        out = OUT / f"{res['model']}_{res['alphabet']}.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"{out.name}: {len(df)} pairs, accuracy {100 * df.correct.mean():.1f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trial")
    t.add_argument("--budget", type=float, default=1.0)
    r = sub.add_parser("run")
    r.add_argument("--budget", type=float, required=True, help="stop sending requests once this much (USD) is spent")
    r.add_argument("--workers", type=int, default=16)
    sub.add_parser("collect")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "trial":
        trial(args.budget)
    elif args.cmd == "run":
        run(args.budget, args.workers)
    else:
        collect()


if __name__ == "__main__":
    main()
