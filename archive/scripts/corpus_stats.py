"""Corpus statistics and minimal-pair candidate search for UzBLiMP.

Streams the corpus (a .zip, or a folder of .txt / .jsonl files) one line at a
time and reports, per top-level part (e.g. books/, legal/, wiki/):
  - documents, paragraphs (lines), sentences and words;
  - Latin vs Cyrillic letters, and documents by majority script;
  - which apostrophe-like characters follow o/g (oʻ/gʻ spellings);
  - candidate sentences for three phenomena, with random examples saved to
    data/candidates/ (git-ignored: corpus text stays on this machine).

A document is one .txt file, or one line of a .jsonl file (its "text" field).
Sentence splitting and pattern matching are heuristic regexes, so counts are
approximate; the saved examples are there to check precision by hand.
No normalization is applied: text is matched and saved exactly as stored.

    python scripts/corpus_stats.py --corpus "D:/drive-download-20260601T072834Z-3-001.zip"
    python scripts/corpus_stats.py --selftest
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import random
import re
import sys
import time
import zipfile
from pathlib import Path

# Apostrophe-like characters seen in Uzbek Latin text: ʻ ' ’ ` ‘ ʼ ´
APOS_CHARS = "\u02bb'\u2019`\u2018\u02bc\u00b4"
APOS_NAMES = {
    "\u02bb": "U+02BB ʻ (standard)",
    "'": "U+0027 ' (ASCII)",
    "\u2019": "U+2019 ’",
    "`": "U+0060 `",
    "\u2018": "U+2018 ‘",
    "\u02bc": "U+02BC ʼ",
    "\u00b4": "U+00B4 ´",
}
A = f"[{APOS_CHARS}]"
L = rf"(?:[^\W\d_]|{A})"  # a letter, or an apostrophe inside a word (boʻlgandan)

WORD_RE = re.compile(rf"[^\W\d_]+(?:(?:{A}|-)[^\W\d_]+)*{A}?")
OG_APOS_RE = re.compile(rf"(?<=[oOgG]){A}")
LAT_RE = re.compile(r"[A-Za-z\u00C0-\u024F]")
CYR_RE = re.compile(r"[\u0400-\u04FF]")
REFORMED = "öÖğĞşŞçÇ"
SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")

# a) ablative + keyin: "darsdan keyin" / "дарсдан кейин" (not keyingi, keyinroq)
KEYIN_RE = re.compile(rf"{L}+(?:dan|дан)\s+(?:keyin|кейин)\b", re.I)

# b) hech + negation. The negated verb is searched after "hech" in the same sentence.
HECH_RE = re.compile(rf"\b(?:hech|ҳеч|хеч)\s+({L}+)", re.I)
HECH_STEMS = ["kim", "narsa", "nima", "qachon", "qayer", "qay", "bir", "qanday", "ham", "vaqt",
              "ким", "нарса", "нима", "қачон", "қаер", "қай", "бир", "қандай", "ҳам", "вақт"]
# -ma- followed by a verbal suffix (kelmadi, bilmayman, koʻrmagan, aytmang, kelmas ...).
# At least 2 letters before -ma- so that words starting with "ma" don't match.
# -masin/-masa/-mang must end the word, or hamma-si-ni would count as negated.
# Known false positive: verbs whose stem ends in -ma (kamaydi "decreased").
NEG_VERB_RE = re.compile(
    rf"{L}{{2,}}(?:ma(?:y|di|gan|ng(?:iz)?\b|sin\b|sa(?:m|ng|k|ngiz|lar)?\b|sdan|slik|sdi|s\b|yap)"
    rf"|ма(?:й|ди|ган|нг(?:из)?\b|син\b|са(?:м|нг|к|нгиз|лар)?\b|сдан|слик|сди|с\b|ёп))",
    re.I,
)
HECH_IDIOM_RE = re.compile(rf"(?:bo{A}lmasa|бўлмаса)\b", re.I)
NEG_COPULA_RE = re.compile(rf"\b(?:emas|yo{A}q|эмас|йўқ)\b", re.I)

# c) numeral + -ta + next word: "uchta kitob" / "учта китоб" / "5 ta kitob"
NUM_LAT = (rf"(?:bit|ikki|uch|to{A}rt|besh|olti|yetti|sakkiz|to{A}qqiz|o{A}n|yigirma|"
           rf"o{A}ttiz|qirq|ellik|oltmish|yetmish|sakson|to{A}qson|yuz|ming)")
NUM_CYR = (r"(?:бит|икки|уч|тўрт|беш|олти|етти|саккиз|тўққиз|ўн|йигирма|ўттиз|қирқ|"
           r"эллик|олтмиш|етмиш|саксон|тўқсон|юз|минг)")
NUM_TA_RE = re.compile(rf"\b(?:{NUM_LAT}|{NUM_CYR}|\d+[\s-]?)(?:ta|та)\s+({L}+)", re.I)

MIN_WORDS, MAX_WORDS = 4, 30  # sentence length range for saved examples


class Reservoir:
    """Uniform random sample of k items from a stream of unknown length."""

    def __init__(self, k, seed):
        self.k, self.n, self.items = k, 0, []
        self.rng = random.Random(seed)

    def add(self, item):
        self.n += 1
        if len(self.items) < self.k:
            self.items.append(item)
        else:
            j = self.rng.randrange(self.n)
            if j < self.k:
                self.items[j] = item


def split_sentences(line):
    """Split after . ! ? … unless the next piece starts lowercase."""
    out = []
    for piece in SPLIT_RE.split(line.strip()):
        if not piece:
            continue
        first = next((c for c in piece if c.isalpha()), "")
        if out and first.islower():
            out[-1] += " " + piece
        else:
            out.append(piece)
    return out


def script_of(text):
    return "cyrl" if CYR_RE.search(text) else "latn"


def hech_category(word):
    w = word.lower()
    return next((s for s in HECH_STEMS if w.startswith(s)), "other")


def classify_hech(sentence):
    """Return (category of the word after hech, negation type) or None."""
    m = HECH_RE.search(sentence)
    if not m:
        return None
    if HECH_IDIOM_RE.match(m.group(1)):  # hech boʻlmasa = "at least", not negative concord
        return "idiom", "idiom"
    rest = sentence[m.start(1):]  # include the word right after hech (Hech tushunmadim)
    if NEG_VERB_RE.search(rest):
        neg = "neg_verb"
    elif NEG_COPULA_RE.search(rest):
        neg = "neg_copula"
    else:
        neg = "none"
    return hech_category(m.group(1)), neg


def find_num_ta(sentence):
    """Return [(matched text, next word, next word looks plural)]."""
    out = []
    for m in NUM_TA_RE.finditer(sentence):
        nxt = m.group(1).lower()
        out.append((m.group(0), m.group(1), len(nxt) > 3 and ("lar" in nxt or "лар" in nxt)))
    return out


def iter_documents(corpus, skipped):
    """Yield (part, doc_name, iterator over lines). Lines must be consumed in order."""
    if zipfile.is_zipfile(corpus):
        z = zipfile.ZipFile(corpus)
        names = sorted(i.filename for i in z.infolist() if not i.is_dir())
        opener = lambda n: io.TextIOWrapper(z.open(n), encoding="utf-8-sig")
    else:
        root = Path(corpus)
        names = sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file())
        opener = lambda n: open(root / n, encoding="utf-8-sig")
    for name in names:
        part = name.split("/")[0] if "/" in name else "."
        ext = os.path.splitext(name)[1].lower()
        if ext == ".txt":
            with opener(name) as fh:
                yield part, name, fh
        elif ext == ".jsonl":
            with opener(name) as fh:
                for i, line in enumerate(fh):
                    d = json.loads(line)
                    skipped["jsonl_source:" + str(d.get("source"))] += 1
                    yield part, f"{name}#{d.get('doc_id', i)}", iter(d.get("text", "").splitlines())
        else:
            skipped[f"skipped_file:{ext or '(none)'}"] += 1


def run(args):
    t0 = time.time()
    skipped = collections.Counter()
    parts = collections.defaultdict(collections.Counter)
    apos = collections.defaultdict(collections.Counter)  # part -> char -> count after o/g
    apos_any = collections.Counter()  # char -> count anywhere
    seen_hashes = collections.defaultdict(set)
    cand = collections.Counter()
    hech_cats = collections.Counter()
    seeds = lambda name: f"{args.seed}-{name}"
    res = {
        "keyin_ablative": Reservoir(args.n_examples, seeds("keyin")),
        "hech_negated_verb": Reservoir(args.n_examples, seeds("hech_neg")),
        "hech_no_negation": Reservoir(args.n_examples, seeds("hech_none")),
        "numeral_ta_noun": Reservoir(args.n_examples, seeds("num")),
        "numeral_ta_plural": Reservoir(args.n_examples, seeds("num_pl")),
    }

    n_docs = 0
    for part, doc, lines in iter_documents(args.corpus, skipped):
        p = parts[part]
        h = hashlib.md5()
        lat = cyr = 0
        for line in lines:
            h.update(line.encode("utf-8"))
            if not line.strip():
                continue
            p["paragraphs"] += 1
            p["words"] += len(WORD_RE.findall(line))
            nl, nc = len(LAT_RE.findall(line)), len(CYR_RE.findall(line))
            lat, cyr = lat + nl, cyr + nc
            for c in OG_APOS_RE.findall(line):
                apos[part][c] += 1
            for c in APOS_CHARS:
                apos_any[c] += line.count(c)
            p["reformed_letters"] += sum(line.count(c) for c in REFORMED)

            low = line.lower()
            check_keyin = "keyin" in low or "кейин" in low
            check_hech = "hech" in low or "ҳеч" in low or "хеч" in low
            for s in split_sentences(line):
                p["sentences"] += 1
                nw = None
                if check_keyin and KEYIN_RE.search(s):
                    nw = len(WORD_RE.findall(s))
                    cand[f"keyin:sentences:{script_of(s)}"] += 1
                    if MIN_WORDS <= nw <= MAX_WORDS:
                        cand["keyin:usable"] += 1
                        res["keyin_ablative"].add((part, doc, script_of(s), KEYIN_RE.search(s).group(0), s))
                if check_hech:
                    hc = classify_hech(s)
                    if hc:
                        cat, neg = hc
                        nw = nw or len(WORD_RE.findall(s))
                        cand[f"hech:{neg}:{script_of(s)}"] += 1
                        hech_cats[f"{cat}:{neg}"] += 1
                        if MIN_WORDS <= nw <= MAX_WORDS:
                            cand[f"hech:{neg}:usable"] += 1
                            m = HECH_RE.search(s).group(0)
                            if neg == "neg_verb":
                                res["hech_negated_verb"].add((part, doc, script_of(s), m, s))
                            elif neg == "none":
                                res["hech_no_negation"].add((part, doc, script_of(s), m, s))
                hits = find_num_ta(s)
                if hits:
                    nw = nw or len(WORD_RE.findall(s))
                    for text, _, plural in hits:
                        kind = "plural" if plural else "other"
                        cand[f"num_ta:{kind}:{script_of(text)}"] += 1
                        if MIN_WORDS <= nw <= MAX_WORDS:
                            cand[f"num_ta:{kind}:usable"] += 1
                            res["numeral_ta_plural" if plural else "numeral_ta_noun"].add(
                                (part, doc, script_of(text), text, s))
        p["documents"] += 1
        p["latin_letters"] += lat
        p["cyrillic_letters"] += cyr
        total = lat + cyr
        if total == 0:
            p["docs_no_letters"] += 1
        elif lat / total >= 0.9:
            p["docs_mostly_latin"] += 1
        elif cyr / total >= 0.9:
            p["docs_mostly_cyrillic"] += 1
        else:
            p["docs_mixed"] += 1
        digest = h.hexdigest()
        if digest in seen_hashes[part]:
            p["exact_duplicate_docs"] += 1
        seen_hashes[part].add(digest)
        n_docs += 1
        if args.limit_docs and n_docs >= args.limit_docs:
            break
        if n_docs % 20000 == 0:
            print(f"  ... {n_docs:,} documents, {time.time() - t0:.0f}s", flush=True)

    # Write candidate examples (local only; data/candidates/ is git-ignored)
    cand_dir = Path(args.cand_dir)
    cand_dir.mkdir(parents=True, exist_ok=True)
    for name, r in res.items():
        with open(cand_dir / f"{name}.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            w.writerow(["part", "doc", "script", "match", "sentence"])
            w.writerows(r.items)

    totals = collections.Counter()
    for c in parts.values():
        totals.update(c)
    corpus_path = Path(args.corpus)
    stats = {
        "corpus": str(corpus_path),
        "corpus_bytes": corpus_path.stat().st_size if corpus_path.is_file() else None,
        "corpus_sha256": sha256(corpus_path) if corpus_path.is_file() else None,
        "run_seconds": round(time.time() - t0),
        "limit_docs": args.limit_docs,
        "seed": args.seed,
        "example_sentence_words": [MIN_WORDS, MAX_WORDS],
        "parts": {k: dict(v) for k, v in parts.items()},
        "totals": dict(totals),
        "apostrophe_after_o_g": {k: {APOS_NAMES[c]: n for c, n in v.most_common()} for k, v in apos.items()},
        "apostrophe_anywhere": {APOS_NAMES[c]: n for c, n in apos_any.most_common()},
        "candidates": dict(sorted(cand.items())),
        "hech_word_by_negation": dict(sorted(hech_cats.items())),
        "candidate_pool_sizes": {k: r.n for k, r in res.items()},
        "skipped_and_metadata": dict(skipped),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    report(stats)
    print(f"\nWrote {args.out} and {len(res)} files in {cand_dir}/ ({stats['run_seconds']}s)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def report(s):
    print(f"\n{'part':8} {'docs':>9} {'sentences':>11} {'words':>12} {'Latin %':>8} {'Cyr-docs':>9} {'Lat-docs':>9} {'mixed':>6} {'dups':>5}")
    for name, p in sorted(s["parts"].items()) + [("TOTAL", s["totals"])]:
        letters = p.get("latin_letters", 0) + p.get("cyrillic_letters", 0)
        lat_share = 100 * p.get("latin_letters", 0) / letters if letters else 0
        print(f"{name:8} {p.get('documents', 0):>9,} {p.get('sentences', 0):>11,} {p.get('words', 0):>12,} "
              f"{lat_share:>7.1f}% {p.get('docs_mostly_cyrillic', 0):>9,} {p.get('docs_mostly_latin', 0):>9,} "
              f"{p.get('docs_mixed', 0):>6,} {p.get('exact_duplicate_docs', 0):>5,}")
    print("\nCharacter after o/g, per part:")
    for part, d in s["apostrophe_after_o_g"].items():
        total = sum(d.values()) or 1
        print(f"  {part:6} " + " | ".join(f"{k}: {v:,} ({100 * v / total:.1f}%)" for k, v in d.items()))
    print("\nCandidates (sentences; num_ta counts matches):")
    for k, v in s["candidates"].items():
        print(f"  {k:28} {v:>9,}")


def selftest():
    """Check the patterns on hand-written sentences (not corpus text)."""
    keyin = [("Darsdan keyin uchrashamiz.", True), ("Ishdan keyin uyga bordim.", True),
             ("Boʻlgandan keyin keldi.", True), ("Дарсдан кейин учрашамиз.", True),
             ("Bu keyingi dars.", False), ("Keyin uchrashamiz.", False), ("Darsdan keyinroq keldi.", False)]
    hech = [("Hech kim kelmadi.", ("kim", "neg_verb")), ("Men hech narsani bilmayman.", ("narsa", "neg_verb")),
            ("Hech kim keldimi?", ("kim", "none")), ("Hech narsa yoʻq.", ("narsa", "neg_copula")),
            ("Ҳеч ким келмади.", ("ким", "neg_verb")), ("Hech qachon koʻrmaganman.", ("qachon", "neg_verb")),
            ("Hamma keldi.", None), ("Hech kim hammasini oldi.", ("kim", "none")),
            ("Hech kim aytmang.", ("kim", "neg_verb")), ("Hech kim kelmasin.", ("kim", "neg_verb")),
            ("Hech kim kelmasa ham boramiz.", ("kim", "neg_verb")),
            ("Hech boʻlmasa bir marta keling.", ("idiom", "idiom")),
            ("Men hech tushunmadim.", ("other", "neg_verb"))]
    num = [("Uchta kitob oldim.", [("kitob", False)]), ("Uchta kitoblar oldim.", [("kitoblar", True)]),
           ("Toʻrtta olma bor.", [("olma", False)]), ("Учта китоб олдим.", [("китоб", False)]),
           ("5 ta talaba keldi.", [("talaba", False)]), ("Bitta odam keldi.", [("odam", False)]),
           ("Uch tarafdan keldi.", [])]
    fails = 0
    for s, want in keyin:
        got = bool(KEYIN_RE.search(s))
        fails += got != want
        print(f"{'ok ' if got == want else 'FAIL'} keyin  {s!r}: {got}")
    for s, want in hech:
        got = classify_hech(s)
        fails += got != want
        print(f"{'ok ' if got == want else 'FAIL'} hech   {s!r}: {got}")
    for s, want in num:
        got = [(w, pl) for _, w, pl in find_num_ta(s)]
        fails += got != want
        print(f"{'ok ' if got == want else 'FAIL'} num_ta {s!r}: {got}")
    print(f"\n{fails} failures")
    return fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", help="corpus .zip or folder")
    p.add_argument("--out", default="results/corpus_stats.json")
    p.add_argument("--cand-dir", default="data/candidates")
    p.add_argument("--n-examples", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--limit-docs", type=int, help="stop after N documents (quick tests)")
    p.add_argument("--selftest", action="store_true", help="check the patterns and exit")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(1 if selftest() else 0)
    if not args.corpus:
        p.error("--corpus is required")
    run(args)


if __name__ == "__main__":
    main()
