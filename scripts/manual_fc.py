"""Shared parts of the forced-choice runs that are done by hand: scripts/antigravity_fc.py (Google Antigravity) and
scripts/gemini_app_fc.py (the Gemini app). The order of the 96 requests, the kit's settings, the log, the questions
asked at the keyboard, the clipboard and the per-pair result files."""
import csv
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude_fc as fc  # noqa: E402

ALPHABETS = ["latn", "cyrl", "latn_reformed"]
NAMES = {"latn": "current Latin", "cyrl": "Cyrillic", "latn_reformed": "reformed Latin"}
LOG_FIELDS = ["time", "n", "request", "result", "model", "level", "sha256", "conversation", "tools", "note"]


def run_order(plan):
    """The 96 requests as (pass, alphabet, batch index), in the order to run them: pass A in the three alphabets,
    batch by batch (current Latin 1, Cyrillic 1, reformed Latin 1, current Latin 2, ...), then pass B in the same
    way. A run that stops early thus has the same pairs in every alphabet, and pass A, the one order of the
    OpenRouter runs, comes first."""
    return [(p, a, b) for p in "AB" for b in range(len(plan["batches"])) for a in ALPHABETS]


def describe(p, a, b):
    return f"{NAMES[a]}, pass {p}, batch {b + 1}"


def outside_repo(folder):
    """The kit folder, which must not be inside this repository (the repository holds the answers) and must not
    hold a kit already."""
    folder = Path(os.path.abspath(Path(folder).expanduser()))
    if folder == fc.ROOT or fc.ROOT in folder.parents or folder.resolve() == fc.ROOT \
            or fc.ROOT in folder.resolve().parents:
        sys.exit(f"{folder} is inside the uzblimp folder, which holds the answers. Choose a folder outside it, "
                 f"for example {fc.ROOT.parent / folder.name}")
    if (folder / "kit.json").exists():
        sys.exit(f"{folder} already holds a kit. Use a new folder for a new kit.")
    return folder


def slug(model):
    return re.sub(r"[^a-z0-9.]+", "-", model.lower()).strip("-")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path):
    """A text file as saved by any editor: UTF-8 with or without a byte-order mark, or UTF-16."""
    data = path.read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    return data.decode("utf-8-sig", "replace")


