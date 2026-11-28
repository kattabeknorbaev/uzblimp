"""Forced choice with Gemini models in the Gemini app (gemini.google.com), by hand: one temporary chat per request.
results/chat/gemini_app/README.md is the step-by-step guide; `kit` puts a copy of it in the kit folder as HOW_TO.md.

`kit` writes a folder outside this repository:

    <kit>/paste/01_latn_A_01.txt ... 96_latn_reformed_B_16.txt   the text of each chat, in the order to run them
    <kit>/answers/                                               each reply, saved under the same name
    <kit>/HOW_TO.md, kit.json, log.csv

Each paste file is exactly the request of the Gemini CLI runs (gemini_cli_fc.prompt_for): the request of the Claude
runs, with one line asking for the answers as JSON. The order is pass A in all three alphabets first, batch by batch,
then pass B. `go` puts each request on the clipboard, reads Gemini's reply from the clipboard once you have copied
it, checks it and saves it. Its first request is the longest one, to check that a whole request fits into the
message box.

    python scripts/gemini_app_fc.py kit ../uzblimp-gemini-app-neon --model "Gemini 4 Neon" --level Low
    python scripts/gemini_app_fc.py go ../uzblimp-gemini-app-neon        # one chat after another
    python scripts/gemini_app_fc.py check ../uzblimp-gemini-app-neon     # what is done, and what comes next
    python scripts/gemini_app_fc.py collect ../uzblimp-gemini-app-neon   # per-pair files in results/chat/gemini_app/
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude_fc as fc  # noqa: E402
import gemini_cli_fc as gcli  # noqa: E402
import manual_fc as mf  # noqa: E402

KIND = "gemini-app"
OUT = fc.ROOT / "results" / "chat" / "gemini_app"
GUIDE = OUT / "README.md"
END = "Reply with JSON only"  # the start of the request's last line (gemini_cli_fc.FORMAT_LINE)
assert END in gcli.FORMAT_LINE


def requests(plan):
    """(chat number, file name, pass, alphabet, batch index), in the order to run them."""
    return [(k, f"{k:02d}_{a}_{p}_{b + 1:02d}", p, a, b) for k, (p, a, b) in enumerate(mf.run_order(plan), 1)]


def kit(folder, model, level):
    folder = mf.outside_repo(folder)
    if (folder / "answers").exists() and any((folder / "answers").iterdir()):
        sys.exit(f"{folder} already holds answers. Use a new folder for a new kit.")
    plan = fc.load_plan()
    (folder / "paste").mkdir(parents=True, exist_ok=True)
    (folder / "answers").mkdir(exist_ok=True)
    longest, size = None, -1
    for k, name, p, a, b in requests(plan):
        text = gcli.prompt_for(plan, a, p, b)
        (folder / "paste" / f"{name}.txt").write_text(text, encoding="utf-8")
        if len(text) > size:
            longest, size = name, len(text)
    if GUIDE.exists():
        shutil.copy2(GUIDE, folder / "HOW_TO.md")
    mf.save_settings(folder, kind=KIND, model=model, level=level, alias=mf.slug(model), trial=longest)
    print(f"Wrote {folder}: {len(requests(plan))} requests in paste/ (the longest, {longest}, has {size:,} characters)."
          f"\nThen run: python scripts/gemini_app_fc.py go \"{folder}\"")


def read_answer(path):
    """(answers as a string of N digits, None) for a usable reply, else (None, what is wrong)."""
    if not path.exists():
        return None, "missing"
    ans = gcli.parse(path.read_text(encoding="utf-8", errors="replace"))
    return (ans, None) if ans else (None, f"no complete list of {fc.N} answers")


def status(folder, plan):
    return [(k, name, p, a, b, *read_answer(folder / "answers" / f"{name}.txt")) for k, name, p, a, b in requests(plan)]


def check(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    st = status(folder, fc.load_plan())
    for p in "AB":
        part = [s for s in st if s[2] == p]
        print(f"pass {p}: {sum(1 for s in part if s[5])} of {len(part)} replies done")
    for k, name, p, a, b, _, why in st:
        if why and why != "missing":
            print(f"  answers/{name}.txt ({mf.describe(p, a, b)}): {why}")
    nxt = next((s for s in st if not s[5]), None)
    print("All replies are there. Next: collect." if not nxt else
          f"Next: chat {nxt[0]}, paste/{nxt[1]}.txt ({mf.describe(*nxt[2:5])}).")


def is_request(text):
    return END in text and "\nItem 1\n" in text


def go(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    model, level = kit_["model"], kit_["level"]
    plan = fc.load_plan()
    if not any(s[5] for s in status(folder, plan)) and not mf.ask(
            "Have you made the settings of HOW_TO.md (step 2)?", default="n"):
        sys.exit(f"Do those first: {folder / 'HOW_TO.md'}")
    clip = mf.Clipboard()
    if not clip.ok:
        print("No access to the clipboard here: copy each request and save each reply by hand, as HOW_TO.md says.")
    while True:
        st = status(folder, plan)
        todo = [s for s in st if not s[5]]
        if not todo:
            print(f"All replies are there. Next: python scripts/gemini_app_fc.py collect \"{folder}\"")
            return
        trial = not any(s[5] for s in st)
        cur = next((s for s in todo if trial and s[1] == kit_["trial"]), todo[0])
        k, name, p, a, b, _, why = cur
        request = (folder / "paste" / f"{name}.txt").read_text(encoding="utf-8")
        answer = folder / "answers" / f"{name}.txt"
        if answer.exists():  # an unusable reply from an earlier attempt
            print(f"  answers/{name}.txt was not usable ({why}); moved to {mf.set_aside(answer, folder)}")
        head = f"\n[chat {k} of {len(st)}] {name} ({mf.describe(p, a, b)}); {len(st) - len(todo)} done"
        if clip.ok:
            clip.put(request)
            print(f"{head}. The request is on the clipboard.")
        else:
            print(f"{head}. Open paste/{name}.txt and copy all of it.")
        print(f"  In Gemini: a new Temporary chat; model {model}, thinking level {level} (set both); paste; send.")
        if trial:
            print(f"  This first chat is the trial, with the longest request. After sending, scroll to the end of "
                  f"your message: it must end with the line \"{END}, ...\".")
        reply = None
        while reply is None:
            if clip.ok:
                cmd = input("  When the answer is complete, click its copy button, then press Enter here (r = this "
                            "reply is broken, ask again; q = stop): ").strip().lower()
            else:
                cmd = input(f"  Save the answer as answers/{name}.txt, then press Enter (r = broken, ask again; "
                            "q = stop): ").strip().lower()
            if cmd == "q":
                return
            text = clip.get() if clip.ok else (answer.read_text(encoding="utf-8") if answer.exists() else "")
            if cmd == "r":
                mf.log(folder, n=k, request=name, result="asked again", note=input("  What was wrong? ").strip())
                break
            if is_request(text):
                print("  The clipboard still holds the request: copy Gemini's answer with its copy button first.")
            elif not gcli.parse(text):
                print(f"  That is not a complete list of {fc.N} answers ({len(text)} characters). Copy the whole "
                      "answer again, or type r if the answer itself is broken.")
            else:
                reply = text
        if reply is None:
            continue
        answer.write_text(reply, encoding="utf-8")
        confirmed = mf.ask(f"  Below the answer: no Sources button and no 'Limit reached', and the picker still "
                           f"shows {model}, {level}?")
        if not confirmed:
            note = input("  What was different? (one line) ").strip()
            moved = mf.set_aside(answer, folder)
            print(f"  Not used: moved to {moved}. This request is asked again in a new temporary chat. If the limit "
                  "was reached, type q next and come back when it has reset (gemini.google.com/usage).")
            mf.log(folder, n=k, request=name, result="set aside", answers=fc.N, confirmed=False, note=note)
            continue
        mf.log(folder, n=k, request=name, result="kept", answers=fc.N, confirmed=True)
        print(f"  Saved answers/{name}.txt.")


def collect(folder):
    folder, kit_ = mf.load_settings(folder, KIND)
    alias = kit_["alias"]
    answers, sources = {}, {}
    keep = OUT / f"{alias}_answers"
    for k, name, p, a, b, ans, why in status(folder, fc.load_plan()):
        if ans:
            answers[(p, a, b)], sources[(p, a, b)] = ans, f"{name}.txt"
            keep.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / "answers" / f"{name}.txt", keep / f"{name}.txt")
    mf.write_results(OUT, alias, kit_["model"], kit_["level"], "gemini-app", answers, sources)
    if (folder / "log.csv").exists():
        shutil.copy2(folder / "log.csv", OUT / f"{alias}_log.csv")
    (OUT / f"{alias}_kit.json").write_text(json.dumps(kit_, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit")
    k.add_argument("folder")
    k.add_argument("--model", required=True, help='the model as the Gemini app names it, e.g. "Gemini 4 Neon"')
    k.add_argument("--level", required=True, help="the thinking level you will choose, e.g. Low")
    for name in ("go", "check", "collect"):
        sub.add_parser(name).add_argument("folder")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    {"kit": lambda: kit(args.folder, args.model, args.level), "go": lambda: go(args.folder),
     "check": lambda: check(args.folder), "collect": lambda: collect(args.folder)}[args.cmd]()


if __name__ == "__main__":
    main()
