"""LOCAL helper (not pushed): score one HF causal LM on all three alphabets with ONE model load,
using eval.py's own scorer (run_logprob) and writers. Same outputs as running eval.py three times."""
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import eval as ev
from schema import RELEASE_PHENOMENA

p = argparse.ArgumentParser()
p.add_argument("--model", required=True); p.add_argument("--label")
p.add_argument("--dtype", default="float32"); p.add_argument("--batch-size", type=int, default=32)
p.add_argument("--device", default="cuda"); p.add_argument("--per-phenomenon", type=int)
p.add_argument("--out", default=str(ev.ROOT / "results"))
p.add_argument("--scripts", nargs="*", default=["latn", "cyrl", "latn_reformed"])
a = p.parse_args()
a.no_start_token = False
t0 = time.time()
pairs = []
for s in a.scripts:
    ps = ev.load_pairs(str(ev.ROOT / "data" / "jsonl"), s, a.per_phenomenon)
    for q in ps: q["_script"] = s
    pairs += ps
assert not ({q["paradigm"] for q in pairs} - set(RELEASE_PHENOMENA))
rows, settings = ev.run_logprob(pairs, a.model, a)
settings["wall_seconds_total"] = round(time.time() - t0)
for s in a.scripts:
    sub = [r for r, q in zip(rows, pairs) if q["_script"] == s]
    ev.write_results(ev.summarize(sub, a.model, s, "logprob", settings, a.label), sub, Path(a.out))
print(f"DONE {a.model} in {time.time()-t0:.0f}s", flush=True)
