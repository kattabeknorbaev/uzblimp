"""Forced choice with Gemini models through the Gemini CLI, signed in with your Google account. Run it on your
own computer: the CLI needs your browser sign-in, and the requests count against your account's daily limit.

It sends the prompts of scripts/claude_fc.py (the same 150-pair batches as the Claude and OpenRouter runs) to the
Gemini CLI in headless mode, one request at a time, and saves every answer as it arrives, so a run can be stopped
and continued (for example the next day, when the daily limit is back). For every request the CLI:

- uses its own profile folder, ~/.uzblimp-gemini (GEMINI_CLI_HOME, with the login kept in an encrypted file there
  instead of the system keychain), so only the account you sign in with here is used, and no GEMINI.md, settings,
  extensions or MCP servers of your everyday Gemini CLI reach the requests;
- runs in an empty temporary folder, trusted for the session (--skip-trust), under a policy that denies every
  tool (--policy), so Gemini is offered no tools: it cannot read files, run commands or search the web;
- is pinned to the model you name (-m), and its statistics are checked: an answer that used a tool is not kept,
  and the run stops if another model answered.

The CLI cannot be given an answer schema, so one line asking for the answers as JSON is added to the end of each
prompt. Tested with Gemini CLI 0.71.1; results/chat/gemini_cli/README.md is the step-by-step guide.

    python scripts/gemini_cli_fc.py login                          # sign in once, in the browser
    python scripts/gemini_cli_fc.py models                         # model names this CLI offers
    python scripts/gemini_cli_fc.py check --model MODEL            # signed in, and is MODEL answering?
    python scripts/gemini_cli_fc.py trial --model MODEL            # one request: batch 1, pass A, current Latin
    python scripts/gemini_cli_fc.py run --model MODEL              # pass A in all three alphabets (48 requests)
    python scripts/gemini_cli_fc.py run --model MODEL --passes AB  # both orders, as the Claude runs (96 requests)
    python scripts/gemini_cli_fc.py collect                        # per-pair files in results/chat/gemini_cli/
"""
import argparse
import json
import os
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
OUT = ROOT / "results" / "chat" / "gemini_cli"
CACHE = OUT / "responses"
# The CLI's profile for these runs: its own login and no personal settings. UZBLIMP_GEMINI_HOME names another
# folder, for example to keep a second account apart.
PROFILE = Path(os.environ.get("UZBLIMP_GEMINI_HOME") or Path.home() / ".uzblimp-gemini")
TESTED = "0.71.1"
ATTEMPTS = 2  # per batch; quota, access and sign-in errors stop the run instead of using up attempts
FORMAT_LINE = ('\n\nReply with JSON only, in this form, with all {n} items: '
               '{{"answers": [{{"item": 1, "answer": 1}}, {{"item": 2, "answer": 2}}, ...]}}')
DENY_ALL = ('# Written by scripts/gemini_cli_fc.py: no tools in the benchmark runs.\n'
            '[[rule]]\ntoolName = "*"\ndecision = "deny"\npriority = 999\n')
QUOTA = re.compile(r"quota|RESOURCE_EXHAUSTED|rate.?limit|\b429\b|exhausted your|usage limit", re.I)
NO_ACCESS = re.compile(r"ModelNotFound|model not found|not found for API|\b404\b|PERMISSION_DENIED|\b403\b|"
                       r"does not have access", re.I)
NOT_SIGNED_IN = re.compile(r"auth(entication)? method|not authenticated|sign in|log ?in|credentials", re.I)


def gemini():
    exe = shutil.which("gemini")
    if not exe:
        sys.exit(f"The Gemini CLI was not found. Install it with: npm install -g @google/gemini-cli@{TESTED}")
    return exe


