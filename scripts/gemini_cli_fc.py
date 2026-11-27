"""Forced choice with Gemini models through the Gemini CLI, signed in with your Google account. Run it on your
own computer: the CLI needs your browser sign-in, and the requests count against your account's daily limit.

It sends the prompts of scripts/claude_fc.py (the same 150-pair batches as the Claude and OpenRouter runs) to the
Gemini CLI in headless mode, one request at a time, and saves every answer as it arrives, so a run can be stopped
and continued (for example the next day, when the daily limit is back). For every request the CLI:

- is its own copy of Gemini CLI 0.71.1, installed by `setup` in ~/.uzblimp-gemini/cli: another Gemini CLI on the
  computer, or an update of it, does not change these runs, and this copy does not update itself;
- uses its own profile folder, ~/.uzblimp-gemini (GEMINI_CLI_HOME), with its own login (the file
  .gemini/oauth_creds.json there), so only the account you sign in with here is used, and no GEMINI.md, settings,
  .env file, extensions or MCP servers of your everyday Gemini CLI reach the requests;
- runs in an empty temporary folder, trusted for the session (--skip-trust), under a policy that denies every
  tool (--policy), so Gemini is offered no tools: it cannot read files, run commands or search the web;
- is pinned to the model you name (-m), and its statistics are checked: an answer that used a tool is not kept,
  and the run stops if another model answered.

The CLI cannot be given an answer schema, so one line asking for the answers as JSON is added to the end of each
prompt. results/chat/gemini_cli/README.md is the step-by-step guide.

    python scripts/gemini_cli_fc.py setup                          # install the CLI for these runs (once)
    python scripts/gemini_cli_fc.py login                          # sign in once, in the browser
    python scripts/gemini_cli_fc.py models                         # model names this CLI offers
    python scripts/gemini_cli_fc.py check --model MODEL            # signed in, and is MODEL answering?
    python scripts/gemini_cli_fc.py trial --model MODEL            # one request: batch 1, pass A, current Latin
    python scripts/gemini_cli_fc.py run --model MODEL              # pass A in all three alphabets (48 requests)
    python scripts/gemini_cli_fc.py run --model MODEL --passes AB  # both orders, as the Claude runs (96 requests)
    python scripts/gemini_cli_fc.py collect                        # per-pair files in results/chat/gemini_cli/
"""
import argparse
import atexit
import hashlib
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
VERSION = "0.71.1"  # the CLI version these runs use; `setup` installs it
CLI_DIR = Path.home() / ".uzblimp-gemini" / "cli"
CLI_JS = CLI_DIR / "node_modules" / "@google" / "gemini-cli" / "bundle" / "gemini.js"
# The CLI's profile for these runs: its own login and no personal settings. UZBLIMP_GEMINI_HOME names another
# folder, for example to keep a second account apart.
PROFILE = Path(os.environ.get("UZBLIMP_GEMINI_HOME") or Path.home() / ".uzblimp-gemini")
SETTINGS = PROFILE / ".gemini" / "settings.json"
LOGIN_FILE = PROFILE / ".gemini" / "oauth_creds.json"  # where the CLI keeps a Google login
# Written into the profile's settings before the CLI starts: no self-update (it would replace VERSION), no editor
# integration and no usage statistics.
PROFILE_SETTINGS = {"general": {"enableAutoUpdate": False, "enableAutoUpdateNotification": False},
                    "ide": {"enabled": False, "hasSeenNudge": True},
                    "privacy": {"usageStatisticsEnabled": False}}
# Variables of an everyday Gemini CLI setup that would change these runs: a default model, a replaced system
# prompt, or another Google Cloud project (and its quota) instead of the subscription.
DROP = ("GEMINI_MODEL", "GEMINI_SYSTEM_MD", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT_ID",
        "GOOGLE_CLOUD_QUOTA_PROJECT")
# ... and, for the sign-in, variables that would preselect another sign-in method than the Google account.
DROP_AT_LOGIN = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA",
                 "GOOGLE_GEMINI_BASE_URL", "GEMINI_DEFAULT_AUTH_TYPE")
ATTEMPTS = 2  # per batch and run; a batch without a usable reply is asked again by the next run
FORMAT_LINE = ('\n\nReply with JSON only, in this form, with one entry for each of the {n} items: '
               '{{"answers": [{{"item": <item number>, "answer": <1 or 2>}}, ...]}}')
