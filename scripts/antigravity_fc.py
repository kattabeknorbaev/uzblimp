"""Forced choice with Gemini models in Google Antigravity (the agent, signed in with your Google account): the
question files of the Codex runs, one conversation per file. results/chat/antigravity/README.md is the step-by-step
guide; `kit` puts a copy of it in the kit folder as HOW_TO.md.

`kit` writes a folder outside this repository (the repository holds the answers):

    <kit>/workspace/questions/batch_01.txt ... batch_96.txt   the question files of scripts/codex_fc.py, unchanged
    <kit>/workspace/answers/                                  the agent writes answers/batch_XX.txt here
    <kit>/prompts/01_batch_01.txt ... 96_batch_96.txt          one prompt per conversation, in the order to run them
    <kit>/HOW_TO.md, kit.json, log.csv

Only workspace/ is opened in Antigravity. Each prompt keeps the wording of the Codex prompt (codex_fc.PROMPT),
narrowed to one question file, with one added paragraph (EXTRA) against helpers, the terminal, the browser, web
search and subagents. The order is pass A in all three alphabets first (files 01, 33, 65, 02, 34, 66, ...), then
pass B, so a run stopped early has the same pairs in every alphabet. After each conversation, `go` checks the answer
file and reads the conversation's transcript, which Antigravity keeps in ~/.gemini/antigravity*/brain/, to list
every tool the agent used.

    python scripts/antigravity_fc.py kit ../uzblimp-antigravity-hydrogen --model "Gemini 4 Hydrogen" --level Low
    python scripts/antigravity_fc.py go ../uzblimp-antigravity-hydrogen       # one conversation after another
    python scripts/antigravity_fc.py check ../uzblimp-antigravity-hydrogen    # what is done, and what comes next
    python scripts/antigravity_fc.py audit ../uzblimp-antigravity-hydrogen    # tools used in every conversation
    python scripts/antigravity_fc.py collect ../uzblimp-antigravity-hydrogen  # per-pair files in results/chat/antigravity/
"""
import argparse
import csv
import json
import re
import shutil
import sys
import time
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
FORBIDDEN = re.compile(r"command|terminal|shell|search|url|browser|subagent|mcp|execut|python|code_exec|fetch|web",
                       re.I)
LINE = re.compile(r"^\s*(\d+)\s*:\s*([12])\s*$")
MODEL_NAME = re.compile(r"gemini[-_ ]\d+(?:\.\d+)?[-_ ](?:flash|pro|hydrogen|neon|carbon|argon)[\w.\-]*", re.I)


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


def kit(folder, model, level):
    folder = mf.outside_repo(folder)
    ws = folder / "workspace"
    if (ws / "answers").exists() and any((ws / "answers").iterdir()):
        sys.exit(f"{folder} already holds answers. Use a new folder for a new kit.")
    plan = fc.load_plan()
    (ws / "questions").mkdir(parents=True, exist_ok=True)
    (ws / "answers").mkdir(exist_ok=True)
    (folder / "prompts").mkdir(exist_ok=True)
    for k, n, p, a, b in requests(plan):
        (ws / "questions" / f"batch_{n:02d}.txt").write_text(codex_fc.question_file(plan, a, p, b), encoding="utf-8")
        (folder / "prompts" / f"{k:02d}_batch_{n:02d}.txt").write_text(prompt(n) + "\n", encoding="utf-8")
    if GUIDE.exists():
        shutil.copy2(GUIDE, folder / "HOW_TO.md")
    mf.save_settings(folder, kind=KIND, model=model, level=level, alias=mf.slug(model), workspace=str(ws))
    print(f"Wrote {folder}: {len(plan['batches']) * 6} question files in workspace/questions/ and one prompt per "
          f"conversation in prompts/.\nOpen only {ws} in Antigravity. Then run: python scripts/antigravity_fc.py go "
          f"\"{folder}\"")


def read_answer(path):
    """(answers as a string of N digits, None) for a valid answer file, else (None, what is wrong)."""
    if not path.exists():
        return None, "missing"
    got = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def status(ws, plan):
    return [(k, n, p, a, b, *read_answer(ws / "answers" / f"batch_{n:02d}.txt")) for k, n, p, a, b in requests(plan)]


def norm(text):
    """Text with backslashes as slashes, URL escapes decoded and in lower case, to find paths in a transcript."""
    return urllib.parse.unquote(text).replace("\\\\", "/").replace("\\", "/").lower()


