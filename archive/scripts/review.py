"""Review UzBLiMP pairs one at a time in the terminal.

Keys: y accept · n reject (asks for a reason) · e edit · s skip · u undo last · q quit
Every answer is written to the file at once, so you can quit any time and resume
later; only `unchecked` pairs are shown. The changed words are highlighted
(green = grammatical, red = ungrammatical).

    python scripts/review.py data/pairs_v1_numeral_no_plural.tsv --reviewer KN
"""
import argparse
import csv
import difflib
import os
import sys
from datetime import datetime

from schema import ALL_PHENOMENA, COLUMNS, OPTIONAL_COLUMNS, TOKEN_RE
from validate_pairs import check_pair

GREEN, RED, BOLD, DIM, RESET = "\033[32;1m", "\033[31;1m", "\033[1m", "\033[2m", "\033[0m"
REASONS = {
    "1": "bad sentence is actually grammatical",
    "2": "good sentence is unnatural or wrong",
    "3": "change alters meaning, not grammar",
    "4": "name or personal data",
    "5": "dialect or colloquial form",
}
INTERACTIVE = sys.stdin.isatty()


# ------------------------------------------------------------------ file I/O
def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    for c in OPTIONAL_COLUMNS:
        if c not in header:
            header.append(c)
    return header, rows


