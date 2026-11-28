"""Forced choice with Gemini models in the Gemini app (gemini.google.com), by hand: one temporary chat per request.
results/chat/gemini_app/README.md is the step-by-step guide; `kit` puts a copy of it in the kit folder as HOW_TO.md,
with this kit's commands at the top.

`kit` writes a folder outside this repository:

    <kit>/paste/01_latn_A_01.txt ... 96_latn_reformed_B_16.txt   the text of each chat, in the order to run them
    <kit>/answers/                                               the checked answers, under the same names
    <kit>/HOW_TO.md, kit.json, log.csv, rejected/

Each paste file is exactly the request of the Gemini CLI runs (gemini_cli_fc.prompt_for): the request of the Claude
runs, with one line asking for the answers as JSON. The order is pass A in all three alphabets first, batch by batch,
then pass B. `go` puts each request on the clipboard, reads Gemini's answer from the clipboard once you have copied
it, checks it, asks you to confirm, and only then saves it. Its first request is the longest one (current Latin,
batch 4), to check that a whole request fits into the message box; the same batch in the other two alphabets comes
next, so that a run stopped early still has the same pairs in every alphabet.

    python scripts/gemini_app_fc.py kit ../uzblimp-gemini-app-neon --model "Gemini 4 Neon" --picker "Deeper analysis" --level Low
    python scripts/gemini_app_fc.py go ../uzblimp-gemini-app-neon        # one chat after another
    python scripts/gemini_app_fc.py check ../uzblimp-gemini-app-neon     # what is done, and what comes next
    python scripts/gemini_app_fc.py collect ../uzblimp-gemini-app-neon   # per-pair files in results/chat/gemini_app/
"""
import argparse
import json
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
    """(chat number, file name, pass, alphabet, batch index), in the order of the plan."""
    return [(k, f"{k:02d}_{a}_{p}_{b + 1:02d}", p, a, b) for k, (p, a, b) in enumerate(mf.run_order(plan), 1)]


def header(folder, settings):
    """This kit's commands, put at the top of its HOW_TO.md."""
    f = f'"{folder}"'
    return (f"# This kit: {settings['model']} ('{settings['picker']}' in the model picker), thinking level "
            f"{settings['level']}\n\nKit folder: `{folder}`. Run these commands in a terminal in the uzblimp folder "
            f"(`cd \"{fc.ROOT}\"`; use `py` if `python` is not found):\n\n```\npython scripts/gemini_app_fc.py go {f}\n"
            f"python scripts/gemini_app_fc.py check {f}\npython scripts/gemini_app_fc.py collect {f}\n```\n\nThe guide "
            f"below uses the folder and model of its examples; use the ones above.\n\n")


def kit(folder, model, picker, level, alias):
    folder = mf.outside_repo(folder)
    plan = fc.load_plan()
    (folder / "paste").mkdir(parents=True, exist_ok=True)
    (folder / "answers").mkdir(exist_ok=True)
    longest, size = None, -1
    for k, name, p, a, b in requests(plan):
        text = gcli.prompt_for(plan, a, p, b)
        (folder / "paste" / f"{name}.txt").write_text(text, encoding="utf-8")
        if len(text) > size:
            longest, size = name, len(text)
    mf.save_settings(folder, kind=KIND, model=model, picker=picker or model, level=level,
                     alias=alias or mf.slug(model), trial=longest)
    settings = json.loads((folder / "kit.json").read_text(encoding="utf-8"))
    guide = GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else ""
    (folder / "HOW_TO.md").write_text(header(folder, settings) + guide, encoding="utf-8")
    print(f"Wrote {folder}: {len(requests(plan))} requests in paste/ (the longest, {longest}, has {size:,} characters)."
          f"\nThen run: python scripts/gemini_app_fc.py go \"{folder}\"")


def read_answer(path):
    """(answers as a string of N digits, None) for a usable reply, else (None, what is wrong)."""
    if not path.exists():
        return None, "missing"
    ans = gcli.parse(mf.read_text(path))
    return (ans, None) if ans else (None, f"no complete list of {fc.N} answers")


