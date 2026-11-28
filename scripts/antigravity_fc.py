"""Forced choice with Gemini models in Google Antigravity (the agent, signed in with your Google account): the
question files of the Codex runs, one conversation per file. results/chat/antigravity/README.md is the step-by-step
guide; `kit` puts a copy of it in the kit folder as HOW_TO.md, with this kit's commands at the top.

`kit` writes a folder outside this repository (the repository holds the answers):

    <kit>/questions/batch_01.txt ... batch_96.txt   the question files of scripts/codex_fc.py, unchanged
    <kit>/prompts/01_batch_01.txt ... 96_batch_96.txt  one prompt per conversation, in the order to run them
    <kit>/workspace/                                   the folder opened in Antigravity: questions/ and answers/
    <kit>/answers/                                     the checked answer files
    <kit>/HOW_TO.md, kit.json, log.csv, rejected/, transcripts/, audit.csv

For each conversation `go` copies only that conversation's question file into workspace/questions/, so the agent
can see no other question file (the same pairs appear in six files) and no earlier answer. The prompt keeps the
wording of the Codex prompt (codex_fc.PROMPT), narrowed to one file, with one added paragraph (EXTRA) against
helpers, the terminal, the browser, web search and subagents. The order is pass A in all three alphabets first
(files 01, 33, 65, 02, 34, 66, ...), then pass B. After the conversation, `go` checks the answer file, sets aside
any other file the agent wrote, reads the conversation's transcript (Antigravity keeps it in
~/.gemini/antigravity*/brain/<conversation>/) to list every tool the agent used, asks you to confirm, and moves the
answer out of the workspace into <kit>/answers/. `collect` checks the transcripts once more and writes the results.

    python scripts/antigravity_fc.py kit ../uzblimp-antigravity-hydrogen --model "Gemini 4 Hydrogen" --level Low
    python scripts/antigravity_fc.py go ../uzblimp-antigravity-hydrogen       # one conversation after another
    python scripts/antigravity_fc.py check ../uzblimp-antigravity-hydrogen    # what is done, and what comes next
    python scripts/antigravity_fc.py audit ../uzblimp-antigravity-hydrogen    # tools used in every conversation
    python scripts/antigravity_fc.py collect ../uzblimp-antigravity-hydrogen  # per-pair files in results/chat/antigravity/
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude_fc as fc  # noqa: E402
import codex_fc  # noqa: E402
import manual_fc as mf  # noqa: E402

KIND = "antigravity"
OUT = fc.ROOT / "results" / "chat" / "antigravity"
GUIDE = OUT / "README.md"
BRAINS = [Path.home() / ".gemini" / d / "brain" for d in ("antigravity", "antigravity-ide", "antigravity-cli")]
EXTRA = ("Read each pair in full. Do not write helpers that shorten, diff or pre-process the pairs, and do not use the "
         "terminal, the browser, web search or subagents: use only your file tools, to read {q} and to write {a}.")
READ_TOOLS = {"view_file", "read_file", "view_file_outline", "view_code_item", "read_many_files"}
WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "create_file", "edit_file",
               "write_file"}
ARG_KEYS = ("args", "arguments", "input", "parameters", "toolInput", "tool_input", "argsJson", "argumentsJson",
            "args_json", "toolArgs", "functionArgs", "params")
CALL_KEYS = ("functionCall", "function_call", "toolCall", "tool_call")
FORBIDDEN = re.compile(r"command|terminal|shell|search|url|browser|subagent|mcp|execut|python|code_exec|fetch|web",
                       re.I)
LINE = re.compile(r"^\s*(\d+)\s*:\s*([12])\s*$")
MODEL_NAME = re.compile(r"gemini[-_ ]\d+(?:\.\d+)?[-_ ](?:flash|pro|hydrogen|neon|carbon|argon)[\w.\-]*", re.I)
RANK = {"OK": 0, "CHECK": 1, "UNKNOWN": 2, "BAD": 3}


def prompt(n):
    """The prompt of the conversation for questions/batch_<n>.txt."""
    q, a = f"questions/batch_{n:02d}.txt", f"answers/batch_{n:02d}.txt"
    return f"""You judge the grammaticality of Uzbek sentences.