DENY_ALL = ('# Written by scripts/gemini_cli_fc.py: no tools in the benchmark runs.\n'
            '[[rule]]\ntoolName = "*"\ndecision = "deny"\npriority = 999\n')
TIP = re.compile("\U0001F4A1 Tip:.*?environment variable\\.?", re.S)  # the CLI's advice added to quota errors
STOPS = [  # (pattern in the CLI's error, what to tell the user); the first match ends the run
    (r"Manual authorization is required|Opening authentication page|No input provided via stdin|"
     r"consent could not be obtained",
     "The CLI could not use the saved login at {where}: no network, or the login has expired. Check the "
     "connection and run the same command again; if this repeats, run: python scripts/gemini_cli_fc.py login"),
    (r"exhausted your daily quota|quota will reset after|QUOTA_EXHAUSTED|PerDay",
     "The daily limit for {model} was reached at {where}. Every answer so far is saved: run the same command "
     "again when the limit is reset (the CLI's message below says when)."),
    (r"No capacity available|overloaded|MODEL_CAPACITY_EXHAUSTED|MODEL_CAPACITY_EXCEEDED|capacity exceeded|"
     r"exhausted your capacity|UNAVAILABLE",
     "Google's servers had no capacity for {model} at {where}. Every answer so far is saved: run the same "
     "command again in a few minutes."),
    (r"VALIDATION_REQUIRED|Verify your account",
     "Google asks you to verify your account ({where}): {link}"),
    (r"quota|RESOURCE_EXHAUSTED|rate.?limit|\b429\b|usage limit",
     "A usage limit was reached at {where}. Every answer so far is saved: run the same command again later "
     "(after the daily limit, the next day)."),
    (r"ModelNotFound|model not found|not found for API|\b404\b|NOT_FOUND|PERMISSION_DENIED|\b403\b|"
     r"does not have access",
     "The CLI cannot use the model {model} with this account ({where}). The model names are listed by: "
     "python scripts/gemini_cli_fc.py models"),
    (r"auth(entication)? method|not authenticated|UNAUTHENTICATED|\b401\b|invalid_grant",
     "The CLI is not signed in for these runs. Run: python scripts/gemini_cli_fc.py login"),
]


def node():
    exe = shutil.which("node")
    if not exe:
        sys.exit("Node.js was not found. Install Node.js 20 or newer (nodejs.org) and open a new terminal.")
    return exe


def gemini():
    """The command that starts the CLI of these runs (Node.js and the CLI's script, no shell in between)."""
    if not CLI_JS.is_file():
        sys.exit("The Gemini CLI for these runs is not installed. Run: python scripts/gemini_cli_fc.py setup")
    return [node(), str(CLI_JS)]


def cli_env(login=False):
    """The environment of every CLI call: the profile of these runs, and none of the variables in DROP."""
    env = dict(os.environ)
    env["GEMINI_CLI_HOME"] = str(PROFILE)
    env["GEMINI_FORCE_FILE_STORAGE"] = "true"  # API keys and MCP tokens in the profile, not the system keychain
    for name in DROP + (DROP_AT_LOGIN if login else ()):
        env.pop(name, None)
    if not login:
        env["NO_BROWSER"] = "true"  # a login that cannot be used fails at once instead of waiting for a browser
        env["GEMINI_CLI_NO_RELAUNCH"] = "true"  # one process, so that a time-out stops it
    return env


def read_settings():
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        sys.exit(f"The settings of the profile could not be read: {SETTINGS}. Delete the file and run login again.")


def prepare_profile(forget_sign_in=False):
    """Writes PROFILE_SETTINGS into the profile's settings and keeps everything else; for login, also forgets the
    chosen sign-in method, so that the CLI asks for it again."""
    settings = read_settings()
    for section, values in PROFILE_SETTINGS.items():
        settings.setdefault(section, {}).update(values)
    auth = (settings.get("security") or {}).get("auth")
    if forget_sign_in and isinstance(auth, dict):
        auth.pop("selectedType", None)
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def sign_in_type():
    return (((read_settings().get("security") or {}).get("auth") or {}).get("selectedType"))


