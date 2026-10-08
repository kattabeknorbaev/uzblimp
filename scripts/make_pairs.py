"""Generate candidate minimal pairs from corpus sentences.

1. scan:  stream the corpus once, count every word form (the lexicon) and keep a
          seeded random sample of eligible sentences per phenomenon. Cached in
          data/cache/, so changing a rule doesn't need a new scan.
2. edit:  one function per phenomenon changes exactly one word of a grammatical
          sentence, or skips it with a reason.
3. write: data/pairs_v1_<phenomenon>.tsv (status "unchecked"), skip counts in
          results/make_pairs_summary.json, skipped sentences in data/cache/.

Every edit must pass:
- plausibility (as in TatBLiMP): the new word form occurs in the corpus ≥ --min-count times;
- TurkicNLP agrees on the changed morpheme (segmenter ABL/NEG; UPOS NOUN after numerals);
- scripts/validate_pairs.py (one place, apostrophes, length, ...).

    python scripts/make_pairs.py --corpus "D:/drive-download-20260601T072834Z-3-001.zip"
"""
import argparse
import csv
import json
import pickle
import random
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from corpus_stats import A, L, NEG_VERB_RE, NUM_LAT, WORD_RE, Reservoir, iter_documents, split_sentences
from schema import COLUMNS, CYR_RE, OG_BAD_APOS_RE, OPTIONAL_COLUMNS, n_words
from validate_pairs import check_pair

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"


@dataclass
class Edit:
    bad: str | None  # ungrammatical sentence, or None when skipped
    why: str  # breaking operation if bad is set, else the skip reason


def skip(reason):
    return Edit(None, reason)


# ---------------------------------------------------------------- eligibility
CAPS_INSIDE = re.compile(r"\s[^\W\d_a-zʻʼ]")  # a capitalised word after the first: names, places
BAD_CHARS = re.compile(r"[\d@«»\"“”„()\[\]{}:;/\\|<>…—–']|http|www|\s-\s|^-|-[\s.!?,]")


def eligible(s):
    """Short, single, plain sentence without names, digits, quotes or dialogue dashes."""
    if not s or not s[0].isupper() or s[-1] not in ".!?":
        return False
    if sum(s.count(c) for c in ".!?") > 1:
        return False
    if CAPS_INSIDE.search(s) or BAD_CHARS.search(s) or OG_BAD_APOS_RE.search(s) or CYR_RE.search(s):
        return False
    return 4 <= n_words(s) <= 15


# ------------------------------------------------------- numeral_no_plural
NUM_TA_WORD_RE = re.compile(rf"\b(?:{NUM_LAT})ta\s+([^\W\d_]+(?:{A}[^\W\d_]+)*)", re.I)
CASE_SUFFIXES = ["ning", "dan", "ni", "ga", "ka", "qa", "da"]


