import pyarrow.parquet as pq,glob,collections,pickle
from multiprocessing import Pool
from common8 import sents,tok
def work(f):
    c=collections.Counter()
    for t in pq.read_table(f).column("text").to_pylist():
        for s,w in sents(t): c.update(tok(x) for x in w)
    return collections.Counter({k:v for k,v in c.items() if v>=2})
if __name__=="__main__":
    fs=sorted(glob.glob("data/lat-*.parquet"));print(len(fs))
    tot=collections.Counter()
    with Pool(4) as p:
        for c in p.imap_unordered(work,fs): tot.update(c)
    tot={k:v for k,v in tot.items() if v>=3}
    pickle.dump(tot,open("lex8.pkl","wb"));print(len(tot))