def sign_in_problem():
    """None when the profile is signed in with a Google account; otherwise what to do."""
    kind = sign_in_type()
    if kind == "oauth-personal" and LOGIN_FILE.is_file():
        return None
    if kind in (None, "oauth-personal"):
        return "The CLI is not signed in for these runs. Run: python scripts/gemini_cli_fc.py login"
    return (f"The profile of these runs signs in with {kind}, not with your Google account, so the requests "
            "would not count against your subscription. Run: python scripts/gemini_cli_fc.py login, and choose "
            "'Sign in with Google'.")


def version():
    try:
        p = subprocess.run(gemini() + ["--version"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=cli_env(), timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    lines = (p.stdout or p.stderr).strip().splitlines()
    return lines[-1].strip() if lines else "unknown"


def folders():
    """An empty working folder for the CLI and, beside it, the policy file that denies every tool and an empty
    .env file: the CLI looks for a .env file in the working folder and in every folder above it, and stops at
    this one (on Windows the temporary folder is inside the home folder, where an everyday .env may be)."""
    d = Path(tempfile.mkdtemp(prefix="uzblimp_gemini_"))
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    (d / "work").mkdir()
    (d / ".env").write_text("", encoding="utf-8")
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
    """One headless request: the prompt on standard input (as UTF-8 bytes, so that its line ends stay as they are
    on every system), JSON output with the CLI's statistics."""
    cmd = gemini() + ["--skip-trust", "--policy", str(policy), "-o", "json"] + (["-m", model] if model else [])
    t = time.time()
    try:
        p = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, cwd=work, env=cli_env(),
                           timeout=timeout)
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        code, out, err = "timeout", e.stdout or b"", e.stderr or b""
    out, err = out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
    obj = last_json(out) or last_json(err) or {}
    stats = obj.get("stats") or {}
    models = stats.get("models") or {}
    main = sorted(m for m, s in models.items() if "main" in (s.get("roles") or {})) or \
        sorted(m for m, s in models.items() if ((s.get("tokens") or {}).get("candidates") or 0) > 0)
    return {"cmd": ["gemini"] + ["<policy>" if c == str(policy) else c for c in cmd[2:]], "returncode": code,
            "stdout": out[-20000:], "stderr": err[-4000:], "seconds": round(time.time() - t, 1),
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "text": obj.get("response") or "",
            "error": obj.get("error"), "stats": stats or None,
            "tool_calls": (stats.get("tools") or {}).get("totalCalls"),
            "models_used": sorted(models), "main_models": main}


def cli_message(rec):
    """The CLI's own error message, without its stack trace and its advice about Google Cloud projects."""
    err = rec.get("error")
    msg = err.get("message") if isinstance(err, dict) else (str(err) if err else "")
    lines = [x for x in (rec["stderr"] + "\n" + rec["stdout"][-2000:]).splitlines()
             if x.strip() and not re.match(r"\s+at |\s*[{}\[\]]|\s*\"", x)]
    text = TIP.sub("", (msg or "") + "\n" + "\n".join(lines))
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).strip()  # without terminal colours


def stop_on_error(rec, where, model):
    """Ends the run on errors that another attempt cannot fix, with the CLI's own message below."""
    msg = cli_message(rec)
    probe = re.sub(r"\S*[/\\]\S*", " ", msg)  # without paths and links, whose digits are not error codes
    for pattern, text in STOPS:
        if re.search(pattern, probe, re.I):
            first = next((x.strip() for x in msg.splitlines() if x.strip()), "")
            link = re.search(r"validationLink: '([^']+)'", rec["stderr"])
            link = (f"open {link.group(1)} in your browser, signed in with the same account, and then run the "
                    "same command again." if link else
                    "run python scripts/gemini_cli_fc.py login, type a short message such as hi in the CLI, "
                    "and follow the link it shows; then run the same command again.")
            sys.exit(text.format(where=where, model=model, link=link) + f"\n  The CLI said: {first[:300]}")


def same_model(answered, model):
    """The model asked for, or a dated version of it (gemini-x-001, gemini-x-2026-05-12)."""
    return answered == model or re.fullmatch(re.escape(model) + r"-\d[\w.\-]*", answered or "") is not None


def judge(rec):
    """The answers of a saved reply as a string of digits, or None and why the reply cannot be used."""
    if rec.get("tool_calls"):
        return None, f"the model tried {rec['tool_calls']} tool call(s); not kept"
    ans = parse(rec.get("text"))
    return (ans, None) if ans else (None, f"no complete list of {fc.N} answers in the reply")


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
                    if not isinstance(i, int) or not 1 <= i <= n or out[i - 1] or v not in (1, 2) \
                            or isinstance(v, bool) or not isinstance(v, int):
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


