"""Forced choice with Claude models on the full benchmark, run as Claude Code subagents.

Each model sees every pair of an alphabet twice, once in each order, in requests of 150 pairs. The pairs are
shuffled once with a fixed seed and cut into 16 batches, so every request mixes the phenomena; within a batch,
half of the pairs show the grammatical sentence first in pass A, and pass B reverses every pair. All models,
alphabets and passes use the same batches in the same positions. The prompt (HEADER and render below) repeats
the question of the API pilot (scripts/score_api.py) for many pairs at once and gives no hint about the alphabet.

    python scripts/claude_fc.py plan                      # results/claude_fc/plan_v1.2.json
    python scripts/claude_fc.py workflow MODEL ALPHABET OUT.js [--batches 0,1] [--passes A]
    python scripts/claude_fc.py collect OUTPUT [...]     # per-pair files in results/claude_fc/
    python scripts/claude_fc.py audit TRANSCRIPT_DIR [...]   # served model and tool use of every request
    python scripts/claude_fc.py summary
    python scripts/claude_fc.py readme                    # the table of README.md

MODEL is a Claude Code model alias (fable, opus, sonnet, haiku); ALPHABET is latn, cyrl or latn_reformed. The
workflow script is run with Claude Code's Workflow tool; collect reads the workflow's return value from its output
file (the raw answers are kept in results/claude_fc/raw/), and audit reads the transcripts of its subagents.
"""
import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "claude_fc"
PLAN = OUT / "plan_v1.2.json"
FILES = {"latn": "uzblimp.tsv", "cyrl": "uzblimp_cyrl.tsv", "latn_reformed": "uzblimp_reformed.tsv"}
MODELS = ["fable", "opus", "sonnet", "haiku"]
SEED, N = 2026, 150
EFFORT = "low"  # as the reasoning effort of the API pilot

HEADER = (
    "You judge the grammaticality of Uzbek sentences.\n\n"
    f"Below are {N} numbered items. Each item has two Uzbek sentences, labelled 1 and 2. For each item: which of "
    "the two sentences is grammatically correct? Exactly one of them is.\n\n"
    "Answer from your own knowledge of Uzbek and judge each item on its own. Apart from returning your answers, "
    "do not use any tools: do not read or search files, run code or search the web.\n\n"
    f"Return an answer for every item from 1 to {N}, even when you are unsure: the item number and the number "
    "(1 or 2) of the grammatically correct sentence."
)

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answers"], "properties": {"answers": {
    "type": "array", "minItems": N, "maxItems": N, "items": {
        "type": "object", "additionalProperties": False, "required": ["item", "answer"], "properties": {
            "item": {"type": "integer", "minimum": 1, "maximum": N}, "answer": {"type": "integer", "enum": [1, 2]}}}}}}


def bench(alphabet):
    return pd.read_csv(ROOT / "data" / "benchmark" / FILES[alphabet], sep="\t", dtype=str, keep_default_na=False)


