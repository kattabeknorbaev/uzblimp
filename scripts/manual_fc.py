"""Shared parts of the forced-choice runs that are done by hand: scripts/antigravity_fc.py (Google Antigravity) and
scripts/gemini_app_fc.py (the Gemini app). The order of the 96 requests, the kit's settings, the log, the clipboard
and the per-pair result files."""
import csv
import datetime
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
LOG_FIELDS = ["time", "n", "request", "result", "answers", "confirmed", "tools", "note"]


def run_order(plan):
    """The 96 requests as (pass, alphabet, batch index), in the order to run them: pass A in the three alphabets,
    batch by batch (current Latin 1, Cyrillic 1, reformed Latin 1, current Latin 2, ...), then pass B in the same
    way. A run that stops early thus has the same pairs in every alphabet, and pass A, the one order of the
    OpenRouter runs, comes first."""
    return [(p, a, b) for p in "AB" for b in range(len(plan["batches"])) for a in ALPHABETS]


def describe(p, a, b):
    return f"{NAMES[a]}, pass {p}, batch {b + 1}"


def outside_repo(folder):
    """The kit folder, which must not be inside this repository: the repository holds the answers."""
    folder = Path(folder).expanduser().resolve()
    if folder == fc.ROOT or fc.ROOT in folder.parents:
        sys.exit(f"{folder} is inside the uzblimp folder, which holds the answers. Choose a folder outside it, "
                 f"for example {fc.ROOT.parent / folder.name}")
    return folder


def slug(model):
    return re.sub(r"[^a-z0-9.]+", "-", model.lower()).strip("-")


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


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
    f = Path(folder).expanduser().resolve() / "kit.json"
    if not f.exists():
        sys.exit(f"{f.parent} is not a kit folder (it has no kit.json). Make one with the kit command first.")
    settings = json.loads(f.read_text(encoding="utf-8"))
    if settings.get("kind") != kind:
        sys.exit(f"{f.parent} is a kit for {settings.get('kind')}, not for {kind}.")
    return f.parent, settings


def log(folder, **row):
    """Appends one line to the kit's log.csv."""
    f = folder / "log.csv"
    new = not f.exists()
    with open(f, "a", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({**{k: row.get(k, "") for k in LOG_FIELDS}, "time": now()})


def set_aside(path, folder):
    """Moves a reply that is not used into the kit's rejected/ folder, with the time in its name."""
    dest = folder / "rejected"
    dest.mkdir(exist_ok=True)
    target = dest / f"{path.stem}_{datetime.datetime.now():%Y%m%d-%H%M%S}{path.suffix}"
    shutil.move(str(path), str(target))
    return target


def ask(question, default="y"):
    """A yes/no question; returns True for yes."""
    hint = "[Y/n]" if default == "y" else "[y/N]"
    while True:
        a = input(f"{question} {hint} ").strip().lower()
        if not a:
            return default == "y"
        if a in ("y", "yes", "n", "no"):
            return a.startswith("y")


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
        if not rows:
            print(f"{alias}_{a}: no answers yet")
            continue
        df = pd.DataFrame(rows)
        order = {i: n for n, i in enumerate(fc.bench(a).id)}
        df = df.sort_values(["id", "order"], key=lambda s: s.map(order) if s.name == "id" else s)
        out = out_dir / f"{alias}_{a}.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"{out.name}: {cover}; accuracy {100 * df.correct.mean():.1f} ({len(df)} answers, "
              f"{int((~df.correct).sum())} wrong)"
              + (f"; still missing: {', '.join(gaps)}" if gaps else ""))