def cli_env():
    """The environment of every CLI call: the benchmark profile, with the login in a file inside it."""
    env = dict(os.environ)
    env["GEMINI_CLI_HOME"] = str(PROFILE)
    env["GEMINI_FORCE_FILE_STORAGE"] = "true"
    for name in ("GEMINI_MODEL", "GEMINI_SYSTEM_MD"):  # a default model or a replaced system prompt
        env.pop(name, None)
    return env


def signed_in():
    return (PROFILE / ".gemini" / "gemini-credentials.json").exists()


def sign_in_method():
    """How the profile signs in, from its settings: the requests of a Google account count against its
    subscription; an API key is billed per request."""
    try:
        settings = json.loads((PROFILE / ".gemini" / "settings.json").read_text(encoding="utf-8"))
        kind = ((settings.get("security") or {}).get("auth") or {}).get("selectedType")
    except (OSError, ValueError, AttributeError):
        kind = None
    return {"oauth-personal": "Google account", None: "not chosen yet"}.get(
        kind, f"{kind} (not your Google account: these requests would not use your subscription)")


def version():
    try:
        p = subprocess.run([gemini(), "--version"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=cli_env(), timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    lines = (p.stdout or p.stderr).strip().splitlines()
    return lines[-1].strip() if lines else "unknown"


def folders():
    """An empty working folder for the CLI and, beside it, the policy file that denies every tool."""
    d = Path(tempfile.mkdtemp(prefix="uzblimp_gemini_"))
    (d / "work").mkdir()
    (d / "deny_all_tools.toml").write_text(DENY_ALL, encoding="utf-8")
    return d / "work", d / "deny_all_tools.toml"


def last_json(text):
    """The last JSON object that starts a line of the CLI's output: its result, or its error report."""
    dec, found = json.JSONDecoder(), None
    for m in re.finditer(r"(?m)^\{", text or ""):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict):
            found = obj
    return found


def ask(model, prompt, work, policy, timeout=1800):
    """One headless request: the prompt on standard input, JSON output with the CLI's statistics."""
    cmd = [gemini(), "--skip-trust", "--policy", str(policy), "-o", "json"] + (["-m", model] if model else [])
    t = time.time()
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=work, env=cli_env(), timeout=timeout)
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        code, out, err = "timeout", e.stdout or "", e.stderr or ""
        out, err = [x.decode("utf-8", "replace") if isinstance(x, bytes) else x for x in (out, err)]
    obj = last_json(out) or last_json(err) or {}
    stats = obj.get("stats") or {}
    models = stats.get("models") or {}
    main = sorted(m for m, s in models.items() if "main" in (s.get("roles") or {})) or \
        sorted(m for m, s in models.items() if ((s.get("tokens") or {}).get("candidates") or 0) > 0)
    return {"cmd": ["gemini"] + ["<policy>" if c == str(policy) else c for c in cmd[1:]], "returncode": code,
            "stdout": out[-20000:], "stderr": err[-4000:], "seconds": round(time.time() - t, 1),
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "text": obj.get("response") or "",
            "error": obj.get("error"), "stats": stats or None,
            "tool_calls": (stats.get("tools") or {}).get("totalCalls"),
            "models_used": sorted(models), "main_models": main}


def stop_on_error(rec, where, model):
    """Ends the run on errors that another attempt cannot fix."""
    msg = json.dumps(rec.get("error") or "") + "\n" + rec["stderr"] + "\n" + rec["stdout"][-2000:]
    if QUOTA.search(msg):
        sys.exit(f"The daily limit or a rate limit was reached at {where}. Every answer so far is saved: run the "
                 "same command later (for example tomorrow) to continue.")
    if NO_ACCESS.search(msg):
        sys.exit(f"The CLI cannot use the model {model!r} with this account ({where}). The model names are listed "
                 "by: python scripts/gemini_cli_fc.py models")
    if NOT_SIGNED_IN.search(msg):
        sys.exit("The CLI is not signed in for these runs. Run: python scripts/gemini_cli_fc.py login")


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