def git_commit():
    try:
        return subprocess.run(["git", "-C", str(fc.ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=20).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def save_settings(folder, **settings):
    settings.update(created=now(), commit=git_commit())
    (folder / "kit.json").write_text(json.dumps(settings, indent=1, ensure_ascii=False), encoding="utf-8")


def load_settings(folder, kind):
    folder = Path(os.path.abspath(Path(folder).expanduser()))
    f = folder / "kit.json"
    if not f.exists():
        sys.exit(f"{folder} is not a kit folder (it has no kit.json). Make one with the kit command first.")
    try:
        settings = json.loads(f.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        sys.exit(f"{f} cannot be read ({e}). Undo the change to it, or make a new kit.")
    if settings.get("kind") != kind:
        sys.exit(f"{folder} is a kit for {settings.get('kind')}, not for {kind}.")
    return folder, settings


def log(folder, settings, **row):
    """Appends one line to the kit's log.csv."""
    f = folder / "log.csv"
    new = not f.exists()
    row = {**row, "model": settings["model"], "level": settings["level"], "time": now()}
    with open(f, "a", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_FIELDS})


def read_log(folder):
    f = folder / "log.csv"
    if not f.exists():
        return []
    with open(f, newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def kept(folder):
    """{request: sha256 of its kept answer}, from the last line of the log about each request."""
    last = {}
    for row in read_log(folder):
        last[row["request"]] = row
    return {r: row["sha256"] for r, row in last.items() if row["result"] == "kept" and row["sha256"]}


def set_aside(path, folder):
    """Moves a file that is not used into the kit's rejected/ folder, under a name that keeps its folder and time."""
    dest = folder / "rejected"
    dest.mkdir(exist_ok=True)
    base = f"{path.parent.name}_{path.stem}_{datetime.datetime.now():%Y%m%d-%H%M%S}"
    target, i = dest / f"{base}{path.suffix}", 1
    while target.exists():
        i += 1
        target = dest / f"{base}_{i}{path.suffix}"
    shutil.move(str(path), str(target))
    return target


def flush_input():
    """Drops keys pressed before a question is shown, so that an Enter typed ahead does not answer it."""
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getwch()
    except ImportError:
        try:
            import termios
            if sys.stdin.isatty():
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except (ImportError, OSError, ValueError):
            pass


def ask(question, default="y"):
    """A yes/no question with a default; returns True for yes."""
    hint = "[Y/n]" if default == "y" else "[y/N]"
    while True:
        a = input(f"{question} {hint} ").strip().lower()
        if not a:
            return default == "y"
        if a in ("y", "yes", "n", "no"):
            return a.startswith("y")
        print("Type y or n.")


def confirm(question):
    """A check that has to be answered: y or n, optionally followed by a note. Returns (yes, note)."""
    flush_input()
    while True:
        m = re.fullmatch(r"(?i)\s*(y|yes|n|no)\b[\s,:;.\-]*(.*)", input(f"{question} ") or "")
        if m:
            return m.group(1)[0].lower() == "y", m.group(2).strip()
        print("  Type y or n; a note may follow, for example: n it tried a command")


class Clipboard:
    """The system clipboard through tkinter, or else the system's own commands (PowerShell on Windows, pbcopy and
    pbpaste on macOS). .ok is False when neither works; the steps are then done by hand."""

    def __init__(self):
        self.tk, self.kind = None, None
        try:
            import tkinter
            self.tk = tkinter.Tk()
            self.tk.withdraw()
            self.kind = "tk"
        except Exception:  # no tkinter, or no display
            self.tk = None
            system = platform.system()
            if system == "Windows" and (shutil.which("powershell") or shutil.which("pwsh")):
                self.kind = "powershell"
            elif system == "Darwin" and shutil.which("pbcopy") and shutil.which("pbpaste"):
                self.kind = "mac"
        self.ok = self.kind is not None

    def put(self, text):
        if self.kind == "tk":
            self.tk.clipboard_clear()
            self.tk.clipboard_append(text)
            self.tk.update()
        elif self.kind == "powershell":
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as h:
                h.write(text)
            try:
                subprocess.run([shutil.which("powershell") or shutil.which("pwsh"), "-NoProfile", "-Command",
                                "Set-Clipboard -Value ([IO.File]::ReadAllText($env:UZBLIMP_CLIP, "
                                "[Text.Encoding]::UTF8))"], env={**os.environ, "UZBLIMP_CLIP": h.name},
                               check=True, timeout=60)
            finally:
                os.unlink(h.name)
        elif self.kind == "mac":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), env={**os.environ, "LANG": "en_US.UTF-8"},
                           check=True, timeout=60)

    def get(self):
        try:
            if self.kind == "tk":
                return self.tk.clipboard_get()
            if self.kind == "powershell":
                p = subprocess.run([shutil.which("powershell") or shutil.which("pwsh"), "-NoProfile", "-Command",
                                    "[Console]::OutputEncoding = [Text.Encoding]::UTF8; Get-Clipboard -Raw"],
                                   capture_output=True, timeout=60)
                return p.stdout.decode("utf-8", "replace")
            if self.kind == "mac":
                p = subprocess.run(["pbpaste"], capture_output=True, env={**os.environ, "LANG": "en_US.UTF-8"},
                                   timeout=60)
                return p.stdout.decode("utf-8", "replace")
        except Exception:
            return ""
        return ""


def scrub(text, *folders):
    """The text without the names of the given folders and of the home folder, in any of their spellings."""
    for path, name in [(f, "<kit>") for f in folders] + [(Path.home(), "~")]:
        s = str(path)
        for form in {s, s.replace("\\", "/"), s.replace("\\", "\\\\"), s.replace("/", "\\"),
                     s.replace("/", "\\\\")}:
            text = re.sub(re.escape(form), name.replace("\\", "\\\\"), text, flags=re.I)
    return text


def publish(src, dest, *folders):
    """Copies a log or audit file into results/, without folder names."""
    dest.write_text(scrub(src.read_text(encoding="utf-8"), *folders), encoding="utf-8")
    if Path.home().name.lower() in dest.read_text(encoding="utf-8").lower() and len(Path.home().name) > 2:
        print(f"Note: {dest.name} still contains '{Path.home().name}'; check it before committing.")


def claim_alias(out_dir, alias, settings):
    """Stops when results/ already holds a run of another kit under the same name."""
    f = out_dir / f"{alias}_kit.json"
    if f.exists() and json.loads(f.read_text(encoding="utf-8")).get("created") != settings["created"]:
        sys.exit(f"{out_dir.name}/ already holds results of another kit named {alias}. Make this kit again with "
                 f"another --alias, or remove the old files first.")


def write_results(out_dir, alias, model, level, route, answers, sources):
    """answers: {(pass, alphabet, batch index): string of N digits}; sources: the file each came from. Writes
    <out_dir>/<alias>_<alphabet>.csv with one row per answered pair and order, in benchmark order, and prints how
    many pairs each order has and which batches are still missing."""
    import pandas as pd
    plan = fc.load_plan()
    nb = len(plan["batches"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for a in ALPHABETS:
        d = fc.bench(a).set_index("id")
        rows = []
        for p in "AB":
            for b in range(nb):
                ans = answers.get((p, a, b))
                if not ans:
                    continue
                for i, it in enumerate(plan["batches"][b]):
                    good_first = (it["first_in_A"] == "grammatical") == (p == "A")
                    x = int(ans[i])
                    rows.append({"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"],
                                 "good": d.at[it["id"], "grammatical"], "bad": d.at[it["id"], "ungrammatical"],
                                 "batch": b + 1, "item": i + 1, "pass": p, "order": "gb" if good_first else "bg",
                                 "answer": x, "correct": x == (1 if good_first else 2), "file": sources[(p, a, b)],
                                 "model": model, "alphabet": a, "level": level, "route": route})
        done = {p: [b for b in range(nb) if answers.get((p, a, b))] for p in "AB"}
        cover = "; ".join(f"pass {p}: {len(done[p]) * fc.N} of {nb * fc.N} pairs" for p in "AB")
        gaps = [f"{p}{b + 1}" for p in "AB" if done[p] for b in range(nb) if b not in done[p]]
        out = out_dir / f"{alias}_{a}.csv"
        if not rows:
            out.unlink(missing_ok=True)
            print(f"{alias}_{a}: no answers yet")
            continue
        df = pd.DataFrame(rows)
        order = {i: n for n, i in enumerate(fc.bench(a).id)}
        df = df.sort_values(["id", "order"], key=lambda s: s.map(order) if s.name == "id" else s)
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"{out.name}: {cover}; accuracy {100 * df.correct.mean():.1f} ({len(df)} answers, "
              f"{int((~df.correct).sum())} wrong)" + (f"; still missing: {', '.join(gaps)}" if gaps else ""))


def keep_answers(keep, files):
    """Replaces the folder of published answer files with the given ones."""
    shutil.rmtree(keep, ignore_errors=True)
    if files:
        keep.mkdir(parents=True)
        for src, name in files:
            shutil.copy2(src, keep / name)