The file {q} has {fc.N} numbered items. Each item has two Uzbek sentences, labelled 1 and 2. For each item: which of the two sentences is grammatically correct? Exactly one of them is.

Answer from your own knowledge of Uzbek and judge each item on its own. Read only the question file {q}. Do not run code or scripts to decide your answers. Do not search the web. Do not look anything up. Do not read any other files.

{EXTRA.format(q=q, a=a)}

Write {a} with an answer for every item from 1 to {fc.N}, even when you are unsure. Write only lines in this format, and nothing else:

1: 1
2: 2
3: 1

Each line is the item number, a colon, a space, and then 1 or 2 (the number of the grammatically correct sentence). No explanations.

Do only this one file in this conversation, and then stop."""


def requests(plan):
    """(conversation number, question file number, pass, alphabet, batch index), in the order to run them."""
    return [(k, codex_fc.batch_number(codex_fc.BLOCKS.index((a, p)), b), p, a, b)
            for k, (p, a, b) in enumerate(mf.run_order(plan), 1)]


def header(folder, settings):
    """This kit's commands, put at the top of its HOW_TO.md."""
    f = f'"{folder}"'
    return (f"# This kit: {settings['model']}, thinking level {settings['level']}\n\n"
            f"Kit folder: `{folder}`. Open only `{folder / 'workspace'}` in Antigravity. Run these commands in a "
            f"terminal in the uzblimp folder (`cd \"{fc.ROOT}\"`), not in Antigravity's own terminal (use `py` if "
            f"`python` is not found):\n\n```\npython scripts/antigravity_fc.py go {f}\npython scripts/antigravity_fc.py "
            f"check {f}\npython scripts/antigravity_fc.py collect {f}\n```\n\nThe guide below uses the folder and model "
            f"of its examples; use the ones above.\n\n")


def kit(folder, model, level, alias):
    folder = mf.outside_repo(folder)
    plan = fc.load_plan()
    for sub in ("questions", "prompts", "answers", "workspace/questions", "workspace/answers"):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    for k, n, p, a, b in requests(plan):
        (folder / "questions" / f"batch_{n:02d}.txt").write_text(codex_fc.question_file(plan, a, p, b),
                                                                  encoding="utf-8")
        (folder / "prompts" / f"{k:02d}_batch_{n:02d}.txt").write_text(prompt(n) + "\n", encoding="utf-8")
    settings = dict(kind=KIND, model=model, level=level, alias=alias or mf.slug(model))
    mf.save_settings(folder, **settings)
    settings = json.loads((folder / "kit.json").read_text(encoding="utf-8"))
    guide = GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else ""
    (folder / "HOW_TO.md").write_text(header(folder, settings) + guide, encoding="utf-8")
    print(f"Wrote {folder}: {len(requests(plan))} question files, one prompt per conversation and HOW_TO.md.\n"
          f"Open only {folder / 'workspace'} in Antigravity. Then run: python scripts/antigravity_fc.py go \"{folder}\"")


def read_answer(path):
    """(answers as a string of N digits, None) for a valid answer file, else (None, what is wrong)."""
    if not path.exists():
        return None, "missing"
    got = {}
    for line in mf.read_text(path).splitlines():
        if not line.strip():
            continue
        m = LINE.match(line)
        if not m:
            return None, f"not an answer line: {line.strip()[:40]!r}"
        i = int(m.group(1))
        if i in got:
            return None, f"item {i} answered twice"
        got[i] = m.group(2)
    if set(got) != set(range(1, fc.N + 1)):
        return None, f"{len(got)} items, not 1 to {fc.N}"
    return "".join(got[i] for i in range(1, fc.N + 1)), None