def status(folder, plan):
    """Per request: (k, name, pass, alphabet, batch, answers or None, why). A reply counts only when go kept it: it
    is in answers/ and the log's last line about it says kept, with the same checksum."""
    ok = mf.kept(folder)
    out = []
    for k, name, p, a, b in requests(plan):
        f = folder / "answers" / f"{name}.txt"
        ans, why = read_answer(f)
        if ans and ok.get(name) != mf.sha256(mf.read_text(f)):
            ans, why = None, "not kept by go (no matching line in log.csv)"
        out.append((k, name, p, a, b, ans, why))
    return out


def next_request(st, trial):
    """The trial first; then the same batch in the other alphabets; then the first missing request in order."""
    todo = [s for s in st if not s[5]]
    if not todo:
        return None
    t = next(s for s in st if s[1] == trial)
    if not t[5]:
        return t
    same = [s for s in todo if s[2] == t[2] and s[4] == t[4]]
    return same[0] if same else todo[0]


def check(folder):
    folder, settings = mf.load_settings(folder, KIND)
    st = status(folder, fc.load_plan())
    for p in "AB":
        part = [s for s in st if s[2] == p]
        print(f"pass {p}: {sum(1 for s in part if s[5])} of {len(part)} replies done")
    for k, name, p, a, b, _, why in st:
        if why and why != "missing":
            print(f"  answers/{name}.txt ({mf.describe(p, a, b)}): {why}")
    nxt = next_request(st, settings["trial"])
    print("All replies are there. Next: collect." if not nxt else
          f"Next: chat {nxt[0]}, paste/{nxt[1]}.txt ({mf.describe(*nxt[2:5])}).")


def is_request(text):
    return END in text and "\nItem 1\n" in text


def go(folder):
    folder, settings = mf.load_settings(folder, KIND)
    model, picker, level = settings["model"], settings["picker"], settings["level"]
    plan = fc.load_plan()
    if not any(s[5] for s in status(folder, plan)) and not mf.ask(
            "Have you made the settings of HOW_TO.md (step 2)?", default="n"):
        sys.exit(f"Do those first: {folder / 'HOW_TO.md'}")
    clip = mf.Clipboard()
    by_hand = folder / "reply.txt"
    if not clip.ok:
        print("No access to the clipboard here: copy each request by hand, and save each answer as "
              f"{by_hand} (UTF-8), as HOW_TO.md says.")
    while True:
        st = status(folder, plan)
        cur = next_request(st, settings["trial"])
        if not cur:
            print(f"All replies are there. Next: python scripts/gemini_app_fc.py collect \"{folder}\"")
            return
        k, name, p, a, b, _, why = cur
        request = (folder / "paste" / f"{name}.txt").read_text(encoding="utf-8")
        if request != gcli.prompt_for(plan, a, p, b):
            sys.exit(f"paste/{name}.txt differs from the benchmark (was it changed, or the benchmark since the kit was "
                     "made?). Make a new kit.")
        answer = folder / "answers" / f"{name}.txt"
        if answer.exists():  # a reply that go did not keep
            print(f"  answers/{name}.txt was not usable ({why}): moved to {mf.set_aside(answer, folder)}")
        trial = not any(s[5] for s in st)
        head = f"\n[chat {k} of {len(st)}] {name} ({mf.describe(p, a, b)}); {sum(1 for s in st if s[5])} done"
        if clip.ok:
            clip.put(request)
            print(f"{head}. The request is on the clipboard.")
        else:
            by_hand.unlink(missing_ok=True)
            print(f"{head}. Open {folder / 'paste' / f'{name}.txt'} and copy all of it.")
        print(f"  In Gemini: a new Temporary chat; in the model picker {picker} ({model}) and thinking level {level} "
              "(set both); paste; send.")
        if trial:
            print(f"  This first chat is the trial, with the longest request. After sending, scroll to the end of "
                  f"your message: it must end with the line \"{END}, ...\".")
        try:
            reply = None
            while reply is None:
                where = "click its copy button, then press Enter here" if clip.ok else f"save it as {by_hand.name}, " \
                                                                                       "then press Enter"
                cmd = input(f"  When the answer is complete, {where} (r = the answer is broken, ask again; q = stop): "
                            ).strip().lower()
                if cmd == "q":
                    return
                if cmd == "r":
                    mf.log(folder, settings, n=k, request=name, result="asked again",
                           note=input("  What was wrong? ").strip())
                    break
                text = clip.get() if clip.ok else (mf.read_text(by_hand) if by_hand.exists() else "")
                if is_request(text):
                    print("  The clipboard still holds the request: copy Gemini's answer with its copy button first.")
                elif not gcli.parse(text):
                    print(f"  That is not a complete list of {fc.N} answers ({len(text)} characters). Copy the whole "
                          "answer again, or type r if the answer itself is broken.")
                else:
                    reply = text
            if reply is None:
                continue
            yes, note = mf.confirm(f"  Was everything right: below the answer no Sources button and no 'Limit "
                                   f"reached', and the picker still on {picker}, {level}? Type y or n, a note may "
                                   "follow (for example: y normal chat):")
        except KeyboardInterrupt:
            print("\n  Stopped; this answer is not saved. Run go again to continue.")
            return
        if yes:
            answer.write_text(reply, encoding="utf-8")
            mf.log(folder, settings, n=k, request=name, result="kept", sha256=mf.sha256(mf.read_text(answer)),
                   note=note)
            print(f"  Saved answers/{name}.txt.")
        else:
            rejected = folder / "rejected"
            rejected.mkdir(exist_ok=True)
            target = rejected / f"{name}_{mf.now().replace(':', '')}.txt"
            target.write_text(reply, encoding="utf-8")
            mf.log(folder, settings, n=k, request=name, result="set aside", note=note)
            print(f"  Not used: saved as rejected/{target.name}. This request is asked again, in a new temporary chat. "
                  "If the limit was reached, type q at the next step and come back when it has refreshed "
                  "(gemini.google.com/usage).")
        by_hand.unlink(missing_ok=True)