def request(model, alphabet, pass_, b, plan, work, policy):
    """Asks one batch, or takes it from the cache: (answers or None, record, attempts). Exits on errors that
    another attempt cannot fix."""
    prompt = fc.render(fc.items(plan, alphabet, b), pass_) + FORMAT_LINE.format(n=fc.N)
    where = f"{alphabet} {pass_}{b + 1}"
    for k in range(1, ATTEMPTS + 1):
        f = CACHE / f"{slug(model)}_{alphabet}_{pass_}{b + 1}_try{k}.json"
        if f.exists():
            rec = json.loads(f.read_text(encoding="utf-8"))
        else:
            rec = ask(model, prompt, work, policy)
            rec["chars"] = len(prompt)
            if rec["returncode"] != 0 or rec.get("error"):
                stop_on_error(rec, where, model)
                print(f"  {where}: the CLI failed (exit {rec['returncode']}): "
                      f"{(rec.get('error') or {}).get('message') or rec['stderr'][-300:]}")
                continue  # not cached: the next attempt asks again
            if rec["main_models"] and rec["main_models"] != [model]:
                sys.exit(f"{where} was answered by {', '.join(rec['main_models'])}, not by {model}. Give the full model "
                         "name as `models` lists it (not an alias such as pro or flash); nothing of this request is "
                         "kept.")
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        if rec.get("tool_calls"):
            print(f"  {where} try {k}: the model tried {rec['tool_calls']} tool call(s); not kept")
            continue
        ans = parse(rec.get("text"))
        if ans:
            return ans, rec, k
        print(f"  {where} try {k}: no complete list of {fc.N} answers in the reply")
    return None, None, ATTEMPTS


def login():
    PROFILE.mkdir(parents=True, exist_ok=True)
    work, _ = folders()
    print(f"Profile folder for these runs: {PROFILE}\n\n"
          "The Gemini CLI opens now. Choose 'Sign in with Google' and finish in the browser with the account of\n"
          "your Google AI Pro subscription. If it asks whether to trust the folder, either answer is fine. When the\n"
          "CLI shows its input box, type /quit and press Enter.\n")
    input("Press Enter to open the Gemini CLI...")
    subprocess.run([gemini()], cwd=work, env=cli_env())
    print("\nSigned in: the login is saved in the profile folder." if signed_in() else
          "\nNo saved login was found in the profile folder. Run login again and choose 'Sign in with Google'.")


