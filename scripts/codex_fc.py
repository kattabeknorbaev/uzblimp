"""Forced choice through OpenAI Codex (a ChatGPT subscription), with the requests of the Claude runs.

The kit holds 96 question files: the 16 batches of 150 pairs of results/claude_fc/plan_v1.2.json in each
alphabet (current Latin, Cyrillic, reformed Latin) and pass (A: the order of the plan, B: every pair reversed),
each with the question of scripts/claude_fc.py less its sentence about tools (Codex needs them to read the
question files and write its answers; the pasted prompt restricts them instead, see PROMPT). No file of the kit
names a pair, a phenomenon or the correct member. Codex is opened in the kit's folder only, the prompt is pasted,
and it writes answers/batch_XX.txt with one line "<item>: <1 or 2>" per item. `collect` turns the answer files
into per-pair files in the format of the Claude runs (results/codex_fc/<alias>_<alphabet>.csv) and keeps the
answer files (results/codex_fc/<alias>_answers/).

    python scripts/codex_fc.py kit <folder>                       # write the kit to hand to Codex
    python scripts/codex_fc.py collect <answers folder> --alias gpt --model "GPT 6.2 Sol" --effort light
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from claude_fc import HEADER, N, ROOT, bench, items, load_plan  # noqa: E402

OUT = ROOT / "results" / "codex_fc"
ALPHABETS = ["latn", "cyrl", "latn_reformed"]
BLOCKS = [(a, p) for a in ALPHABETS for p in ("A", "B")]  # batch 1-16 latn A, 17-32 latn B, 33-48 cyrl A, ...
TOOLS = (" Apart from returning your answers, do not use any tools: do not read or search files, run code or search "
         "the web.")
FILE_HEADER = HEADER.replace(TOOLS, "")
assert FILE_HEADER != HEADER

PROMPT = """You judge the grammaticality of Uzbek sentences.

The folder questions/ has 96 files, batch_01.txt through batch_96.txt. Each file has 150 numbered items. Each item has two Uzbek sentences, labelled 1 and 2. For each item: which of the two sentences is grammatically correct? Exactly one of them is.

Answer from your own knowledge of Uzbek and judge each item on its own. Read only the question files in questions/. Do not run code or scripts to decide your answers. Do not search the web. Do not look anything up. Do not read any other files.

For every questions/batch_XX.txt that does not yet have a matching answers/batch_XX.txt, write answers/batch_XX.txt with an answer for every item from 1 to 150, even when you are unsure. Write only lines in this format, and nothing else:

1: 1
2: 2
3: 1

Each line is the item number, a colon, a space, and then 1 or 2 (the number of the grammatically correct sentence). No explanations.

Work through the files in order, starting from the first missing answers/batch_XX.txt. When you finish a file, go on to the next. Do not stop after one batch if you can continue."""


def batch_number(block, b):
    return block * 16 + b + 1


def question_file(plan, alphabet, pass_, b):
    parts = [FILE_HEADER]
    for i, (s1, s2) in enumerate(items(plan, alphabet, b), 1):
        if pass_ == "B":
            s1, s2 = s2, s1
        parts.append(f"Item {i}\n1. {s1}\n2. {s2}")
    return "\n\n".join(parts) + "\n"


def kit(folder):
    folder = Path(folder)
    plan = load_plan()
    (folder / "questions").mkdir(parents=True, exist_ok=True)
    (folder / "answers").mkdir(exist_ok=True)
    (folder / "answers" / ".keep").write_text("", encoding="utf-8")
    for block, (alphabet, pass_) in enumerate(BLOCKS):
        for b in range(len(plan["batches"])):
            text = question_file(plan, alphabet, pass_, b)
            (folder / "questions" / f"batch_{batch_number(block, b):02d}.txt").write_text(text, encoding="utf-8")
    (folder / "INSTRUCTIONS.md").write_text(
        "Open Codex in this folder only, choose the model and reasoning level once, paste the prompt below, and "
        "paste it again whenever Codex stops, until answers/ holds batch_01.txt to batch_96.txt.\n\n```\n"
        + PROMPT + "\n```\n", encoding="utf-8")
    print(f"wrote {folder} (96 question files)")


LINE = re.compile(r"^\s*(\d+)\s*:\s*([12])\s*$")


def read_answers(path):
    """{item: answer} of one answer file; every line must be "<item>: <1 or 2>" and items 1..N appear once."""
    got = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = LINE.match(line)
        if not m:
            sys.exit(f"{path.name}: not an answer line: {line[:40]!r}")
        i = int(m.group(1))
        if i in got:
            sys.exit(f"{path.name}: item {i} answered twice")
        got[i] = int(m.group(2))
    if set(got) != set(range(1, N + 1)):
        sys.exit(f"{path.name}: items missing or out of range")
    return got


def collect(answers, alias, model, effort):
    answers = Path(answers)
    plan = load_plan()
    files = {batch_number(k, b): answers / f"batch_{batch_number(k, b):02d}.txt"
             for k in range(len(BLOCKS)) for b in range(len(plan["batches"]))}
    missing = [f.name for f in files.values() if not f.exists()]
    if missing:
        sys.exit(f"missing answer files: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
    got = {n: read_answers(f) for n, f in files.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    for alphabet in ALPHABETS:
        d = bench(alphabet).set_index("id")
        rows = []
        for b, batch in enumerate(plan["batches"]):
            for i, it in enumerate(batch):
                row = {"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"], "good": d.at[it["id"], "grammatical"],
                       "bad": d.at[it["id"], "ungrammatical"], "batch": b + 1, "item": i + 1}
                for pass_ in ("A", "B"):
                    n = batch_number(BLOCKS.index((alphabet, pass_)), b)
                    ans = got[n][i + 1]
                    good_first = (it["first_in_A"] == "grammatical") == (pass_ == "A")
                    order = "gb" if good_first else "bg"
                    row[f"answer_{order}"] = ans
                    row[f"correct_{order}"] = ans == (1 if good_first else 2)
                    row[f"file_{order}"] = f"batch_{n:02d}.txt"
                rows.append(row)
        df = pd.DataFrame(rows)
        df["accuracy"] = (df.correct_gb.astype(int) + df.correct_bg.astype(int)) / 2
        df["consistent"] = df.correct_gb & df.correct_bg
        df["model"], df["alphabet"], df["effort"] = model, alphabet, effort
        df = df.set_index("id").loc[bench(alphabet).id].reset_index()  # benchmark order
        df = df[["id", "phenomenon", "good", "bad", "batch", "item", "answer_gb", "correct_gb", "file_gb", "answer_bg",
                 "correct_bg", "file_bg", "accuracy", "consistent", "model", "alphabet", "effort"]]
        f = OUT / f"{alias}_{alphabet}.csv"
        df.to_csv(f, index=False, encoding="utf-8")
        print(f"{f.name}: accuracy {100 * df.accuracy.mean():.1f}, consistent {100 * df.consistent.mean():.1f}, "
              f"wrong judgments {int((~df.correct_gb).sum() + (~df.correct_bg).sum())} of {2 * len(df)}")
    keep = OUT / f"{alias}_answers"
    keep.mkdir(exist_ok=True)
    for f in files.values():
        shutil.copy2(f, keep / f.name)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit")
    k.add_argument("folder")
    c = sub.add_parser("collect")
    c.add_argument("answers")
    c.add_argument("--alias", required=True)
    c.add_argument("--model", required=True)
    c.add_argument("--effort", required=True)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "kit":
        kit(args.folder)
    else:
        collect(args.answers, args.alias, args.model, args.effort)


if __name__ == "__main__":
    main()
