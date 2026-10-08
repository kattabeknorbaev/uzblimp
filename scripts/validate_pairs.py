"""Check UzBLiMP pair files against the format in data/README.md.

Errors (exit code 1): missing columns, invalid values, duplicate ids or pairs,
pairs that differ in more than one place, mixed scripts, apostrophes other
than U+02BB in oʻ/gʻ, empty or identical sentences.
Warnings: sentence length outside the preferred range, reused grammatical
sentences, possible personal data, multi-word changes, word-order pairs whose
words don't match.

    python scripts/validate_pairs.py data/pairs_v0.tsv [more files ...]
    python scripts/validate_pairs.py --selftest
"""
import argparse
import csv
import difflib
import re
import sys
from collections import Counter, defaultdict

from schema import (APOS_BAD, COLUMNS, CYR_RE, LAT_RE, METHODS, OG_BAD_APOS_RE, PHENOMENA,
                    STATUSES, WORD_ORDER, n_words, tokens)

ID_RE = re.compile(r"^[a-z_]+-\d{4}$")
PHONE_RE = re.compile(r"(?:\+?998[\s-]?)?\(?\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b")
EMAIL_RE = re.compile(r"\S+@\S+\.\w+")


def changed_region(a, b):
    """Strip the common prefix and suffix; return the differing middle of a and b."""
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[-1 - j] == b[-1 - j]:
        j += 1
    return a[i:len(a) - j], b[i:len(b) - j]


def check_pair(row, min_words=4, max_words=15):
    """Return (errors, warnings) for one row."""
    errs, warns = [], []
    pid, ph = row.get("id", ""), row.get("phenomenon", "")
    g, u = (row.get("grammatical") or "").strip(), (row.get("ungrammatical") or "").strip()

    if not ID_RE.match(pid):
        errs.append(f"id {pid!r} is not <phenomenon>-<4 digits>")
    elif not pid.startswith(ph + "-"):
        warns.append(f"id prefix doesn't match phenomenon {ph!r}")
    if ph not in PHENOMENA:
        errs.append(f"unknown phenomenon {ph!r}")
    if row.get("method") not in METHODS:
        errs.append(f"method {row.get('method')!r} not in {sorted(METHODS)}")
    if row.get("status") not in STATUSES:
        errs.append(f"status {row.get('status')!r} not in {sorted(STATUSES)}")
    if row.get("status") == "rejected" and not (row.get("reason") or row.get("notes")):
        warns.append("rejected without a reason")

    if not g or not u:
        errs.append("empty sentence")
        return errs, warns
    if g == u:
        errs.append("grammatical and ungrammatical are identical")
        return errs, warns

    for label, s in (("grammatical", g), ("ungrammatical", u)):
        if LAT_RE.search(s) and CYR_RE.search(s):
            errs.append(f"{label}: mixes Latin and Cyrillic letters")
        bad = sorted({m[1] for m in OG_BAD_APOS_RE.findall(s)})
        if bad:
            errs.append(f"{label}: oʻ/gʻ written with {', '.join(f'U+{ord(c):04X}' for c in bad)} instead of U+02BB")
        n = n_words(s)
        if n > max_words:
            warns.append(f"{label}: {n} words (> {max_words})")
        elif n < min_words:
            warns.append(f"{label}: {n} words (< {min_words})")
        if PHONE_RE.search(s) or EMAIL_RE.search(s):
            warns.append(f"{label}: possible phone number or e-mail")

    tg, tu = tokens(g), tokens(u)
    if ph in WORD_ORDER:
        rg, ru = changed_region(tg, tu)
        if Counter(rg) != Counter(ru):
            errs.append("word-order pair: the changed region doesn't contain the same words")
        elif len(rg) > 6:
            warns.append(f"word-order change spans {len(rg)} tokens")
    else:
        blocks = [op for op in difflib.SequenceMatcher(a=tg, b=tu, autojunk=False).get_opcodes()
                  if op[0] != "equal"]
        if len(blocks) > 1:
            places = ["/".join(tg[i1:i2]) + " → " + "/".join(tu[j1:j2]) for _, i1, i2, j1, j2 in blocks]
            errs.append(f"differs in {len(blocks)} places: {'; '.join(places)}")
        elif blocks:
            tag, i1, i2, j1, j2 = blocks[0]
            a, b = i2 - i1, j2 - j1
            # Inserting/deleting adjacent words (hech qachon) is one place; replacing
            # several adjacent words on both sides is several changes side by side.
            if tag == "replace" and a > 1 and b > 1:
                errs.append(f"{a} adjacent words replaced ({' '.join(tg[i1:i2])} → {' '.join(tu[j1:j2])}); "
                            "change one word only")
            elif max(a, b) > 2:
                warns.append(f"one place, but {max(a, b)} tokens inserted/deleted/replaced")
    return errs, warns


