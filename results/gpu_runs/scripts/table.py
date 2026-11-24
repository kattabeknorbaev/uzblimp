import json,glob,os
rows={}
for f in glob.glob('OUTDIR/repo/results/json/*__logprob.json'):
    d=json.load(open(f))
    if d.get('n_pairs')!=2400 or d['settings'].get('scorer')!='scripts/eval.py' or d['settings'].get('device','').startswith('cpu'): continue
    rows.setdefault(d['model'],{})[d['script']]=d
for m,r in rows.items():
    s=next(iter(r.values()))['settings']
    print(f"{m:45} {s['dtype']:8} L {r.get('latn',{}).get('accuracy','-'):>5}  C {r.get('cyrl',{}).get('accuracy','-'):>5}  R {r.get('latn_reformed',{}).get('accuracy','-'):>5}  wall {s.get('wall_seconds_total')}s")