def numeral_no_plural(s, ctx):
    ms = list(NUM_TA_WORD_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one numeral+ta")
    m = ms[0]
    if m.start() > 0 and s[m.start() - 1] == "-":
        return skip("hyphenated numeral (bitta-bitta, bir-ikkita)")
    if re.search(r"\bhar\s+$", s[:m.start()], re.I):
        return skip("quantifier har + numeral")
    noun = m.group(1)
    low = noun.lower()
    if "lar" in low:
        return skip("noun already contains -lar")
    # bare noun → noun+lar; noun+CASE → noun+lar+CASE (dative after -lar is always -ga)
    forms = [low + "lar"] + [low[:-len(sf)] + "lar" + ("ga" if sf in ("ka", "qa") else sf)
                             for sf in CASE_SUFFIXES if low.endswith(sf) and len(low) - len(sf) >= 2]
    form = next((f for f in forms if ctx.lex[f] >= ctx.min_count), None)
    if form is None:
        return skip("plural form not attested in corpus")
    if ctx.an.upos_of(s, noun) != "NOUN":
        return skip("word after numeral is not NOUN (TurkicNLP)")
    return Edit(s[:m.start(1)] + form + s[m.end(1):], f"{noun} → {form}")


# --------------------------------------------------------------- npi_hech
VOWELS = "aeiou"
NEG_RULES = [  # (negative verb ending, affirmative builder)
    (re.compile(rf"^({L}{{2,}}?)ma(di(?:m|ng|k|ngiz|lar)?)$"), lambda st, r: st + r),  # kelmadi → keldi
    (re.compile(rf"^({L}{{2,}}?)ma(gan{L}*)$"), lambda st, r: st + r),  # kelmagan(dim) → kelgan(dim)
    (re.compile(rf"^({L}{{2,}}?)ma(yapti{L}*)$"), lambda st, r: st + r),  # kelmayapti → kelyapti
    (re.compile(rf"^({L}{{2,}}?)ma(yotgan{L}*)$"), lambda st, r: st + r),  # kelmayotgan → kelyotgan
    (re.compile(rf"^({L}{{2,}}?)may(di|man|san|miz|siz|dilar)$"),  # kelmaydi → keladi, oʻqimaydi → oʻqiydi
     lambda st, r: st + ("y" if st[-1] in VOWELS or st.endswith("oʻ") else "a") + r),
]
TOKEN_RE = re.compile(rf"{L}+")


def _affirmative(word):
    low = word.lower()
    for rule, build in NEG_RULES:
        m = rule.match(low)
        if m:
            aff = build(m.group(1), m.group(2))
            return aff[0].upper() + aff[1:] if word[0].isupper() else aff
    return None


def npi_hech(s, ctx):
    low = s.lower()
    if s.endswith("?"):
        return skip("question (questions license hech)")
    hm = re.search(r"\bhech\b", low)
    if not hm:
        return skip("no hech")
    if re.search(rf"\bhech\s+bo{A}lmasa\b", low):
        return skip("idiom hech boʻlmasa")
    if re.search(rf"\b(?:emas|yo{A}q)\b", low):
        return skip("copula negation (emas/yoʻq)")
    neg = [w for w in TOKEN_RE.finditer(s, hm.end()) if _affirmative(w.group())]
    if not neg:
        return skip("no supported negated verb after hech")
    if len(neg) > 1 or len(NEG_VERB_RE.findall(s)) > 1:
        return skip("more than one negated word")
    w = neg[0]
    aff = _affirmative(w.group())
    if ctx.lex[aff.lower()] < ctx.min_count:
        return skip("affirmative form not attested in corpus")
    if "NEG" not in " ".join(ctx.an.labels(w.group().lower())):
        return skip("TurkicNLP doesn't label NEG")
    return Edit(s[:w.start()] + aff + s[w.end():], f"{w.group()} → {aff}")


# ------------------------------------------------------- postposition_case
POSTP_RE = re.compile(rf"\b({L}{{2,}}?)dan(\s+)(keyin|beri)\b", re.I)
# Dative pronouns are often arguments of the verb, which makes "X-ga keyin" grammatical
# ("unga keyin alam qilmasdi" = it wouldn't hurt him later), so skip them.
DATIVE_PRONOUNS = {"unga", "bunga", "shunga", "menga", "senga", "bizga", "sizga", "ularga", "bularga",
                   "shularga", "hammaga", "oʻshanga", "kimga", "nimaga", "oʻzimga", "oʻzingga", "oʻziga",
                   "oʻzimizga", "oʻzingizga", "oʻzlariga"}


def postposition_case(s, ctx):
    ms = list(POSTP_RE.finditer(s))
    if len(ms) != 1:
        return skip("not exactly one -dan keyin/beri")
    m = ms[0]
    base = m.group(1)
    if base.lower().endswith(("g", "gʻ")):
        return skip("g/gʻ-final stem: dative form unclear (toqqa?)")
    new = base + ("qa" if base.lower().endswith("q") else "ka" if base.lower().endswith("k") else "ga")
    old = base + "dan"
    if new.lower() in DATIVE_PRONOUNS:
        return skip("pronoun: dative reading likely grammatical (unga keyin …)")
    if ctx.lex[new.lower()] < ctx.min_count:
        return skip("dative form not attested in corpus")
    if "ABL" not in ctx.an.labels(old.lower()):
        return skip("TurkicNLP doesn't label ABL")
    return Edit(s[:m.start(1)] + new + s[m.start(2):], f"{old} → {new} ({m.group(3).lower()})")


GENERATORS = {  # phenomenon: (keyword prefilter on lowercased sentence, edit function)
    "numeral_no_plural": (re.compile(rf"\b(?:{NUM_LAT})ta\s"), numeral_no_plural),
    "npi_hech": (re.compile(r"\bhech\b"), npi_hech),
    "postposition_case": (re.compile(r"dan\s+(?:keyin|beri)\b"), postposition_case),
}
KEYWORDS = ("ta ", "hech", "keyin", "beri")


# ------------------------------------------------------------------- scan
def scan(corpus, phenomena, pool_size, seed, limit_docs):
    t0 = time.time()
    lex = Counter()
    pools = {ph: Reservoir(pool_size, f"{seed}-{ph}") for ph in phenomena}
    eligible_n = Counter()
    seen = set()
    skipped = Counter()
    for n_docs, (part, doc, lines) in enumerate(iter_documents(corpus, skipped), 1):
        for ln, line in enumerate(lines, 1):
            low = line.lower()
            lex.update(WORD_RE.findall(low))
            if not any(k in low for k in KEYWORDS):
                continue
            for si, s in enumerate(split_sentences(line)):
                key = s.lower()
                if key in seen or not eligible(s):
                    continue
                for ph in phenomena:
                    if GENERATORS[ph][0].search(key):
                        seen.add(key)
                        eligible_n[ph] += 1
                        pools[ph].add((s, f"{doc}:{ln}:{si}"))
        if limit_docs and n_docs >= limit_docs:
            break
        if n_docs % 20000 == 0:
            print(f"  ... {n_docs:,} documents, {time.time() - t0:.0f}s", flush=True)
    lex = Counter({w: c for w, c in lex.items() if c >= 2})
    meta = {"corpus": str(corpus), "limit_docs": limit_docs, "pool_size": pool_size, "seed": seed,
            "eligible": dict(eligible_n), "scan_seconds": round(time.time() - t0)}
    return lex, {ph: r.items for ph, r in pools.items()}, meta


def load_or_scan(args):
    CACHE.mkdir(parents=True, exist_ok=True)
    meta_path, lex_path, pools_path = CACHE / "scan_meta.json", CACHE / "lexicon.pkl", CACHE / "pools.json"
    want = {"corpus": str(args.corpus), "limit_docs": args.limit_docs, "pool_size": args.pool, "seed": args.seed}
    if not args.rescan and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pools = json.loads(pools_path.read_text(encoding="utf-8"))
        if all(meta.get(k) == v for k, v in want.items()) and all(ph in pools for ph in args.phenomena):
            print(f"Using cached scan ({meta['scan_seconds']}s originally).")
            with open(lex_path, "rb") as f:
                return pickle.load(f), pools, meta
    print("Scanning corpus (lexicon + candidate pools) ...", flush=True)
    lex, pools, meta = scan(args.corpus, args.phenomena, args.pool, args.seed, args.limit_docs)
    with open(lex_path, "wb") as f:
        pickle.dump(lex, f)
    pools_path.write_text(json.dumps(pools, ensure_ascii=False), encoding="utf-8")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return lex, pools, meta


# ------------------------------------------------------------------- main
class Ctx:
    def __init__(self, lex, min_count):
        from tnlp import Analyzer  # loads TurkicNLP only when edits run
        self.lex, self.min_count, self.an = lex, min_count, Analyzer()


def generate(ph, pool, ctx, n, seed):
    rows, reasons, skipped = [], Counter(), []
    items = list(pool)
    random.Random(f"{seed}-{ph}-order").shuffle(items)
    for s, src in items:
        if len(rows) >= n:
            break
        e = GENERATORS[ph][1](s, ctx)
        if e.bad:
            first = ctx.an.upos(s)[:1]
            if first and first[0][1] == "PROPN":  # names at sentence start pass the capitals filter
                e = skip("starts with a proper noun (TurkicNLP)")
        if e.bad:
            row = {"id": f"{ph}-0000", "phenomenon": ph, "grammatical": s, "ungrammatical": e.bad,
                   "method": "corpus-edit", "source_id": src, "status": "unchecked", "notes": e.why}
            errs, _ = check_pair(row)
            if errs:
                e = skip("validator: " + errs[0])
        if e.bad:
            reasons["ok"] += 1
            rows.append(row)
        else:
            reasons[e.why] += 1
            skipped.append((e.why, s, src))
    return rows, reasons, skipped


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", default="D:/drive-download-20260601T072834Z-3-001.zip")
    p.add_argument("--phenomena", nargs="+", default=list(GENERATORS), choices=list(GENERATORS))
    p.add_argument("--n", type=int, default=250, help="pairs to write per phenomenon")
    p.add_argument("--pool", type=int, default=1500, help="sampled sentences per phenomenon")
    p.add_argument("--min-count", type=int, default=2, help="corpus count needed for a new word form")
    p.add_argument("--id-start", type=int, default=1001)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--limit-docs", type=int, help="scan only the first N documents (tests)")
    p.add_argument("--rescan", action="store_true")
    p.add_argument("--out-dir", default=str(ROOT / "data"))
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lex, pools, meta = load_or_scan(args)
    print(f"Lexicon: {len(lex):,} word forms (count ≥ 2). Eligible sentences: {meta['eligible']}")
    ctx = Ctx(lex, args.min_count)
    summary = {"meta": meta, "min_count": args.min_count, "phenomena": {}}
    for ph in args.phenomena:
        rows, reasons, skipped = generate(ph, pools[ph], ctx, args.n, args.seed)
        for k, row in enumerate(rows):
            row["id"] = f"{ph}-{args.id_start + k:04d}"
        out = Path(args.out_dir) / f"pairs_v1_{ph}.tsv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS + OPTIONAL_COLUMNS, delimiter="\t",
                               lineterminator="\n", quoting=csv.QUOTE_NONE, extrasaction="ignore", restval="")
            w.writeheader()
            w.writerows(rows)
        with open(CACHE / f"skips_{ph}.tsv", "w", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="\t", lineterminator="\n").writerows([("reason", "sentence", "source")] + skipped)
        tried = sum(reasons.values())
        summary["phenomena"][ph] = {"pool": len(pools[ph]), "tried": tried, "generated": len(rows),
                                    "reasons": dict(reasons.most_common())}
        print(f"\n{ph}: {len(rows)} pairs → {out.name} (tried {tried} of {len(pools[ph])} sampled)")
        for r, c in reasons.most_common():
            print(f"   {c:5}  {r}")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "make_pairs_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
