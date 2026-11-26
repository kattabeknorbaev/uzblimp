"""Forced choice with Gemini models through the Gemini CLI, signed in with your Google account. Run it on your
own computer (the CLI needs your browser sign-in).

It sends the prompts of scripts/claude_fc.py, the same 150-pair batches as the Claude and OpenRouter runs, to the
Gemini CLI in non-interactive mode, one request at a time, and saves every answer as it arrives, so the run can be
stopped and continued (for example the next day, when the daily quota is back). Gemini runs in an empty temporary
folder with its file, shell, memory and web tools switched off, so it cannot see the answer key in this repository
or look the sentences up; the CLI's statistics are checked for any tool call, and an answer that used a tool is
not kept. Because the CLI cannot be given an answer schema, one line asking for the answers as JSON is added to the
end of each prompt.

    python scripts/gemini_cli_fc.py check                          # CLI installed, signed in, answering?
    python scripts/gemini_cli_fc.py trial --model MODEL            # one request: batch 1, pass A, current Latin
    python scripts/gemini_cli_fc.py run --model MODEL              # pass A in all three alphabets (48 requests)
    python scripts/gemini_cli_fc.py run --model MODEL --passes AB  # both orders, as the Claude runs (96 requests)
    python scripts/gemini_cli_fc.py collect                        # per-pair files in results/gemini_cli/

MODEL is a model name the CLI accepts (inside `gemini`, the /model command lists them). Results go to
results/gemini_cli/; commit and push that folder.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude_fc as fc  # noqa: E402

ROOT = fc.ROOT
OUT = ROOT / "results" / "gemini_cli"
CACHE = OUT / "responses"
ATTEMPTS = 2  # per batch; a quota error stops the run instead of using up attempts
FORMAT_LINE = ('\n\nReply with JSON only, in this form, with all {n} items: '
               '{{"answers": [{{"item": 1, "answer": 1}}, {{"item": 2, "answer": 2}}, ...]}}')
# Built-in tools of the Gemini CLI that could read files, run commands, search the web or remember things.
NO_TOOLS = ["read_file", "read_many_files", "list_directory", "glob", "search_file_content", "write_file", "replace",
            "run_shell_command", "web_fetch", "google_web_search", "save_memory", "write_todos"]
QUOTA = re.compile(r"quota|RESOURCE_EXHAUSTED|rate limit|\b429\b|exhausted your daily|usage limit", re.I)


def gemini():
    exe = shutil.which("gemini")
    if not exe:
        sys.exit("The Gemini CLI was not found. Install it with: npm install -g @google/gemini-cli")
    return exe


def workspace():
    """An empty folder for the CLI to run in, whose settings switch its tools off."""
    d = Path(tempfile.mkdtemp(prefix="uzblimp_gemini_"))
    (d / ".gemini").mkdir()
    (d / ".gemini" / "settings.json").write_text(json.dumps({"tools": {"exclude": NO_TOOLS}}, indent=1), encoding="utf-8")
    return d


def ask(model, prompt, cwd, plain=False, timeout=1800):
    """One non-interactive request: the prompt on standard input; JSON output with statistics unless plain."""
    cmd = [gemini()] + (["-m", model] if model else []) + ([] if plain else ["--output-format", "json"])
    t = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=cwd, timeout=timeout)
    rec = {"cmd": cmd[1:], "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr[-4000:],
           "seconds": round(time.time() - t, 1), "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    text, stats = p.stdout, None
    if not plain:
        try:
            obj = json.loads(p.stdout[p.stdout.find("{"):])
            text, stats = obj.get("response") or "", obj.get("stats")
            if obj.get("error"):
                rec["error"] = obj["error"]
        except ValueError:
            pass
    rec["text"], rec["stats"] = text, stats
    rec["tool_calls"] = ((stats or {}).get("tools") or {}).get("totalCalls")
    rec["models_used"] = sorted(((stats or {}).get("models") or {}).keys())
    return rec


def parse(text, n=fc.N):
    """The answers as a string of n digits: from the JSON asked for, else from lines like "12: 2"."""
    if not text:
        return None
    s = text.strip()
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(s[start:end + 1])
            items = obj.get("answers") if isinstance(obj, dict) else None
            if isinstance(items, list) and len(items) == n:
                out = [0] * n
                for a in items:
                    i, v = a.get("item"), a.get("answer")
                    if not isinstance(i, int) or not 1 <= i <= n or out[i - 1] or v not in (1, 2):
                        return None
                    out[i - 1] = v
                return "".join(map(str, out))
        except (ValueError, AttributeError):
            pass
    pairs = re.findall(r"(?m)^\D{0,10}?(\d{1,3})\s*[:.)\-–]\s*(?:sentence\s*)?([12])\b", s)
    found = {}
    for i, v in pairs:
        i = int(i)
        if 1 <= i <= n:
            if i in found and found[i] != v:
                return None
            found[i] = v
    if len(found) == n:
        return "".join(found[i] for i in range(1, n + 1))
    return None


def slug(model):
    return re.sub(r"[^A-Za-z0-9.\-]+", "-", model or "default").strip("-")


def request(model, alphabet, pass_, b, plan, cwd, plain):
    """Asks one batch (or takes it from the cache): (answers or None, record), or raises SystemExit on a quota error."""
    prompt = fc.render(fc.items(plan, alphabet, b), pass_) + FORMAT_LINE.format(n=fc.N)
    for k in range(1, ATTEMPTS + 1):
        f = CACHE / f"{slug(model)}_{alphabet}_{pass_}{b + 1}_try{k}.json"
        if f.exists():
            rec = json.loads(f.read_text(encoding="utf-8"))
        else:
            rec = ask(model, prompt, cwd, plain)
            rec["chars"] = len(prompt)
            if rec["returncode"] != 0 or rec.get("error"):
                if QUOTA.search(rec["stderr"] + json.dumps(rec.get("error") or "") + rec["stdout"][-2000:]):
                    sys.exit(f"Quota or rate limit reached at {alphabet} {pass_}{b + 1}. Run the same command later "
                             "to continue; every answer so far is saved.")
                print(f"  {alphabet} {pass_}{b + 1}: the CLI failed (exit {rec['returncode']}): {rec['stderr'][-300:]}")
                continue  # failures are not cached; next attempt
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        if rec.get("tool_calls"):
            print(f"  {alphabet} {pass_}{b + 1} try {k}: the model used {rec['tool_calls']} tool call(s); not kept")
            continue
        ans = parse(rec.get("text"))
        if ans:
            return ans, rec, k
    return None, None, ATTEMPTS


def check():
    print(subprocess.run([gemini(), "--version"], capture_output=True, text=True).stdout.strip() or "version unknown")
    cwd = workspace()
    rec = ask(None, "Reply with the single word OK.", cwd)
    if rec["returncode"] != 0:
        rec = ask(None, "Reply with the single word OK.", cwd, plain=True)
        print("JSON output is not supported by this CLI version; use --plain with trial and run.")
    print("exit", rec["returncode"], "| answer:", (rec["text"] or "").strip()[:80], "| models:", rec["models_used"],
          "| tool calls:", rec["tool_calls"])
    if rec["returncode"] != 0:
        print(rec["stderr"][-800:])


def run(model, alphabets, passes, batches, pause, plain):
    plan = fc.load_plan()
    cwd = workspace()
    jobs = [(a, p, b) for a in alphabets for p in passes for b in batches]
    results = {}
    try:
        for n, (a, p, b) in enumerate(jobs, 1):
            cached = any((CACHE / f"{slug(model)}_{a}_{p}{b + 1}_try{k}.json").exists() for k in range(1, ATTEMPTS + 1))
            ans, rec, k = request(model, a, p, b, plan, cwd, plain)
            results[(a, p, b)] = (ans, rec, k)
            key = "".join("1" if (it["first_in_A"] == "grammatical") == (p == "A") else "2" for it in plan["batches"][b])
            acc = f"{100 * sum(x == y for x, y in zip(ans, key)) / fc.N:.1f}%" if ans else "no valid answer"
            print(f"[{n}/{len(jobs)}] {a} {p}{b + 1}: {acc}" + ("" if not rec else f" ({rec.get('seconds')} s, "
                  f"models {rec.get('models_used')})"), flush=True)
            if not cached and n < len(jobs):
                time.sleep(pause)
    finally:
        write_runs(model, alphabets, passes, batches, results)


def write_runs(model, alphabets, passes, batches, results):
    for a in alphabets:
        rows = []
        for p in passes:
            for b in batches:
                if (a, p, b) not in results:
                    continue
                ans, rec, k = results[(a, p, b)]
                rows.append({"pass": p, "batch": b, "attempts": k, "chars": rec["chars"] if rec else None,
                             "answers": ans, "usage": (rec or {}).get("stats"), "provider": "gemini-cli",
                             "models_used": (rec or {}).get("models_used")})
        if rows:
            (OUT / "runs").mkdir(parents=True, exist_ok=True)
            f = OUT / "runs" / f"{slug(model)}_{a}.json"
            old = json.loads(f.read_text(encoding="utf-8"))["results"] if f.exists() else []
            keep = {(r["pass"], r["batch"]): r for r in old}
            keep.update({(r["pass"], r["batch"]): r for r in rows})
            res = {"model": slug(model), "model_id": model, "endpoint": "gemini-cli", "alphabet": a,
                   "effort": "CLI default",
                   "results": sorted(keep.values(), key=lambda r: (r["pass"], r["batch"]))}
            f.write_text(json.dumps(res, indent=1), encoding="utf-8")


def collect():
    """One row per answered pair and order (results/gemini_cli/<model>_<alphabet>.csv), in benchmark order."""
    import pandas as pd
    plan = fc.load_plan()
    for f in sorted((OUT / "runs").glob("*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        d = fc.bench(res["alphabet"]).set_index("id")
        rows = []
        for r in res["results"]:
            if not r["answers"]:
                continue
            pairs = fc.items(plan, res["alphabet"], r["batch"])
            assert r["chars"] == len(fc.render(pairs, r["pass"]) + FORMAT_LINE.format(n=fc.N)), f"{f.name}: prompt differs"
            for i, it in enumerate(plan["batches"][r["batch"]]):
                good_first = (it["first_in_A"] == "grammatical") == (r["pass"] == "A")
                ans = int(r["answers"][i])
                rows.append({"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"], "good": d.at[it["id"], "grammatical"],
                             "bad": d.at[it["id"], "ungrammatical"], "batch": r["batch"] + 1, "item": i + 1,
                             "order": "gb" if good_first else "bg", "answer": ans, "correct": ans == (1 if good_first else 2),
                             "attempts": r["attempts"], "models_used": ",".join(r.get("models_used") or []),
                             "model": res["model"], "alphabet": res["alphabet"]})
        if not rows:
            continue
        df = pd.DataFrame(rows)
        order = {i: n for n, i in enumerate(fc.bench(res["alphabet"]).id)}
        df = df.sort_values(["id", "order"], key=lambda s: s.map(order) if s.name == "id" else s)
        out = OUT / f"{res['model']}_{res['alphabet']}.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"{out.name}: {df.id.nunique()} pairs, {len(df)} answers, accuracy {100 * df.correct.mean():.1f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    for name in ("trial", "run"):
        s = sub.add_parser(name)
        s.add_argument("--model", required=True, help="a model name the Gemini CLI accepts")
        s.add_argument("--plain", action="store_true", help="for CLI versions without --output-format json")
        if name == "run":
            s.add_argument("--passes", default="A", help="A (one order, as the OpenRouter runs) or AB (both orders)")
            s.add_argument("--alphabets", default=",".join(fc.FILES))
            s.add_argument("--pause", type=float, default=15, help="seconds between requests")
    sub.add_parser("collect")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "check":
        check()
    elif args.cmd == "trial":
        run(args.model, ["latn"], "A", [0], 0, args.plain)
    elif args.cmd == "run":
        run(args.model, args.alphabets.split(","), args.passes, range(16), args.pause, args.plain)
    else:
        collect()


if __name__ == "__main__":
    main()