def find_transcripts(ws, since=0.0, extra=None):
    """Transcripts (transcript.jsonl) that mention the workspace, oldest first."""
    dirs = [Path(extra)] if extra else BRAINS
    files = set()
    for d in dirs:
        if d.is_dir():
            files.update(d.glob("*/.system_generated/logs/transcript.jsonl"))
            if extra:
                files.update(d.glob("**/*.jsonl"))
    key = norm(str(ws))
    found = []
    for f in files:
        try:
            if f.stat().st_mtime >= since and key in norm(f.read_text(encoding="utf-8", errors="replace")):
                found.append(f)
        except OSError:
            continue
    return sorted(found, key=lambda f: f.stat().st_mtime)


def tool_calls(obj, out):
    """Collects (tool name, arguments) from any JSON structure that looks like a tool call."""
    if isinstance(obj, dict):
        name = next((obj[k] for k in ("name", "toolName", "tool_name", "tool") if isinstance(obj.get(k), str)), None)
        key = next((k for k in ARG_KEYS if k in obj), None)
        if name and key and re.fullmatch(r"[A-Za-z][\w.\-/]*", name):
            args = obj[key]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    pass
            schema = isinstance(args, dict) and "properties" in args and str(args.get("type")).lower() == "object"
            if not schema and not (key == "parameters" and "description" in obj):  # skip tool declarations
                out.append((name, args))
        for v in obj.values():
            tool_calls(v, out)
    elif isinstance(obj, list):
        for v in obj:
            tool_calls(v, out)


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def paths(args, key):
    """The file paths among a tool call's arguments, relative to the workspace when they are inside it."""
    out = []
    for s in strings(args):
        t = norm(s.strip())
        if "\n" in s or not (t.startswith(("/", "file:", "./", "questions/", "answers/")) or re.match(r"[a-z]:/", t)
                             or key in t):
            continue
        out.append(t.split(key, 1)[1] if key in t else t.removeprefix("./"))
    return out


def analyse(path, ws):
    """What one transcript shows: the question files read, the answer files written, calls of tools that are not
    allowed, file tools on other files, other calls, and the model names it mentions."""
    calls, seen = [], set()
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        found = []
        tool_calls(obj, found)
        for name, args in found:
            sig = (name, json.dumps(args, sort_keys=True, ensure_ascii=False, default=str))
            if sig not in seen:
                seen.add(sig)
                calls.append((name, args))
    key = norm(str(ws)).rstrip("/") + "/"
    res = {"transcript": path, "calls": len(calls), "read": set(), "wrote": set(), "forbidden": [], "files": [],
           "other": []}
    for name, args in calls:
        short = name.split("/")[-1].split(".")[-1]
        rel = paths(args, key)
        shown = ", ".join(rel) if rel else json.dumps(args, ensure_ascii=False, default=str)
        label = f"{short}({shown[:120]})"
        q = {int(m.group(1)) for r in rel if (m := re.fullmatch(r"questions/batch_(\d+)\.txt", r))}
        a = {int(m.group(1)) for r in rel if (m := re.fullmatch(r"answers/batch_(\d+)\.txt", r))}
        if FORBIDDEN.search(short):
            res["forbidden"].append(label)
        elif short in READ_TOOLS and rel and len(q) == len(rel):
            res["read"] |= q
        elif short in WRITE_TOOLS and rel and len(a) == len(rel):
            res["wrote"] |= a
        elif short in READ_TOOLS | WRITE_TOOLS:
            res["files"].append(label)
        else:
            res["other"].append(label)
    res["read"], res["wrote"] = sorted(res["read"]), sorted(res["wrote"])
    res["models"] = sorted({m.group(0).lower() for m in MODEL_NAME.finditer(text)})
    return res


def verdict(res, n=None):
    """OK; BAD (a tool that is not allowed, or another file read or written); CHECK (something this script does not
    know, worth a look); UNKNOWN (no tool call could be read from the transcript)."""
    if not res["calls"]:
        return "UNKNOWN"
    want = {n} if n is not None else set(res["read"][:1] or res["wrote"][:1])
    if res["forbidden"] or res["files"] or not set(res["read"]) <= want or not set(res["wrote"]) <= want:
        return "BAD"
    if res["other"] or set(res["read"]) != want or set(res["wrote"]) != want:
        return "CHECK"
    return "OK"


def summary(res):
    s = (f"read {', '.join(f'questions/batch_{x:02d}.txt' for x in res['read']) or 'no question file'}; "
         f"wrote {', '.join(f'answers/batch_{x:02d}.txt' for x in res['wrote']) or 'no answer file'}")
    for kind in ("forbidden", "files", "other"):
        if res[kind]:
            s += f"; {kind.replace('files', 'other files')}: {'; '.join(res[kind][:4])}" + \
                 (" ..." if len(res[kind]) > 4 else "")
    return s