def validate(rows_by_file, min_words=4, max_words=15):
    """rows_by_file: {name: (header, rows)}. Returns (errors, warnings, counts)."""
    errors, warnings = [], []
    ids, pairs, goods = Counter(), Counter(), defaultdict(list)
    counts = defaultdict(Counter)
    for name, (header, rows) in rows_by_file.items():
        missing = [c for c in COLUMNS if c not in header]
        if missing:
            errors.append((name, "-", f"missing columns: {missing}"))
            continue
        for k, row in enumerate(rows, start=2):
            where = (name, row.get("id") or f"line {k}")
            e, w = check_pair(row, min_words, max_words)
            errors += [(*where, m) for m in e]
            warnings += [(*where, m) for m in w]
            ids[row.get("id")] += 1
            pairs[(row.get("grammatical", "").strip(), row.get("ungrammatical", "").strip())] += 1
            goods[(row.get("phenomenon"), row.get("grammatical", "").strip())].append(row.get("id"))
            counts[row.get("phenomenon")][row.get("status")] += 1
    errors += [("*", i, f"duplicate id ({n}×)") for i, n in ids.items() if n > 1]
    errors += [("*", f"{g[:40]}…", f"duplicate pair ({n}×)") for (g, _), n in pairs.items() if n > 1]
    warnings += [("*", ", ".join(v), "same grammatical sentence reused in one phenomenon")
                 for v in goods.values() if len(v) > 1]
    return errors, warnings, counts


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        return reader.fieldnames or [], list(reader)


def report(errors, warnings, counts):
    for title, items in (("ERRORS", errors), ("WARNINGS", warnings)):
        if items:
            print(f"\n{title} ({len(items)})")
            for f, i, m in items:
                print(f"  {f}: {i}: {m}")
    print(f"\n{'phenomenon':22} {'total':>6} {'unchecked':>10} {'accepted':>9} {'edited':>7} {'rejected':>9}")
    total = Counter()
    for ph in list(PHENOMENA) + sorted(k for k in counts if k not in PHENOMENA):
        c = counts.get(ph, Counter())
        n = sum(c.values())
        total.update(c)
        print(f"{ph:22} {n:>6} {c['unchecked']:>10} {c['accepted']:>9} {c['edited']:>7} {c['rejected']:>9}")
    print(f"{'TOTAL':22} {sum(total.values()):>6} {total['unchecked']:>10} {total['accepted']:>9} "
          f"{total['edited']:>7} {total['rejected']:>9}")
    print("\n" + ("CLEAN" if not errors else f"{len(errors)} error(s)") + f", {len(warnings)} warning(s)")


def selftest():
    def row(i, ph, g, u, **kw):
        return {"id": f"{ph}-{i:04d}", "phenomenon": ph, "grammatical": g, "ungrammatical": u,
                "method": "hand-written", "source_id": "", "status": "unchecked", "notes": "", **kw}
    cases = [
        (row(1, "numeral_no_plural", "Uchta kitob oldim.", "Uchta kitoblar oldim."), None),
        (row(2, "npi_hech", "Koʻpchilik oldida qoʻshiq aytdim.", "Koʻpchilik oldida hech qachon qoʻshiq aytdim."), None),
        (row(3, "scrambling", "Hasanning maqolani yozganini bilaman.", "Hasanning yozganini maqolani bilaman."), None),
        (row(4, "lexical_case", "Ukam itdan qoʻrqadi.", "Akam itni qoʻrqadi."), "adjacent words replaced"),
        (row(12, "lexical_case", "Ukam har doim itdan qoʻrqadi.", "Akam har doim itni qoʻrqadi."), "differs in 2 places"),
        (row(13, "impersonal_passive", "Ertalab oʻquvchilar tomonidan maktab hovlisida yugurildi.",
             "Ertalab maktab hovlisida yugurildi."), None),
        (row(5, "lexical_case", "Ukam itdan qo'rqadi.", "Ukam itni qo'rqadi."), "instead of U+02BB"),
        (row(6, "lexical_case", "Ukam итдан qoʻrqadi.", "Ukam itni qoʻrqadi."), "mixes Latin and Cyrillic"),
        (row(7, "lexical_case", "", "Ukam itni qoʻrqadi."), "empty sentence"),
        (row(8, "lexical_case", "Ukam itdan qoʻrqadi.", "Ukam itdan qoʻrqadi."), "identical"),
        (row(9, "foo", "Ukam itdan qoʻrqadi.", "Ukam itni qoʻrqadi."), "unknown phenomenon"),
        (row(10, "ellipsis", "Lola kurtkani va Jasur shimni tanladi.", "Lola kurtkani va shimni Lola tanladi."),
         "same words"),
        (row(11, "lexical_case", "Telefon +998 90 123 45 67 dan qoʻrqadi.", "Telefon +998 90 123 45 67 ni qoʻrqadi."),
         "phone"),
    ]
    fails = 0
    for r, expect in cases:
        e, w = check_pair(r)
        msgs = " | ".join(e + w)
        ok = (not e) if expect is None else (expect in msgs)
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} {r['id']:24} expect={expect!r:28} got: {msgs or 'clean'}")
    hdr = COLUMNS
    dup = {"f": (hdr, [cases[0][0], dict(cases[0][0])])}
    e, _, _ = validate(dup)
    ok = any("duplicate id" in m for _, _, m in e)
    fails += not ok
    print(f"{'ok ' if ok else 'FAIL'} duplicate detection")
    print(f"\n{fails} failure(s)")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="*")
    p.add_argument("--min-words", type=int, default=4)
    p.add_argument("--max-words", type=int, default=15)
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    if not args.files:
        p.error("give at least one TSV file")
    errors, warnings, counts = validate({f: read_tsv(f) for f in args.files}, args.min_words, args.max_words)
    report(errors, warnings, counts)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