def prompt_for(plan, alphabet, pass_, b):
    return fc.render(fc.items(plan, alphabet, b), pass_) + FORMAT_LINE.format(n=fc.N)


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def request(model, alphabet, pass_, b, plan, work, policy, cli):
    """One batch: the first usable saved reply, else up to ATTEMPTS new requests. Returns (answers or None, record,
    try number, CLI calls made). Exits on errors that another attempt cannot fix."""
    prompt = prompt_for(plan, alphabet, pass_, b)
    where = f"{alphabet} {pass_}{b + 1}"
    stem = f"{slug(model)}_{alphabet}_{pass_}{b + 1}_try"
    tries = sorted(int(m.group(1)) for f in CACHE.glob(stem + "*.json")
                   if (m := re.fullmatch(re.escape(stem) + r"(\d+)\.json", f.name)))
    for k in tries:
        rec = json.loads((CACHE / f"{stem}{k}.json").read_text(encoding="utf-8"))
        ans, _ = judge(rec)
        if ans:
            return ans, rec, k, 0
    if tries:
        print(f"  {where}: {len(tries)} earlier repl{'y' if len(tries) == 1 else 'ies'} without a usable answer; "
              "asking again")
    k, calls = max(tries, default=0), 0
    for _ in range(ATTEMPTS):
        rec = ask(model, prompt, work, policy)
        calls += 1
        rec.update(chars=len(prompt), sha256=sha256(prompt), cli_version=cli)
        if rec["returncode"] != 0 or rec.get("error"):
            stop_on_error(rec, where, model)
            first = next((x for x in cli_message(rec).splitlines() if x.strip()), "")
            print(f"  {where}: the CLI failed (exit {rec['returncode']}): {first[:300]}")
            continue  # not saved: the next attempt asks again
        wrong = [m for m in rec["main_models"] if not same_model(m, model)]
        if wrong:
            sys.exit(f"{where} was answered by {', '.join(wrong)}, not by {model}; nothing of this request is kept. "
                     "Give --model the full model name as `models` lists it (not a short name such as pro or "
                     "flash). If the model named here is the one you want, give its name to --model.")
        k += 1
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f"{stem}{k}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        ans, why = judge(rec)
        if ans:
            return ans, rec, k, calls
        print(f"  {where} try {k}: {why}")
    return None, None, k, calls


def setup():
    """Installs the CLI of these runs (VERSION) in CLI_DIR with npm; nothing else on the computer is changed."""
    p = subprocess.run([node(), "--version"], capture_output=True, text=True)
    major = re.match(r"v(\d+)", p.stdout.strip())
    if not major or int(major.group(1)) < 20:
        sys.exit(f"Node.js {p.stdout.strip() or '?'} is too old: the Gemini CLI needs version 20 or newer "
                 "(nodejs.org).")
    npm = shutil.which("npm")
    if not npm:
        sys.exit("npm was not found. It comes with Node.js: reinstall Node.js 20 or newer and open a new terminal.")
    CLI_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Installing Gemini CLI {VERSION} in {CLI_DIR} ...", flush=True)
    p = subprocess.run([npm, "install", "--prefix", str(CLI_DIR), "--save-exact", "--no-fund", "--no-audit",
                        "--no-update-notifier", f"@google/gemini-cli@{VERSION}"])
    if p.returncode != 0:
        sys.exit("npm could not install the Gemini CLI (see its messages above).")
    v = version()
    print(f"Gemini CLI {v} is installed for these runs." if v == VERSION else
          f"Something went wrong: the installed CLI reports version {v}, not {VERSION}.")


def login():
    gemini()
    prepare_profile(forget_sign_in=True)
    work, _ = folders()
    print(f"Profile folder for these runs: {PROFILE}\n\n"
          "The Gemini CLI opens now, in this terminal:\n"
          "  1. Choose 'Sign in with Google' (arrow keys and Enter).\n"
          "  2. When it asks whether to open the authentication page in your browser, choose Yes.\n"
          "  3. In the browser, sign in with the Google account of your Google AI Pro subscription and allow\n"
          "     access.\n"
          "  4. Back here, when the CLI says it needs to be restarted, press R.\n"
          "  5. When its input box appears, type /quit and press Enter.\n")
    input("Press Enter to open the Gemini CLI...")
    subprocess.run(gemini() + ["--skip-trust"], cwd=work, env=cli_env(login=True))
    problem = sign_in_problem()
    print("\nSigned in with your Google account: the login is saved in the profile folder." if not problem else
          "\n" + problem.replace("Run: python scripts/gemini_cli_fc.py login", "Run login again"))