def keep_transcript(folder, res, label):
    dest = folder / "transcripts"
    dest.mkdir(exist_ok=True)
    target = dest / f"{label}_{res['transcript'].parent.parent.parent.name}.jsonl"
    shutil.copy2(res["transcript"], target)
    return target


def snapshot(ws):
    """Every file in the workspace with its size and time, to see afterwards what the agent wrote."""
    return {f: (f.stat().st_size, f.stat().st_mtime_ns) for f in ws.rglob("*") if f.is_file()}


def changed(ws, before):
    return [f for f in ws.rglob("*") if f.is_file() and before.get(f) != (f.stat().st_size, f.stat().st_mtime_ns)]


def check(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    plan = fc.load_plan()
    st = status(Path(kit_["workspace"]), plan)
    for p in "AB":
        part = [s for s in st if s[2] == p]
        print(f"pass {p}: {sum(1 for s in part if s[5])} of {len(part)} answer files done")
    bad = [s for s in st if not s[5] and s[6] != "missing"]
    for k, n, p, a, b, _, why in bad:
        print(f"  answers/batch_{n:02d}.txt ({mf.describe(p, a, b)}): {why}")
    nxt = next((s for s in st if not s[5]), None)
    print("All answer files are there. Next: collect." if not nxt else
          f"Next: conversation {nxt[0]}, prompts/{nxt[0]:02d}_batch_{nxt[1]:02d}.txt ({mf.describe(*nxt[2:5])}).")


def audit(folder, transcripts=None):
    folder, kit_ = mf.load_settings(folder, KIND)
    ws = Path(kit_["workspace"])
    found = find_transcripts(ws, extra=transcripts)
    if not found:
        sys.exit("No transcript mentions this kit's workspace. Antigravity keeps them in ~/.gemini/antigravity/brain/ "
                 "(the IDE in ~/.gemini/antigravity-ide/brain/); give another folder with --transcripts.")
    rows = []
    for f in found:
        res = analyse(f, ws)
        v = verdict(res)
        kept = keep_transcript(folder, res, "audit")
        print(f"{v:7} {f.parent.parent.parent.name[:12]}: {summary(res)}" + (f" [models named: {', '.join(res['models'])}]"
                                                                              if res["models"] else ""))
        rows.append({"conversation": f.parent.parent.parent.name, "verdict": v, "read": res["read"],
                     "wrote": res["wrote"], "not_allowed": " | ".join(res["forbidden"]),
                     "other_files": " | ".join(res["files"]), "other": " | ".join(res["other"]),
                     "models": ", ".join(res["models"]), "copy": kept.name})
    with open(folder / "audit.csv", "w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    if any(r["verdict"] in ("UNKNOWN", "CHECK") for r in rows):
        print("UNKNOWN or CHECK: the transcript holds something this script cannot judge (perhaps a format it does "
              f"not know). The copies are in {folder / 'transcripts'}; send one such file so it can be looked at.")
    print(f"Wrote {folder / 'audit.csv'}; copies of the transcripts are in {folder / 'transcripts'}.")


def go(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    ws, model, level = Path(kit_["workspace"]), kit_["model"], kit_["level"]
    plan = fc.load_plan()
    print(f"Kit for {model}, thinking level {level}. Open only this folder in Antigravity:\n  {ws}")
    if not any(s[5] for s in status(ws, plan)) and not mf.ask(
            "Have you made the settings and the test conversation of HOW_TO.md (steps 2 to 4)?", default="n"):
        sys.exit(f"Do those first: {folder / 'HOW_TO.md'}")
    clip = mf.Clipboard()
    while True:
        st = status(ws, plan)
        todo = next((s for s in st if not s[5]), None)
        if not todo:
            print(f"All answer files are there. Next: python scripts/antigravity_fc.py collect \"{folder}\"")
            return
        k, n, p, a, b, _, why = todo
        answer = ws / "answers" / f"batch_{n:02d}.txt"
        if answer.exists():  # an invalid file from an earlier attempt: out of the agent's way
            print(f"  answers/batch_{n:02d}.txt was not usable ({why}); moved to {mf.set_aside(answer, folder)}")
        done = sum(1 for s in st if s[5])
        head = f"\n[{k}/{len(st)}] batch_{n:02d} ({mf.describe(p, a, b)}); {done} done"
        if clip.ok:
            clip.put(prompt(n))
            print(f"{head}. The prompt is on the clipboard.")
        else:
            print(f"{head}. Open prompts/{k:02d}_batch_{n:02d}.txt and copy all of it.")
        print(f"  In Antigravity: a NEW conversation; model {model}, thinking level {level} (check both); paste; send.\n"
              f"  Approve only writing answers/batch_{n:02d}.txt; deny anything else.")
        started, before = time.time() - 5, snapshot(ws)
        if input("  When the agent has finished, press Enter (q to stop): ").strip().lower() == "q":
            return
        stray = [f for f in changed(ws, before) if f != answer]  # any other file the agent wrote or changed
        for f in stray:
            print(f"  The agent also wrote {f.relative_to(ws).as_posix()}: moved to {mf.set_aside(f, folder)}.")
        ans, why = read_answer(answer)
        if not ans:
            print(f"  answers/batch_{n:02d}.txt: {why}. Start a new conversation for this file.")
            mf.log(folder, n=k, request=f"batch_{n:02d}", result=f"not usable: {why}",
                   tools="; ".join(f"also wrote {f.relative_to(ws).as_posix()}" for f in stray))
            continue
        found = find_transcripts(ws, since=started)
        res = analyse(found[-1], ws) if found else None
        v = verdict(res, n) if res else "UNKNOWN"
        if stray:
            v = "BAD"
            if res:
                res["files"] += [f"wrote {f.relative_to(ws).as_posix()}" for f in stray]
        if res:
            keep_transcript(folder, res, f"{k:02d}_batch_{n:02d}")
            print(f"  Transcript: {v}: {summary(res)}")
        else:
            print("  No transcript of this conversation was found; it can be checked later with audit."
                  + (" The agent wrote other files, so this answer is not used." if stray else ""))
        confirmed = mf.ask(f"  Did the picker show {model}, {level}, and did the agent ask for nothing but writing "
                           f"answers/batch_{n:02d}.txt? (If it tried a command, a search or anything else, even one you "
                           "denied, answer n.)")
        note = "" if confirmed and v != "BAD" else input("  Anything to note? (one line) ").strip()
        tools = f"{v}: {summary(res)}" if res else f"{v}: no transcript found" + "".join(
            f"; also wrote {f.relative_to(ws).as_posix()}" for f in stray)
        if v == "BAD" or not confirmed:
            moved = mf.set_aside(answer, folder)
            print(f"  Not used: moved to {moved}. This file is asked again in a new conversation.")
            mf.log(folder, n=k, request=f"batch_{n:02d}", result="set aside", answers=fc.N, confirmed=confirmed,
                   tools=tools, note=note)
            continue
        if v != "OK":
            print(f"  Kept, but the transcript could not be checked fully ({v}). Its copy is in {folder / 'transcripts'}:"
                  " send it, so that the check can be adapted.")
        mf.log(folder, n=k, request=f"batch_{n:02d}", result="kept", answers=fc.N, confirmed=confirmed, tools=tools,
               note=note)


def collect(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    ws, alias = Path(kit_["workspace"]), kit_["alias"]
    plan = fc.load_plan()
    answers, sources = {}, {}
    keep = OUT / f"{alias}_answers"
    for k, n, p, a, b, ans, why in status(ws, plan):
        if ans:
            answers[(p, a, b)], sources[(p, a, b)] = ans, f"batch_{n:02d}.txt"
            keep.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ws / "answers" / f"batch_{n:02d}.txt", keep / f"batch_{n:02d}.txt")
    mf.write_results(OUT, alias, kit_["model"], kit_["level"], "antigravity", answers, sources)
    for name in ("log.csv", "audit.csv"):
        if (folder / name).exists():
            shutil.copy2(folder / name, OUT / f"{alias}_{name}")
    settings = {k: v for k, v in kit_.items() if k != "workspace"}
    (OUT / f"{alias}_kit.json").write_text(json.dumps(settings, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit")
    k.add_argument("folder")
    k.add_argument("--model", required=True, help='the model as Antigravity names it, e.g. "Gemini 4 Hydrogen"')
    k.add_argument("--level", required=True, help="the thinking level you will choose, e.g. Low")
    for name in ("go", "check", "audit", "collect"):
        s = sub.add_parser(name)
        s.add_argument("folder")
        if name == "audit":
            s.add_argument("--transcripts", help="a folder with the transcripts, if not in ~/.gemini/antigravity*/brain")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "kit":
        kit(args.folder, args.model, args.level)
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
