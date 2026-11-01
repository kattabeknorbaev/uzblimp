"""Check the release files in data/jsonl/ (written by export_jsonl.py).

Errors (exit code 1): lines that aren't JSON, missing or mistyped fields, values outside the allowed
sets, a record in the wrong file or folder, repeated ids or pairs, alphabets with different ids,
`verified` without `verifier_id` (or the reverse), a `lexically_identical` flag that doesn't match the
sentences, ʻ left in Cyrillic or reformed text, and every pair-level error validate_pairs.py reports:
more than one place changed, oʻ/gʻ written with anything but U+02BB, mixed scripts, empty or
identical sentences. Roman numerals (XV asr) are allowed in Cyrillic text.
Warnings: what validate_pairs.py warns about, a phenomenon without 150 pairs, and sentences more
than --max-edit characters apart (the benchmark's pairs differ by 1-6).

    python scripts/validate.py              # checks data/jsonl
    python scripts/validate.py --selftest
"""
import argparse
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from schema import FIELDS, METHODS, RELEASE_PHENOMENA, SCRIPT_FILES, tokens
from validate_pairs import check_pair

ROOT = Path(__file__).resolve().parent.parent
PER_PHENOMENON = 150
REQUIRED = {"pair_id": str, "paradigm": str, "phenomenon": str, "field": str, "sentence_good": str,
            "sentence_bad": str, "lexically_identical": bool, "script": str, "source": str,
            "source_id": str, "verified": bool, "reviewer": str}
ROMAN_RE = re.compile(r"\b[IVXLCDM]+\b")