def models():
    prepare_profile()
    work, _ = folders()
    p = subprocess.run(gemini() + ["--list-models", "--skip-trust"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=work, env=cli_env())
    print((p.stdout or p.stderr).strip())
    print("\nGive --model the name in brackets of the model you want. Short names such as pro or flash are not "
          "accepted, because they can stand for different models.")


def check(model):
    prepare_profile()
    v = version()
    print(f"Gemini CLI {v}" + ("" if v == VERSION else f": these runs need {VERSION}. Run: "
                                                     "python scripts/gemini_cli_fc.py setup"))
    problem = sign_in_problem()
    print(f"Profile folder: {PROFILE}; sign-in: " + ("Google account" if not problem else problem))
    if problem or v != VERSION:
        return
    work, policy = folders()
    rec = ask(model, "Reply with the single word OK.", work, policy, timeout=600)
    print(f"exit {rec['returncode']} | reply: {rec['text'].strip()[:60]!r} | answered by: {rec['main_models']} | "
          f"tool calls: {rec['tool_calls']}")
    if rec["returncode"] != 0 or rec.get("error"):
        print(cli_message(rec)[:800])
    elif model and not all(same_model(m, model) for m in rec["main_models"]):
        print(f"Not answered by {model}: give --model the full model name as `models` lists it.")
    else:
        print("Ready.")


def run(model, alphabets, passes, batches, pause):
    problem = sign_in_problem()
    if problem:
        sys.exit(problem)
    prepare_profile()
    cli = version()
    if cli != VERSION:
        sys.exit(f"This is Gemini CLI {cli}; these runs need {VERSION}. Run: python scripts/gemini_cli_fc.py setup")
    plan = fc.load_plan()
    work, policy = folders()
    print(f"Gemini CLI {cli}, signed in with your Google account, model {model}", flush=True)
    jobs = [(a, p, b) for a in alphabets for p in passes for b in batches]
    results = {}
    try:
        for n, (a, p, b) in enumerate(jobs, 1):
            ans, rec, k, calls = request(model, a, p, b, plan, work, policy, cli)
            results[(a, p, b)] = (ans, rec, k)
            key = "".join("1" if (it["first_in_A"] == "grammatical") == (p == "A") else "2" for it in plan["batches"][b])
            acc = f"{100 * sum(x == y for x, y in zip(ans, key)) / fc.N:.1f}%" if ans else "no usable answer"
            print(f"[{n}/{len(jobs)}] {a} {p}{b + 1}: {acc}" + ("" if not rec else f" ({rec.get('seconds')} s, "
                  f"answered by {', '.join(rec.get('main_models') or []) or '?'})"), flush=True)
            if calls and n < len(jobs):
                time.sleep(pause)
    except KeyboardInterrupt:
        print("\nStopped. Every answer so far is saved; run the same command to continue.")
    finally:
        write_runs(model, alphabets, passes, batches, results)
    missing = [f"{a} {p}{b + 1}" for (a, p, b), (ans, _, _) in results.items() if not ans]
    if missing:
        print(f"Without a usable answer so far: {', '.join(missing)}. Run the same command again to ask "
              f"{'it' if len(missing) == 1 else 'them'} again.")


def write_runs(model, alphabets, passes, batches, results):
    for a in alphabets:
        rows = []
        for p in passes:
            for b in batches:
                if (a, p, b) not in results:
                    continue
                ans, rec, k = results[(a, p, b)]
                rec = rec or {}
                rows.append({"pass": p, "batch": b, "attempts": k, "chars": rec.get("chars"),
                             "sha256": rec.get("sha256"), "answers": ans, "usage": rec.get("stats"),
                             "provider": "gemini-cli", "cli_version": rec.get("cli_version"),
                             "time": rec.get("time"), "models_used": rec.get("models_used"),
                             "main_models": rec.get("main_models")})
        if rows:
            (OUT / "runs").mkdir(parents=True, exist_ok=True)
            f = OUT / "runs" / f"{slug(model)}_{a}.json"
            old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            keep = {(r["pass"], r["batch"]): r for r in old.get("results", [])}
            # a saved answer is never replaced by a batch that has none
            keep.update({(r["pass"], r["batch"]): r for r in rows
                         if r["answers"] or not (keep.get((r["pass"], r["batch"])) or {}).get("answers")})
            versions = sorted({r["cli_version"] for r in keep.values() if r.get("cli_version")})
            res = {"model": slug(model), "model_id": model, "endpoint": "gemini-cli", "alphabet": a,
                   "effort": "CLI default", "cli_versions": versions,
                   "results": sorted(keep.values(), key=lambda r: (r["pass"], r["batch"]))}
            f.write_text(json.dumps(res, indent=1), encoding="utf-8")


def collect():
    """One row per answered pair and order (results/chat/gemini_cli/<model>_<alphabet>.csv), in benchmark order,
    and a list of the batches without an answer."""
    import pandas as pd
    plan = fc.load_plan()
    nb = len(plan["batches"])
    for f in sorted((OUT / "runs").glob("*.json")):
        res = json.loads(f.read_text(encoding="utf-8"))
        d = fc.bench(res["alphabet"]).set_index("id")
        rows, done = [], {}
        for r in res["results"]:
            assert r["pass"] in ("A", "B"), f"{f.name}: unknown pass {r['pass']!r}"
            if not r["answers"]:
                continue
            prompt = prompt_for(plan, res["alphabet"], r["pass"], r["batch"])
            assert (r.get("sha256") or sha256(prompt)) == sha256(prompt) and r["chars"] == len(prompt), \
                f"{f.name}: the prompt of {r['pass']}{r['batch'] + 1} differs from the benchmark's"
            done.setdefault(r["pass"], set()).add(r["batch"])
            for i, it in enumerate(plan["batches"][r["batch"]]):
                good_first = (it["first_in_A"] == "grammatical") == (r["pass"] == "A")
                ans = int(r["answers"][i])
                rows.append({"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"], "good": d.at[it["id"], "grammatical"],
                             "bad": d.at[it["id"], "ungrammatical"], "batch": r["batch"] + 1, "item": i + 1,
                             "order": "gb" if good_first else "bg", "answer": ans, "correct": ans == (1 if good_first else 2),
                             "attempts": r["attempts"], "main_model": ",".join(r.get("main_models") or []),
                             "models_used": ",".join(r.get("models_used") or []), "cli_version": r.get("cli_version"),
                             "model": res["model"], "alphabet": res["alphabet"]})
        for p in sorted({r["pass"] for r in res["results"]} | set(done)):
            left = [f"{p}{b + 1}" for b in range(nb) if b not in done.get(p, set())]
            print(f"{f.name}: pass {p}: {len(done.get(p, ())) * fc.N} of {nb * fc.N} pairs" +
                  (f"; no answer yet for {', '.join(left)}" if left else ""))
        if not rows:
            print(f"{f.name}: no answers yet; nothing written")
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
    sub.add_parser("setup")
    sub.add_parser("login")
    sub.add_parser("models")
    c = sub.add_parser("check")
    c.add_argument("--model", help="the model to test (default: the CLI's default)")
    for name in ("trial", "run"):
        s = sub.add_parser(name)
        s.add_argument("--model", required=True, help="a full model name, as `models` lists it")
        if name == "run":
            s.add_argument("--passes", default="A", type=str.upper, choices=["A", "B", "AB"],
                           help="A (one order, as the OpenRouter runs) or AB (both orders)")
            s.add_argument("--alphabets", default=",".join(fc.FILES), help=f"some of {', '.join(fc.FILES)}")
            s.add_argument("--pause", type=float, default=15, help="seconds between requests")
    sub.add_parser("collect")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "setup":
        setup()
    elif args.cmd == "login":
        login()
    elif args.cmd == "models":
        models()
    elif args.cmd == "check":
        check(args.model)
    elif args.cmd == "trial":
        run(args.model, ["latn"], "A", [0], 0)
    elif args.cmd == "run":
        alphabets = [a.strip() for a in args.alphabets.split(",") if a.strip()]
        unknown = [a for a in alphabets if a not in fc.FILES]
        if unknown or not alphabets:
            p.error(f"--alphabets: {', '.join(unknown) or 'none given'}; choose from {', '.join(fc.FILES)}")
        run(args.model, alphabets, args.passes, range(16), args.pause)
    else:
        collect()


if __name__ == "__main__":
    main()