def status(folder, plan):
    """Per request: (k, n, pass, alphabet, batch, answers or None, why). An answer counts only when go kept it: it is
    in <kit>/answers/ and the log's last line about it says kept, with the same checksum."""
    ok = mf.kept(folder)
    out = []
    for k, n, p, a, b in requests(plan):
        f = folder / "answers" / f"batch_{n:02d}.txt"
        ans, why = read_answer(f)
        if ans and ok.get(f"batch_{n:02d}") != mf.sha256(mf.read_text(f)):
            ans, why = None, "not kept by go (no matching line in log.csv)"
        out.append((k, n, p, a, b, ans, why))
    return out


def norm(text):
    """Text with backslashes as slashes, URL escapes decoded and in lower case, to find paths in a transcript."""
    return urllib.parse.unquote(text).replace("\\\\", "/").replace("\\", "/").lower()


def ws_keys(folder, settings):
    """The spellings of the workspace path that a transcript may use."""
    keys = {norm(str(folder / "workspace")), norm(os.path.realpath(folder / "workspace"))}
    if settings.get("workspace"):
        keys.add(norm(settings["workspace"]))
    return sorted({k.rstrip("/") for k in keys}, key=len, reverse=True)


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def mentions(path, keys):
    """True when the transcript names the workspace, also inside JSON strings with \\u escapes."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if any(k in norm(text) for k in keys):
        return True
    for line in text.splitlines():
        try:
            if any(k in norm(s) for s in strings(json.loads(line)) for k in keys):
                return True
        except ValueError:
            continue
    return False


def brain_folders():
    return {d for b in BRAINS if b.is_dir() for d in b.iterdir() if d.is_dir()}


def transcript_of(d):
    return d / ".system_generated" / "logs" / "transcript.jsonl"


def all_transcripts(extra, skip):
    """Every transcript in Antigravity's folders, or every .jsonl file under the folder given with --transcripts."""
    if not extra:
        return sorted((t for d in brain_folders() if (t := transcript_of(d)).exists()), key=lambda f: f.stat().st_mtime)
    files = [f for f in Path(extra).rglob("*.jsonl") if skip not in f.parents]
    return sorted(files, key=lambda f: f.stat().st_mtime)


def conversation_id(path):
    return path.parents[2].name if path.match("*/.system_generated/logs/transcript.jsonl") else path.stem