def make_plan():
    ids = list(bench("latn").id)
    rng = random.Random(SEED)
    rng.shuffle(ids)
    assert len(ids) % N == 0
    batches = []
    for start in range(0, len(ids), N):
        first = ["grammatical"] * (N // 2) + ["ungrammatical"] * (N - N // 2)
        rng.shuffle(first)
        batches.append([{"id": i, "first_in_A": f} for i, f in zip(ids[start:start + N], first)])
    return {"benchmark": "v1.2", "seed": SEED, "batch_size": N, "effort": EFFORT, "header": HEADER, "batches": batches}


def load_plan():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["header"] == HEADER, "the prompt changed since the plan was written"
    return plan


def items(plan, alphabet, b):
    """The pairs of batch b as (sentence 1, sentence 2) in pass A."""
    d = bench(alphabet).set_index("id")
    out = []
    for it in plan["batches"][b]:
        g, u = d.at[it["id"], "grammatical"], d.at[it["id"], "ungrammatical"]
        out.append((g, u) if it["first_in_A"] == "grammatical" else (u, g))
    return out


def render(pairs, pass_):
    """The prompt of one request; the JavaScript render() in the workflow script builds the same text."""
    parts = [HEADER]
    for i, (a, b) in enumerate(pairs, 1):
        if pass_ == "B":
            a, b = b, a
        parts.append(f"Item {i}\n1. {a}\n2. {b}")
    return "\n\n".join(parts)


JS = r"""export const meta = {
  name: '__NAME__',
  description: '__DESC__',
  phases: [{ title: 'Judge', detail: 'one request of 150 pairs per batch and order' }],
}
const MODEL = __MODEL__
const ALPHABET = __ALPHABET__
const EFFORT = __EFFORT__
const N = __N__
const HEADER = __HEADER__
const SCHEMA = __SCHEMA__
const BATCHES = __BATCHES__
const JOBS = __JOBS__

function render(pairs, pass) {
  const parts = [HEADER]
  pairs.forEach((p, i) => {
    const [a, b] = pass === 'B' ? [p[1], p[0]] : [p[0], p[1]]
    parts.push(`Item ${i + 1}\n1. ${a}\n2. ${b}`)
  })
  return parts.join('\n\n')
}

function compact(r) {
  if (!r || !Array.isArray(r.answers) || r.answers.length !== N) return null
  const out = new Array(N).fill(0)
  for (const a of r.answers) {
    if (!a || !Number.isInteger(a.item) || a.item < 1 || a.item > N || out[a.item - 1] !== 0) return null
    if (a.answer !== 1 && a.answer !== 2) return null
    out[a.item - 1] = a.answer
  }
  return out.join('')
}

phase('Judge')
const results = await parallel(JOBS.map(([pass, b]) => async () => {
  const prompt = render(BATCHES[String(b)], pass)
  for (let attempt = 1; attempt <= 3; attempt++) {
    const r = await agent(prompt, { label: `${MODEL} ${ALPHABET} ${pass}${b + 1} #${attempt}`, phase: 'Judge',
      model: MODEL, effort: EFFORT, schema: SCHEMA })
    const s = compact(r)
    if (s) return { pass, batch: b, attempts: attempt, chars: prompt.length, answers: s }
  }
  log(`${MODEL} ${ALPHABET} ${pass}${b + 1}: no valid answer after 3 attempts`)
  return { pass, batch: b, attempts: 3, chars: prompt.length, answers: null }
}))
return { model: MODEL, alphabet: ALPHABET, effort: EFFORT, results }
"""


def workflow(model, alphabet, out, batches=None, passes=("A", "B")):
    plan = load_plan()
    batches = list(range(len(plan["batches"]))) if batches is None else batches
    data = {str(b): items(plan, alphabet, b) for b in batches}
    jobs = [[p, b] for p in passes for b in batches]
    js = JS
    for k, v in {"__MODEL__": json.dumps(model), "__ALPHABET__": json.dumps(alphabet), "__EFFORT__": json.dumps(EFFORT),
                 "__N__": str(N), "__HEADER__": json.dumps(HEADER, ensure_ascii=False),
                 "__SCHEMA__": json.dumps(SCHEMA), "__BATCHES__": json.dumps(data, ensure_ascii=False),
                 "__JOBS__": json.dumps(jobs)}.items():
        js = js.replace(k, v)
    part = "" if len(batches) == len(plan["batches"]) else f"-b{batches[0] + 1}-{batches[-1] + 1}"
    js = js.replace("__NAME__", f"uzblimp-fc-{model}-{alphabet}{part}").replace(
        "__DESC__", f"Forced choice on UzBLiMP ({alphabet}{part}, {len(jobs)} requests of {N} pairs) with {model}")
    if len(js.encode("utf-8")) > 524288:
        sys.exit(f"{out}: {len(js.encode('utf-8')):,} bytes, more than a workflow script may have; use --batches")
    Path(out).write_text(js, encoding="utf-8")
    chars = {f"{p}{b}": len(render(data[str(b)], p)) for p, b in jobs}
    print(f"wrote {out}: {len(js):,} characters, {len(jobs)} requests; prompt lengths {min(chars.values()):,}–{max(chars.values()):,}")
    return chars


def read_result(path):
    """The workflow's return value, from its output file (one JSON document) or a journal (JSON lines)."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        docs = [json.loads(text)]
    except json.JSONDecodeError:
        docs = []
        for line in text.splitlines():
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    found, stack = None, docs
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            if {"results", "model", "alphabet"} <= set(x):
                found = x
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)
    if found is None:
        sys.exit(f"no workflow result in {path}")
    return found


def audit(dirs):
    """For every subagent of the given workflow runs: the requested alias, the model that answered and the tools it used."""
    f = OUT / "audit.json"
    rec = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for d in dirs:
        d = Path(d)
        agents = []
        for meta in sorted(d.glob("agent-*.meta.json")):
            m = json.loads(meta.read_text(encoding="utf-8"))
            served, tools = set(), []
            for line in meta.with_name(meta.name.replace(".meta.json", ".jsonl")).read_text(encoding="utf-8").splitlines():
                msg = json.loads(line).get("message") or {}
                if msg.get("model"):
                    served.add(msg["model"])
                for part in msg.get("content") if isinstance(msg.get("content"), list) else []:
                    if part.get("type") == "tool_use":
                        tools.append(part.get("name"))
            agents.append({"label": m.get("description"), "alias": m.get("model"), "served": sorted(served), "tools": tools})
        rec[d.name] = agents
        other = [a for a in agents if set(a["tools"]) - {"StructuredOutput"}]
        print(f"{d.name}: {len(agents)} requests; served {sorted({s for a in agents for s in a['served']})}; "
              f"{len(other)} used another tool")
    f.write_text(json.dumps(rec, indent=1), encoding="utf-8")


def collect(res):
    plan = load_plan()
    model, alphabet = res["model"], res["alphabet"]
    d = bench(alphabet).set_index("id")
    got = {(r["pass"], r["batch"]): r for r in res["results"]}
    rows = []
    for b, batch in enumerate(plan["batches"]):
        pairs = items(plan, alphabet, b)
        for i, it in enumerate(batch):
            row = {"id": it["id"], "phenomenon": d.at[it["id"], "phenomenon"], "good": d.at[it["id"], "grammatical"],
                   "bad": d.at[it["id"], "ungrammatical"], "batch": b + 1, "item": i + 1}
            for p in ("A", "B"):
                r = got.get((p, b))
                if r and r["chars"] != len(render(pairs, p)):
                    sys.exit(f"{model} {alphabet} {p}{b + 1}: the prompt differs from render()")
                ans = int(r["answers"][i]) if r and r["answers"] else None
                good_first = (it["first_in_A"] == "grammatical") == (p == "A")
                order = "gb" if good_first else "bg"
                row[f"answer_{order}"] = ans
                row[f"correct_{order}"] = None if ans is None else ans == (1 if good_first else 2)
                row[f"attempts_{order}"] = r["attempts"] if r else None
            rows.append(row)
    df = pd.DataFrame(rows)
    both = df.correct_gb.notna() & df.correct_bg.notna()
    df["accuracy"] = ((df.correct_gb.eq(True).astype(int) + df.correct_bg.eq(True).astype(int)) / 2).where(both)
    df["consistent"] = (df.correct_gb.eq(True) & df.correct_bg.eq(True)).astype(object).where(both, None)
    df["model"], df["alphabet"], df["effort"] = model, alphabet, res.get("effort", EFFORT)
    df = df.set_index("id").loc[bench(alphabet).id].reset_index()  # benchmark order
    df = df[["id", "phenomenon", "good", "bad", "batch", "item", "answer_gb", "correct_gb", "attempts_gb", "answer_bg",
             "correct_bg", "attempts_bg", "accuracy", "consistent", "model", "alphabet", "effort"]]
    # Written only after every request has been checked, so that a rejected result changes nothing.
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "raw" / f"{model}_{alphabet}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    f = OUT / f"{model}_{alphabet}.csv"
    df.to_csv(f, index=False, encoding="utf-8")
    print(f"{f.name}: {both.sum()} of {len(df)} pairs answered in both orders; accuracy {100 * df.accuracy.mean():.1f}, "
          f"consistent {100 * df.consistent.dropna().astype(bool).mean():.1f}")


def summary():
    rows = []
    for f in sorted(OUT.glob("*_*.csv")):
        df = pd.read_csv(f)
        rows.append((df.model[0], df.alphabet[0], df.accuracy.notna().sum()) + tuple(
            f"{100 * s.mean() + 1e-9:.1f}" for s in (df.accuracy, df.consistent.dropna().astype(bool), df.correct_gb, df.correct_bg)))
    # Halves round up, as in the paper and the README.
    print(pd.DataFrame(rows, columns=["model", "alphabet", "pairs", "accuracy", "consistent", "good first", "bad first"])
          .to_string(index=False))


NAMES = {"fable": "Claude Fable 5.2", "opus": "Claude Opus 5.5", "sonnet": "Claude Sonnet 5.5", "haiku": "Claude Haiku 5.5"}


def readme():
    """The table of README.md between <!-- claude:start --> and <!-- claude:end -->."""
    start, end = "<!-- claude:start -->", "<!-- claude:end -->"
    lines = ["| Model | Current Latin | Cyrillic | Reformed Latin |", "|---|---:|---:|---:|"]
    for m in MODELS:
        cells = []
        for a in FILES:
            df = pd.read_csv(OUT / f"{m}_{a}.csv")
            assert df.accuracy.notna().all()
            cells.append(f"{100 * df.accuracy.mean() + 1e-9:.1f} ({100 * df.consistent.astype(bool).mean() + 1e-9:.1f})")
        lines.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    f = ROOT / "README.md"
    text = f.read_text(encoding="utf-8")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    f.write_text(head + start + "\n" + "\n".join(lines) + "\n" + end + tail, encoding="utf-8", newline="\n")
    print("\n".join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    w = sub.add_parser("workflow")
    w.add_argument("model")
    w.add_argument("alphabet", choices=list(FILES))
    w.add_argument("out")
    w.add_argument("--batches")
    w.add_argument("--passes", default="AB")
    c = sub.add_parser("collect")
    c.add_argument("outputs", nargs="+")
    a = sub.add_parser("audit")
    a.add_argument("dirs", nargs="+")
    sub.add_parser("summary")
    sub.add_parser("readme")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "plan":
        if PLAN.exists():
            sys.exit(f"{PLAN} exists; delete it to draw a new plan")
        OUT.mkdir(parents=True, exist_ok=True)
        PLAN.write_text(json.dumps(make_plan(), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {PLAN}")
    elif args.cmd == "workflow":
        batches = None if not args.batches else [int(x) for x in args.batches.split(",")]
        workflow(args.model, args.alphabet, args.out, batches, tuple(args.passes))
    elif args.cmd == "collect":
        # A run may be split into several workflows (--batches); merge their results by model and alphabet.
        merged = {}
        for o in args.outputs:
            r = read_result(o)
            m = merged.setdefault((r["model"], r["alphabet"]), {**r, "results": []})
            m["results"] += r["results"]
        for r in merged.values():
            keys = [(x["pass"], x["batch"]) for x in r["results"]]
            assert len(keys) == len(set(keys)), f"{r['model']} {r['alphabet']}: a request appears twice"
            r["results"].sort(key=lambda x: (x["pass"], x["batch"]))
            collect(r)
    elif args.cmd == "audit":
        audit(args.dirs)
    elif args.cmd == "readme":
        readme()
    else:
        summary()


if __name__ == "__main__":
    main()