def edit_distance(a, b):
    """Levenshtein distance in characters."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_record(rec, script, paradigm, max_edit=8):
    """Return (errors, warnings) for one record read from data/jsonl/<script>/<paradigm>.jsonl."""
    errs, warns = [], []
    for key, typ in REQUIRED.items():
        if not isinstance(rec.get(key), typ):
            errs.append(f"{key}: expected {typ.__name__}, got {type(rec.get(key)).__name__}")
    if "verifier_id" not in rec or not (rec["verifier_id"] is None or isinstance(rec["verifier_id"], str)):
        errs.append("verifier_id: expected a string or null")
    if errs:
        return errs, warns

    if rec["script"] != script:
        errs.append(f"script {rec['script']!r} in the {script}/ folder")
    if rec["paradigm"] != paradigm:
        errs.append(f"paradigm {rec['paradigm']!r} in {paradigm}.jsonl")
    if rec["paradigm"] in RELEASE_PHENOMENA:
        name, field = RELEASE_PHENOMENA[rec["paradigm"]]
        if (rec["phenomenon"], rec["field"]) != (name, field):
            errs.append(f"phenomenon/field {rec['phenomenon']!r}/{rec['field']!r}, expected {name!r}/{field!r}")
    if rec["field"] not in FIELDS:
        errs.append(f"field {rec['field']!r} not in {sorted(FIELDS)}")
    if rec["source"] not in METHODS:
        errs.append(f"source {rec['source']!r} not in {sorted(METHODS)}")
    if rec["verified"] != (rec["verifier_id"] is not None):
        errs.append("verified and verifier_id disagree")

    good, bad = rec["sentence_good"], rec["sentence_bad"]
    if rec["lexically_identical"] != (sorted(tokens(good)) == sorted(tokens(bad))):
        errs.append("lexically_identical doesn't match the sentences")
    if script != "latn" and "ʻ" in good + bad:
        errs.append("ʻ (U+02BB) in Cyrillic or reformed text")
    if script == "cyrl":
        good, bad = ROMAN_RE.sub("0", good), ROMAN_RE.sub("0", bad)
    row = {"id": rec["pair_id"], "phenomenon": rec["paradigm"], "grammatical": good, "ungrammatical": bad,
           "method": rec["source"], "source_id": rec["source_id"], "status": "accepted", "notes": ""}
    e, w = check_pair(row)
    errs += e
    warns += w
    d = edit_distance(rec["sentence_good"], rec["sentence_bad"])
    if d > max_edit:
        warns.append(f"sentences are {d} characters apart (> {max_edit})")
    return errs, warns


def validate(folder, max_edit=8):
    """Returns (errors, warnings, counts) for data/jsonl-style folder; counts[script][paradigm]."""
    errors, warnings = [], []
    counts = defaultdict(Counter)
    ids_by_script = {}
    for script in SCRIPT_FILES:
        sub = Path(folder) / script
        if not sub.is_dir():
            errors.append((script, "-", "folder missing"))
            continue
        ids, pairs = Counter(), Counter()
        for path in sorted(sub.glob("*.jsonl")):
            where = f"{script}/{path.name}"
            if path.stem not in RELEASE_PHENOMENA:
                errors.append((where, "-", "not one of the 16 phenomena"))
            with open(path, encoding="utf-8") as f:
                for k, line in enumerate(f, start=1):
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append((where, f"line {k}", f"not JSON: {exc}"))
                        continue
                    e, w = check_record(rec, script, path.stem, max_edit)
                    pid = rec.get("pair_id") or f"line {k}"
                    errors += [(where, pid, m) for m in e]
                    warnings += [(where, pid, m) for m in w]
                    ids[rec.get("pair_id")] += 1
                    pairs[(rec.get("sentence_good"), rec.get("sentence_bad"))] += 1
                    counts[script][path.stem] += 1
        errors += [(script, i, f"duplicate pair_id ({n}×)") for i, n in ids.items() if n > 1]
        errors += [(script, f"{str(g)[:40]}…", f"duplicate pair ({n}×)") for (g, _), n in pairs.items() if n > 1]
        warnings += [(script, ph, f"{counts[script][ph]} pairs (expected {PER_PHENOMENON})")
                     for ph in RELEASE_PHENOMENA if counts[script][ph] != PER_PHENOMENON]
        ids_by_script[script] = set(ids)
    base = ids_by_script.get("latn")
    for script, found in ids_by_script.items():
        if base is not None and found != base:
            errors.append((script, "-", f"{len(found - base)} ids not in latn, {len(base - found)} latn ids missing"))
    return errors, warnings, counts


def report(errors, warnings, counts):
    for title, items in (("ERRORS", errors), ("WARNINGS", warnings)):
        if items:
            print(f"\n{title} ({len(items)})")
            for f, i, m in items:
                print(f"  {f}: {i}: {m}")
    scripts = list(SCRIPT_FILES)
    print(f"\n{'phenomenon':22} " + " ".join(f"{s:>14}" for s in scripts))
    for ph in RELEASE_PHENOMENA:
        print(f"{ph:22} " + " ".join(f"{counts[s][ph]:>14}" for s in scripts))
    print(f"{'TOTAL':22} " + " ".join(f"{sum(counts[s].values()):>14}" for s in scripts))
    print("\n" + ("CLEAN" if not errors else f"{len(errors)} error(s)") + f", {len(warnings)} warning(s)")


def selftest():
    def rec(**kw):
        r = {"pair_id": "numeral_no_plural-0001", "paradigm": "numeral_no_plural",
             "phenomenon": "No plural after numerals", "field": "morphology",
             "sentence_good": "Men uchta kitob oldim.", "sentence_bad": "Men uchta kitoblar oldim.",
             "lexically_identical": False, "script": "latn", "source": "corpus-edit", "source_id": "test",
             "verified": False, "verifier_id": None, "reviewer": "KN"}
        return {**r, **kw}
    cyr = {"script": "cyrl", "sentence_good": "XV асрда учта бино қурилган.",
           "sentence_bad": "XV асрда учта бинолар қурилган."}
    cases = [
        (rec(), "latn", None),
        (rec(**cyr), "cyrl", None),
        (rec(verified="no"), "latn", "verified: expected bool"),
        (rec(verified=True), "latn", "verified and verifier_id disagree"),
        (rec(field="phonology"), "latn", "not in"),
        (rec(lexically_identical=True), "latn", "lexically_identical"),
        (rec(sentence_good="Men uchta kitob oʻqidim.", sentence_bad="Men uchta kitob o'qidim."), "latn", "instead of U+02BB"),
        (rec(sentence_bad="Sen uchta kitoblar oldim."), "latn", "differs in 2 places"),
        (rec(**{**cyr, "sentence_bad": "XV асрда учта бинолар қурилган ʻ."}), "cyrl", "U+02BB) in Cyrillic"),
        (rec(script="cyrl"), "latn", "in the latn/ folder"),
        (rec(sentence_bad="Men uchta kitoblarimizdagilar oldim."), "latn", "characters apart"),
    ]
    fails = 0
    for r, script, expect in cases:
        e, w = check_record(r, script, "numeral_no_plural")
        msgs = " | ".join(e + w)
        ok = (not e and not w) if expect is None else (expect in msgs)
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} expect={expect!r:40} got: {msgs or 'clean'}")
    with tempfile.TemporaryDirectory() as tmp:
        for script in SCRIPT_FILES:
            (Path(tmp) / script).mkdir()
        line = json.dumps(rec(), ensure_ascii=False) + "\n"
        (Path(tmp) / "latn" / "numeral_no_plural.jsonl").write_text(line * 2, encoding="utf-8")
        errors, _, _ = validate(tmp)
        msgs = " | ".join(m for _, _, m in errors)
        for expect in ("duplicate pair_id", "duplicate pair (", "latn ids missing"):
            ok = expect in msgs
            fails += not ok
            print(f"{'ok ' if ok else 'FAIL'} folder check: {expect}")
    print(f"\n{fails} failure(s)")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", nargs="?", default=str(ROOT / "data" / "jsonl"))
    p.add_argument("--max-edit", type=int, default=8, help="warn when the sentences are more characters apart")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    errors, warnings, counts = validate(args.folder, args.max_edit)
    report(errors, warnings, counts)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