def tool_calls(obj, out, parent=None):
    """Collects (tool name, arguments) from any JSON structure that looks like a tool call."""
    if isinstance(obj, dict):
        name = next((obj[k] for k in ("name", "toolName", "tool_name", "tool") if isinstance(obj.get(k), str)), None)
        key = next((k for k in ARG_KEYS if k in obj), None)
        is_call = parent in CALL_KEYS or obj.get("type") in ("tool_use", "function_call")
        if name and (key or is_call) and re.fullmatch(r"[A-Za-z_][\w.:\-/]*", name):
            args = obj[key] if key else {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    pass
            schema = isinstance(args, dict) and ("properties" in args or str(args.get("type")).lower() == "object")
            declaration = schema or (key == "parameters" and args == {} and "description" in obj)
            if not declaration:
                out.append((name, args))
        for k, v in obj.items():
            tool_calls(v, out, k)
    elif isinstance(obj, list):
        for v in obj:
            tool_calls(v, out, parent)


def paths(args, keys, conv):
    """The distinct file paths among a tool call's arguments: relative to the workspace when inside it,
    '<conversation>/...' when in the conversation's own folder, else without the home folder."""
    home = norm(str(Path.home())).rstrip("/")
    out = set()
    for s in strings(args):
        if "\n" in s:
            continue
        t = norm(s.strip())
        key = next((k for k in keys if k in t), None)
        if key:
            t = t.split(key, 1)[1].lstrip("/") or "."
        elif conv in t:
            t = "<conversation>/" + t.split(conv, 1)[1].lstrip("/")
        elif t.startswith(("./", "questions/", "answers/")):
            t = t.removeprefix("./")
        elif t.startswith(("/", "file:")) or re.match(r"[a-z]:/", t):
            out.add(t.replace(home, "~"))
            continue
        else:
            continue
        if not re.search(r"\s", t):  # a sentence that mentions a path is not a path
            out.add(t)
    return sorted(out)


def first_last(n, folder):
    """The sentences of the first and the last item of a question file, to see whether the agent saw all of it."""
    text = mf.read_text(folder / "questions" / f"batch_{n:02d}.txt")
    items = re.findall(r"(?m)^Item \d+\n1\. (.*)\n2\. (.*)$", text)
    return (items[0], items[-1]) if items else (None, None)


def analyse(path, keys, folder=None):
    """What one transcript shows: question files read, own answer files viewed, answer files written, calls of tools
    that are not allowed, file tools on other files, other calls, whether the whole question file was seen, and the
    model names it mentions."""
    calls, seen, texts = [], set(), []
    raw = path.read_text(encoding="utf-8", errors="replace")
    for line in raw.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        texts.extend(strings(obj))
        found = []
        tool_calls(obj, found)
        for name, args in found:
            sig = (name, json.dumps(args, sort_keys=True, ensure_ascii=False, default=str))
            if sig not in seen:
                seen.add(sig)
                calls.append((name, args))
    conv = norm(str(path.parents[2])).rstrip("/") + "/" if path.match("*/.system_generated/logs/transcript.jsonl") \
        else "\0"
    res = {"transcript": path, "conversation": conversation_id(path), "calls": len(calls), "read": set(),
           "looked": set(), "wrote": set(), "forbidden": [], "files": [], "other": [], "whole": None}
    home = norm(str(Path.home())).rstrip("/")
    for name, args in calls:
        rel = paths(args, keys, conv)
        shown = ", ".join(rel) if rel else norm(json.dumps(args, ensure_ascii=False, default=str)).replace(home, "~")
        for k in keys:
            shown = shown.replace(k, "<workspace>")
        label = f"{name}({shown[:120]})"
        short = name.split("/")[-1].split(".")[-1].split(":")[-1]
        m = [re.fullmatch(r"(questions|answers)/batch_(\d+)\.txt", r) for r in rel]
        if FORBIDDEN.search(name):
            res["forbidden"].append(label)
        elif short in READ_TOOLS and rel and all(m):
            for x in m:
                res["read" if x.group(1) == "questions" else "looked"].add(int(x.group(2)))
        elif short in WRITE_TOOLS and rel and all(x and x.group(1) == "answers" for x in m):
            res["wrote"] |= {int(x.group(2)) for x in m}
        elif (short in READ_TOOLS | WRITE_TOOLS) and rel and all(r.startswith("<conversation>/") for r in rel):
            res["other"].append(label)  # the agent's own notes (Planning mode), in its conversation folder
        elif short in READ_TOOLS | WRITE_TOOLS:
            res["files"].append(label)
        else:
            res["other"].append(label)
    for x in ("read", "looked", "wrote"):
        res[x] = sorted(res[x])
    if folder is not None and len(res["read"]) == 1:
        first, last = first_last(res["read"][0], folder)
        joined = "\n".join(texts)
        if first and all(s in joined for s in first):
            res["whole"] = all(s in joined for s in last)
    res["models"] = sorted({m.group(0).lower() for m in MODEL_NAME.finditer(raw)})
    return res


def verdict(res, n=None):
    """OK; BAD (a tool that is not allowed, another file read or written); CHECK (something this script cannot
    judge, worth a look); UNKNOWN (no tool call could be read from the transcript)."""
    if not res["calls"]:
        return "UNKNOWN"
    want = {n} if n is not None else set(res["read"][:1] or res["wrote"][:1])
    if res["forbidden"] or res["files"] or not set(res["read"]) <= want or not set(res["wrote"]) <= want \
            or not set(res["looked"]) <= want:
        return "BAD"
    if res["other"] or set(res["read"]) != want or set(res["wrote"]) != want or res["whole"] is False:
        return "CHECK"
    return "OK"


def summary(res):
    s = (f"read {', '.join(f'questions/batch_{x:02d}.txt' for x in res['read']) or 'no question file'}; "
         f"wrote {', '.join(f'answers/batch_{x:02d}.txt' for x in res['wrote']) or 'no answer file'}")
    if res["whole"] is False:
        s += "; the transcript shows only part of the question file"
    for kind, label in (("forbidden", "not allowed"), ("files", "other files"), ("other", "other")):
        if res[kind]:
            s += f"; {label}: {'; '.join(res[kind][:4])}" + (" ..." if len(res[kind]) > 4 else "")
    return s


def keep_transcript(folder, res, label):
    dest = folder / "transcripts"
    dest.mkdir(exist_ok=True)
    target, i = dest / f"{label}_{res['conversation']}.jsonl", 1
    while target.exists() and target.read_bytes() != res["transcript"].read_bytes():
        i += 1
        target = dest / f"{label}_{res['conversation']}_{i}.jsonl"
    shutil.copy2(res["transcript"], target)
    return target


def files_in(ws):
    """The files of the workspace, apart from hidden ones (Antigravity's or the editor's own, such as .agents/)."""
    return sorted(f for f in ws.rglob("*") if f.is_file() and not any(x.startswith(".") for x in f.relative_to(ws).parts))


def clean_workspace(ws, folder, settings, k=None, n=None, reason="left in the workspace, not checked by go"):
    """Sets aside every file in the workspace (an answer not checked, a helper) and removes go's question copies."""
    for f in files_in(ws):
        if f.parent == ws / "questions" and (folder / "questions" / f.name).exists() \
                and f.read_bytes() == (folder / "questions" / f.name).read_bytes():
            f.unlink()
            continue
        moved = mf.set_aside(f, folder)
        print(f"  {f.relative_to(ws).as_posix()} was {reason}: moved to {moved.relative_to(folder).as_posix()}")
        mf.log(folder, settings, n=k or "", request=f"batch_{n:02d}" if n else f"workspace/{f.relative_to(ws).as_posix()}",
               result="set aside", note=f"{f.relative_to(ws).as_posix()} {reason}")


def snapshot(ws):
    return {f: (f.stat().st_size, f.stat().st_mtime_ns) for f in files_in(ws)}


def changed(ws, before):
    return [f for f in files_in(ws) if before.get(f) != (f.stat().st_size, f.stat().st_mtime_ns)]


def check(folder):
    folder, settings = mf.load_settings(folder, KIND)
    st = status(folder, fc.load_plan())
    for p in "AB":
        part = [s for s in st if s[2] == p]
        print(f"pass {p}: {sum(1 for s in part if s[5])} of {len(part)} answer files done")
    for k, n, p, a, b, _, why in st:
        if why and why != "missing":
            print(f"  answers/batch_{n:02d}.txt ({mf.describe(p, a, b)}): {why}")
    nxt = next((s for s in st if not s[5]), None)
    print("All answer files are there. Next: collect." if not nxt else
          f"Next: conversation {nxt[0]}, batch_{nxt[1]:02d} ({mf.describe(*nxt[2:5])}).")


def audit(folder, transcripts=None, quiet=False):
    """Judges every transcript that names this kit's workspace and writes audit.csv. Returns its rows."""
    folder, settings = mf.load_settings(folder, KIND)
    keys = ws_keys(folder, settings)
    found = [f for f in all_transcripts(transcripts, folder / "transcripts") if mentions(f, keys)]
    rows = []
    log = mf.read_log(folder)
    for f in found:
        res = analyse(f, keys, folder)
        v = verdict(res)
        kept = keep_transcript(folder, res, "audit")
        used = [r["request"] for r in log if r["conversation"] and res["conversation"] in r["conversation"].split()]
        served = ", ".join(sorted(set(used))) or (", ".join(f"batch_{x:02d}" for x in res["read"]) if res["read"]
                                                  else "no batch (a test?)")
        if not quiet:
            print(f"{v:7} {res['conversation'][:12]} ({served}): {summary(res)}"
                  + (f" [models named: {', '.join(res['models'])}]" if res["models"] else ""))
        rows.append({"conversation": res["conversation"], "served": served, "verdict": v, "read": res["read"],
                     "wrote": res["wrote"], "not_allowed": " | ".join(res["forbidden"]),
                     "other_files": " | ".join(res["files"]), "other": " | ".join(res["other"]),
                     "whole_file": res["whole"], "models": ", ".join(res["models"]), "copy": kept.name})
    if rows:
        with open(folder / "audit.csv", "w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    if not quiet:
        if not rows:
            print("No transcript names this kit's workspace. Antigravity keeps them in ~/.gemini/antigravity/brain/ "
                  "(the IDE in ~/.gemini/antigravity-ide/brain/); give another folder with --transcripts.")
        elif any(r["verdict"] in ("UNKNOWN", "CHECK") for r in rows):
            print("UNKNOWN or CHECK: the transcript holds something this script cannot judge (perhaps a format it "
                  f"does not know). The copies are in {folder / 'transcripts'}: send one, so that it can be looked at.")
        if rows:
            print(f"Wrote {folder / 'audit.csv'}; copies of the transcripts are in {folder / 'transcripts'}.")
    return rows


def transcript_times():
    """Every conversation folder with the time its transcript last changed (0 when it has none yet)."""
    return {d: (transcript_of(d).stat().st_mtime_ns if transcript_of(d).exists() else 0) for d in brain_folders()}


def judge(folder, keys, n, before, logged):
    """The verdict on the conversation just held: the transcripts of conversations that are new or changed since the
    step began, were not judged before, name the workspace and are about batch n. Returns (verdict, results)."""
    res = []
    for d, t in transcript_times().items():
        if not t or d.name in logged or before.get(d) == t:
            continue
        if mentions(transcript_of(d), keys):
            r = analyse(transcript_of(d), keys, folder)
            if n in r["read"] or n in r["wrote"] or not (r["read"] or r["wrote"]):
                res.append(r)
    if not res:
        return "UNKNOWN", []
    return max((verdict(r, n) for r in res), key=RANK.get), res


def describe_check(v, res, stray, ws, n):
    if not res:
        text = "no transcript found"
    elif len(res) == 1:
        text = summary(res[0])
    else:
        text = " | ".join(f"conversation {r['conversation'][:8]}: {verdict(r, n)}: {summary(r)}" for r in res)
    return f"{v}: {text}" + "".join(f"; also wrote {f.relative_to(ws).as_posix()}" for f in stray)


def go(folder):
    folder, settings = mf.load_settings(folder, KIND)
    ws, model, level = folder / "workspace", settings["model"], settings["level"]
    keys = ws_keys(folder, settings)
    plan = fc.load_plan()
    print(f"Kit for {model}, thinking level {level}. Open only this folder in Antigravity:\n  {ws}")
    if not any(s[5] for s in status(folder, plan)) and not mf.ask(
            "Have you made the settings and the test conversation of HOW_TO.md (steps 2 to 4)?", default="n"):
        sys.exit(f"Do those first: {folder / 'HOW_TO.md'}")
    clip = mf.Clipboard()
    (ws / "questions").mkdir(parents=True, exist_ok=True)
    (ws / "answers").mkdir(exist_ok=True)
    hidden = sorted({f.relative_to(ws).parts[0] for f in ws.rglob("*") if f.relative_to(ws).parts[0].startswith(".")})
    if hidden:
        print(f"  The workspace has {', '.join(hidden)} (Antigravity's or yours); go leaves it alone. Make sure it holds "
              "no rules, skills or other instructions (for example .agents/rules/).")
    while True:
        clean_workspace(ws, folder, settings)
        st = status(folder, plan)
        todo = next((s for s in st if not s[5]), None)
        if not todo:
            print(f"All answer files are there. Next: python scripts/antigravity_fc.py collect \"{folder}\"")
            return
        k, n, p, a, b, _, why = todo
        name = f"batch_{n:02d}.txt"
        src = folder / "questions" / name
        if src.read_text(encoding="utf-8") != codex_fc.question_file(plan, a, p, b):
            sys.exit(f"{src} differs from the benchmark (was it changed, or the benchmark since the kit was made?). "
                     "Make a new kit.")
        if (folder / "answers" / name).exists():  # an answer file that go did not keep
            print(f"  answers/{name} was not usable ({why}): moved to {mf.set_aside(folder / 'answers' / name, folder)}")
        shutil.copy2(src, ws / "questions" / name)
        answer = ws / "answers" / name
        head = f"\n[{k}/{len(st)}] batch_{n:02d} ({mf.describe(p, a, b)}); {sum(1 for s in st if s[5])} done"
        if clip.ok:
            clip.put(prompt(n))
            print(f"{head}. The prompt is on the clipboard.")
        else:
            print(f"{head}. Open {folder / 'prompts' / f'{k:02d}_{name}'} and copy all of it.")
        print(f"  In Antigravity: a NEW conversation, Fast mode (not Planning); model {model}, thinking level {level}"
              f" (check both); paste; send.\n  Approve reading questions/{name} and writing answers/{name}; if it "
              "shows a plan or asks whether to go on, tell it to go on; deny anything else.")
        times, before = transcript_times(), snapshot(ws)
        logged = {c for r in mf.read_log(folder) for c in r["conversation"].split()}
        try:
            while True:
                stop = input("  When the agent has finished, press Enter (q = stop): ").strip().lower() == "q"
                ans, why = read_answer(answer)
                if ans or stop:
                    break
                give_up = input(f"  answers/{name}: {why}. If the agent is still working, wait and press Enter again. "
                                f"If it stopped early, tell it in the same conversation: Go on: write all {fc.N} lines "
                                f"of answers/{name}. (n = give up this conversation) ").strip().lower()
                if give_up == "n":
                    convs = " ".join(r["conversation"] for r in judge(folder, keys, n, times, logged)[1])
                    mf.log(folder, settings, n=k, request=f"batch_{n:02d}", result="given up", conversation=convs,
                           note=why)
                    break
            if not ans:  # nothing usable: what is there is set aside, and the same file comes again
                clean_workspace(ws, folder, settings, k, n, "not complete")
                if stop:
                    print("  Stopped. Run go again to continue.")
                    return
                continue
            stray = [f for f in changed(ws, before) if f != answer]
            v, res = judge(folder, keys, n, times, logged)
            if stray:
                v = "BAD"
            for r in res:
                keep_transcript(folder, r, f"{k:02d}_batch_{n:02d}")
            tools = describe_check(v, res, stray, ws, n)
            print(f"  Transcript: {tools}")
            if v in ("UNKNOWN", "CHECK"):
                print("  (This script cannot judge everything here. The answer can still be kept; collect checks "
                      "the transcripts again.)")
            yes, note = mf.confirm(f"  Was everything right: the picker showed {model}, {level}, and the agent only "
                                   f"read questions/{name} and wrote answers/{name} (no command, search, web page or "
                                   "other file, not even one you denied)? Type y or n, a note may follow:")
            convs = " ".join(r["conversation"] for r in res)
            if v == "BAD" or not yes:
                moved = mf.set_aside(answer, folder)
                print(f"  Not used: moved to {moved.relative_to(folder).as_posix()}. This file is asked again, in a new "
                      "conversation.")
                mf.log(folder, settings, n=k, request=f"batch_{n:02d}", result="set aside", conversation=convs,
                       tools=tools, note=note)
            else:
                text = mf.read_text(answer)
                shutil.move(str(answer), str(folder / "answers" / name))
                mf.log(folder, settings, n=k, request=f"batch_{n:02d}", result="kept", sha256=mf.sha256(text),
                       conversation=convs, tools=tools, note=note)
                print(f"  Kept: answers/{name}.")
        except KeyboardInterrupt:
            print("\n  Stopped. This conversation's answer, if any, is set aside; run go again to continue.")
            clean_workspace(ws, folder, settings, k, n, "not checked (stopped)")
            return
        if stop:
            clean_workspace(ws, folder, settings)
            print("  Stopped. Run go again to continue.")
            return


def collect(folder):
    folder, settings = mf.load_settings(folder, KIND)
    alias = settings["alias"]
    plan = fc.load_plan()
    mf.claim_alias(OUT, alias, settings)
    rows = audit(folder, quiet=True)
    bad = {}
    for r in rows:  # a conversation that go could not judge, found BAD now
        for req in (r["served"].split(", ") if r["verdict"] == "BAD" else []):
            bad.setdefault(req, []).append(r["conversation"])
    log = mf.read_log(folder)
    judged = {c for row in log for c in row["conversation"].split()}
    last = {}
    for row in log:
        last[row["request"]] = row
    for req, convs in bad.items():
        row = last.get(req)
        own = set(row["conversation"].split()) if row else set()
        if row and row["result"] == "kept" and any(c in own or c not in judged for c in convs):
            moved = mf.set_aside(folder / "answers" / f"{req}.txt", folder)
            mf.log(folder, settings, request=req, result="set aside", conversation=" ".join(convs),
                   note="collect: a conversation about this file is BAD in its transcript")
            print(f"{req}: a conversation about it used something not allowed (see audit.csv); its answer was moved "
                  f"to {moved.relative_to(folder).as_posix()}. Run go to ask it again.")
    answers, sources, files = {}, {}, []
    for k, n, p, a, b, ans, why in status(folder, plan):
        if ans:
            if mf.read_text(folder / "questions" / f"batch_{n:02d}.txt") != codex_fc.question_file(plan, a, p, b):
                sys.exit(f"questions/batch_{n:02d}.txt differs from the benchmark: the benchmark or the kit changed "
                         f"since the kit was made (commit {settings.get('commit')}).")
            answers[(p, a, b)], sources[(p, a, b)] = ans, f"batch_{n:02d}.txt"
            files.append((folder / "answers" / f"batch_{n:02d}.txt", f"batch_{n:02d}.txt"))
        elif why and why != "missing":
            print(f"answers/batch_{n:02d}.txt not used: {why}")
    mf.write_results(OUT, alias, settings["model"], settings["level"], "antigravity", answers, sources)
    mf.keep_answers(OUT / f"{alias}_answers", files)
    for name in ("log.csv", "audit.csv"):
        if (folder / name).exists():
            mf.publish(folder / name, OUT / f"{alias}_{name}", folder)
        else:
            (OUT / f"{alias}_{name}").unlink(missing_ok=True)
    (OUT / f"{alias}_kit.json").write_text(json.dumps(settings, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit")
    k.add_argument("folder")
    k.add_argument("--model", required=True, help='the model as Antigravity names it, e.g. "Gemini 4 Hydrogen"')
    k.add_argument("--level", required=True, help="the thinking level you will choose, e.g. Low")
    k.add_argument("--alias", help="the name of the result files (default: from --model)")
    for name in ("go", "check", "audit", "collect"):
        s = sub.add_parser(name)
        s.add_argument("folder")
        if name == "audit":
            s.add_argument("--transcripts", help="a folder with the transcripts, if not in ~/.gemini/antigravity*/brain")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "kit":
        kit(args.folder, args.model, args.level, args.alias)
    elif args.cmd == "go":
        go(args.folder)
    elif args.cmd == "check":
        check(args.folder)
    elif args.cmd == "audit":
        audit(args.folder, args.transcripts)
    else:
        collect(args.folder)


if __name__ == "__main__":
    main()