def collect(folder):
    folder, settings = mf.load_settings(folder, KIND)
    alias = settings["alias"]
    plan = fc.load_plan()
    mf.claim_alias(OUT, alias, settings)
    answers, sources, files = {}, {}, []
    for k, name, p, a, b, ans, why in status(folder, plan):
        if ans:
            if (folder / "paste" / f"{name}.txt").read_text(encoding="utf-8") != gcli.prompt_for(plan, a, p, b):
                sys.exit(f"paste/{name}.txt differs from the benchmark: the benchmark or the kit changed since the kit "
                         f"was made (commit {settings.get('commit')}).")
            answers[(p, a, b)], sources[(p, a, b)] = ans, f"{name}.txt"
            files.append((folder / "answers" / f"{name}.txt", f"{name}.txt"))
        elif why and why != "missing":
            print(f"answers/{name}.txt not used: {why}")
    mf.write_results(OUT, alias, settings["model"], settings["level"], "gemini-app", answers, sources)
    mf.keep_answers(OUT / f"{alias}_answers", files)
    if (folder / "log.csv").exists():
        mf.publish(folder / "log.csv", OUT / f"{alias}_log.csv", folder)
    (OUT / f"{alias}_kit.json").write_text(json.dumps(settings, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit")
    k.add_argument("folder")
    k.add_argument("--model", required=True, help='the model, e.g. "Gemini 4 Neon"')
    k.add_argument("--picker", help='how the model picker names it, e.g. "Deeper analysis" (default: --model)')
    k.add_argument("--level", required=True, help="the thinking level you will choose, e.g. Low")
    k.add_argument("--alias", help="the name of the result files (default: from --model)")
    for name in ("go", "check", "collect"):
        sub.add_parser(name).add_argument("folder")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "kit":
        kit(args.folder, args.model, args.picker, args.level, args.alias)
    elif args.cmd == "go":
        go(args.folder)
    elif args.cmd == "check":
        check(args.folder)
    else:
        collect(args.folder)


if __name__ == "__main__":
    main()