def models():
    work, _ = folders()
    p = subprocess.run([gemini(), "--list-models", "--skip-trust"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=work, env=cli_env())
    print((p.stdout or p.stderr).strip())
    print("\nGive --model the name in brackets, for example gemini-3.1-pro-preview or gemini-3.8-flash. Short names "
          "such as pro or flash are not accepted, because they can stand for different models.")


def check(model):
    v = version()
    print(f"Gemini CLI {v}" + ("" if v == TESTED else f" (these runs were tested with {TESTED})"))
    print(f"Profile folder: {PROFILE}; saved login: " +
          ("yes" if signed_in() else "no (run: python scripts/gemini_cli_fc.py login)") +
          f"; sign-in method: {sign_in_method()}")
    work, policy = folders()
    rec = ask(model, "Reply with the single word OK.", work, policy, timeout=600)
    print(f"exit {rec['returncode']} | reply: {rec['text'].strip()[:60]!r} | answered by: {rec['main_models']} | "
          f"tool calls: {rec['tool_calls']}")
    if rec["returncode"] != 0 or rec.get("error"):
        print((rec.get("error") or {}).get("message") or rec["stderr"][-800:])
    elif model and rec["main_models"] != [model]:
        print(f"Not answered by {model}: give the full model name as `models` lists it.")
    else:
        print("Ready.")


def run(model, alphabets, passes, batches, pause):
    if not signed_in():
        sys.exit("The CLI is not signed in for these runs. Run: python scripts/gemini_cli_fc.py login")
    plan = fc.load_plan()
    work, policy = folders()
    cli = version()
    print(f"Gemini CLI {cli}, sign-in method: {sign_in_method()}, model {model}", flush=True)
    jobs = [(a, p, b) for a in alphabets for p in passes for b in batches]
    results = {}
    try:
        for n, (a, p, b) in enumerate(jobs, 1):
            cached = (CACHE / f"{slug(model)}_{a}_{p}{b + 1}_try1.json").exists()
            ans, rec, k = request(model, a, p, b, plan, work, policy)
            results[(a, p, b)] = (ans, rec, k)
            key = "".join("1" if (it["first_in_A"] == "grammatical") == (p == "A") else "2" for it in plan["batches"][b])
            acc = f"{100 * sum(x == y for x, y in zip(ans, key)) / fc.N:.1f}%" if ans else "no valid answer"
            print(f"[{n}/{len(jobs)}] {a} {p}{b + 1}: {acc}" + ("" if not rec else f" ({rec.get('seconds')} s, "
                  f"answered by {', '.join(rec.get('main_models') or []) or '?'})"), flush=True)
            if not cached and n < len(jobs):
                time.sleep(pause)
    except KeyboardInterrupt:
        print("\nStopped. Every answer so far is saved; run the same command to continue.")
    finally:
        write_runs(model, alphabets, passes, batches, results, cli)


def write_runs(model, alphabets, passes, batches, results, cli):
    for a in alphabets:
        rows = []
        for p in passes:
            for b in batches:
                if (a, p, b) not in results:
                    continue
                ans, rec, k = results[(a, p, b)]
                rows.append({"pass": p, "batch": b, "attempts": k, "chars": rec["chars"] if rec else None,
                             "answers": ans, "usage": (rec or {}).get("stats"), "provider": "gemini-cli",
                             "models_used": (rec or {}).get("models_used"),
                             "main_models": (rec or {}).get("main_models")})
        if rows:
            (OUT / "runs").mkdir(parents=True, exist_ok=True)
            f = OUT / "runs" / f"{slug(model)}_{a}.json"
            old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            keep = {(r["pass"], r["batch"]): r for r in old.get("results", [])}
            keep.update({(r["pass"], r["batch"]): r for r in rows})
            versions = sorted(set(old.get("cli_versions", [])) | {cli})
            res = {"model": slug(model), "model_id": model, "endpoint": "gemini-cli", "alphabet": a,
                   "effort": "CLI default", "cli_versions": versions,
                   "results": sorted(keep.values(), key=lambda r: (r["pass"], r["batch"]))}
            f.write_text(json.dumps(res, indent=1), encoding="utf-8")


def collect():
    """One row per answered pair and order (results/chat/gemini_cli/<model>_<alphabet>.csv), in benchmark order."""
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
                             "attempts": r["attempts"], "main_model": ",".join(r.get("main_models") or []),
                             "models_used": ",".join(r.get("models_used") or []),
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
    sub.add_parser("login")
    sub.add_parser("models")
    c = sub.add_parser("check")
    c.add_argument("--model", help="the model to test (default: the CLI's default)")
    for name in ("trial", "run"):
        s = sub.add_parser(name)
        s.add_argument("--model", required=True, help="a full model name, as `models` lists it")
        if name == "run":
            s.add_argument("--passes", default="A", help="A (one order, as the OpenRouter runs) or AB (both orders)")
            s.add_argument("--alphabets", default=",".join(fc.FILES))
            s.add_argument("--pause", type=float, default=15, help="seconds between requests")
    sub.add_parser("collect")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "login":
        login()
    elif args.cmd == "models":
        models()
    elif args.cmd == "check":
        check(args.model)
    elif args.cmd == "trial":
        run(args.model, ["latn"], "A", [0], 0)
    elif args.cmd == "run":
        run(args.model, args.alphabets.split(","), args.passes, range(16), args.pause)
    else:
        collect()


if __name__ == "__main__":
    main()