def save(path, header, rows):
    """Write to a temp file, then replace: a crash can't leave a half-written file."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_NONE, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


# ------------------------------------------------------------------ display
def highlight(a, b):
    """Colour the tokens that differ between sentences a and b."""
    ta, tb = list(TOKEN_RE.finditer(a)), list(TOKEN_RE.finditer(b))
    sm = difflib.SequenceMatcher(a=[m.group() for m in ta], b=[m.group() for m in tb], autojunk=False)
    marks_a, marks_b = set(), set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            marks_a.update(range(i1, i2))
            marks_b.update(range(j1, j2))

    def paint(s, toks, marks, colour):
        out, pos = [], 0
        for k, m in enumerate(toks):
            out.append(s[pos:m.start()])
            out.append(f"{colour}{m.group()}{RESET}" if k in marks else m.group())
            pos = m.end()
        return "".join(out) + s[pos:]

    return paint(a, ta, marks_a, GREEN), paint(b, tb, marks_b, RED)


def show(row, done, total, counts):
    if INTERACTIVE:
        print("\033[2J\033[H", end="")
    g, u = highlight(row["grammatical"], row["ungrammatical"])
    print(f"{BOLD}[{done + 1}/{total}]{RESET}  {row['phenomenon']}  ·  {row['id']}   "
          f"{DIM}(accepted {counts['accepted']} · edited {counts['edited']} · rejected {counts['rejected']}){RESET}")
    print(f"{DIM}rule: {ALL_PHENOMENA.get(row['phenomenon'], '?')}{RESET}\n")
    print(f"  ✓ {g}")
    print(f"  ✗ {u}\n")
    print(f"{DIM}  change: {row.get('notes', '')}   source: {row.get('source_id', '')}{RESET}\n")
    print("[y] accept  [n] reject  [e] edit  [s] skip  [u] undo  [q] quit")


# ------------------------------------------------------------------ input
def getkey(allowed):
    """One keypress in a real terminal; one line (first character) when piped."""
    while True:
        if INTERACTIVE and os.name == "nt":
            import msvcrt
            k = msvcrt.getwch().lower()
        elif INTERACTIVE:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                k = sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        else:
            line = sys.stdin.readline()
            if not line:
                return "q"
            k = line.strip()[:1].lower()
        if k == "\x03":
            raise KeyboardInterrupt
        if k in allowed:
            return k


def ask_line(prompt):
    print(prompt, end="", flush=True)
    line = sys.stdin.readline()
    return line.rstrip("\n").strip() if line else ""


def ask_reason():
    print("\nReason: " + "  ".join(f"{k}={v}" for k, v in REASONS.items()))
    text = ask_line("Number or short text (Enter = cancel): ")
    return REASONS.get(text, text)


def changed_span(old, new):
    """The part of `old` that was replaced, and its replacement (common prefix/suffix stripped)."""
    i = 0
    while i < min(len(old), len(new)) and old[i] == new[i]:
        i += 1
    j = 0
    while j < min(len(old), len(new)) - i and old[-1 - j] == new[-1 - j]:
        j += 1
    # widen to whole words so the match in the other sentence is unambiguous
    while i > 0 and not old[i - 1].isspace():
        i -= 1
    while j > 0 and not old[len(old) - j].isspace():
        j -= 1
    return old[i:len(old) - j], new[i:len(new) - j]


def edit(row):
    """Returns the edited row, or None if cancelled."""
    print("\nEdit which sentence? [g] grammatical  [u] ungrammatical  [c] cancel")
    k = getkey("guc")
    if k == "c":
        return None
    field = "grammatical" if k == "g" else "ungrammatical"
    print(f"Current: {row[field]}")
    new = ask_line("New text (Enter = cancel): ")
    if not new:
        return None
    out = dict(row)
    out[field] = new
    # Fixing a word outside the tested change (a typo, a wrong verb) usually has to happen
    # in both sentences, or the pair stops differing in exactly one place.
    other = "ungrammatical" if field == "grammatical" else "grammatical"
    old_part, new_part = changed_span(row[field], new)
    if old_part and row[other].count(old_part) == 1:
        print(f"Apply the same change ({old_part!r} → {new_part!r}) to the {other} sentence? [y] yes  [n] no")
        if getkey("yn") == "y":
            out[other] = row[other].replace(old_part, new_part)
    errs, warns = check_pair(out)
    for m in errs + warns:
        print(f"  {'ERROR' if m in errs else 'warning'}: {m}")
    if errs:
        print("Keep this edit anyway? [y] yes  [n] no")
        if getkey("yn") == "n":
            return None
    note = f"edited {field}; was: {row[field]}"
    if out[other] != row[other]:
        note += f" | {other} mirrored; was: {row[other]}"
    out["notes"] = f"{row.get('notes', '')} | {note}".strip(" |")
    return out


# ------------------------------------------------------------------ main loop
def review(path, reviewer):
    header, rows = read(path)
    queue = [i for i, r in enumerate(rows) if r.get("status") == "unchecked"]
    history = []  # (row index, row before the decision)
    skipped = []
    total = len(rows)

    def counts():
        c = {"accepted": 0, "edited": 0, "rejected": 0}
        for r in rows:
            if r.get("status") in c:
                c[r["status"]] += 1
        return c

    pos = 0
    while True:
        if pos >= len(queue):
            if skipped:
                print(f"\n{len(skipped)} skipped pair(s). Review them now? [y] yes  [q] quit")
                if getkey("yq") == "y":
                    queue, skipped, pos = skipped, [], 0
                    continue
            break
        i = queue[pos]
        row = rows[i]
        done = sum(1 for r in rows if r.get("status") != "unchecked")
        show(row, done, total, counts())
        k = getkey("ynesuq")
        if k == "q":
            break
        if k == "s":
            skipped.append(i)
            pos += 1
            continue
        if k == "u":
            if not history:
                print("Nothing to undo.")
                continue
            j, before = history.pop()
            rows[j] = before
            save(path, header, rows)
            queue.insert(pos, j)
            continue
        new = dict(row)
        if k == "y":
            new["status"] = "accepted"
        elif k == "n":
            reason = ask_reason()
            if not reason:
                continue
            new["status"], new["reason"] = "rejected", reason
        elif k == "e":
            edited = edit(row)
            if edited is None:
                continue
            new = edited
            new["status"] = "edited"
        new["reviewer"] = reviewer
        new["reviewed_at"] = datetime.now().isoformat(timespec="seconds")
        history.append((i, dict(row)))
        rows[i] = new
        save(path, header, rows)
        pos += 1

    c = counts()
    left = sum(1 for r in rows if r.get("status") == "unchecked")
    print(f"\nSaved {path}: accepted {c['accepted']}, edited {c['edited']}, rejected {c['rejected']}, "
          f"unchecked {left}.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file")
    p.add_argument("--reviewer", default=os.environ.get("UZBLIMP_REVIEWER"),
                   help="your initials, e.g. KN or JM (or set UZBLIMP_REVIEWER)")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if os.name == "nt":
        os.system("")  # turn on ANSI colours in the Windows console
    if not args.reviewer:
        p.error("give --reviewer (e.g. KN)")
    missing = [c for c in COLUMNS if c not in read(args.file)[0]]
    if missing:
        p.error(f"{args.file} is missing columns {missing}")
    try:
        review(args.file, args.reviewer.upper())
    except KeyboardInterrupt:
        print("\nStopped. Everything decided so far is saved.")


if __name__ == "__main__":
    main()
