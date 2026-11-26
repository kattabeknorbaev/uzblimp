"""Full word-frequency list over ALL Latin shards of tahrirchi/uz-books-v2 (every document, no sentence filter, counts>=1).
Normalisation: o/g + any apostrophe -> ʻ, other in-word apostrophes -> ʼ, lowercase, tokens = [a-zʻʼ]+ (hyphen splits).
Out: cache/wf/lat-XXXXX.tsv per shard, then cache/wordfreq_lat_full.tsv.gz (word<TAB>count, sorted by word) and cache/wordfreq_lat_full.sqlite."""
import pyarrow.parquet as pq,glob,collections,re,os,sys
from multiprocessing import Pool
AP="‘’'`ʼʻ"
R1=re.compile(r"([OoGg])["+AP+"]");R2=re.compile(r"(?<=[A-Za-z])["+AP.replace("ʻ","")+r"](?=[A-Za-z])")
TOK=re.compile(r"[a-zʻʼ]+")
def work(f):
    out=f"cache/wf/{os.path.basename(f).split('-of')[0]}.tsv"
    if os.path.exists(out): return out
    c=collections.Counter();pf=pq.ParquetFile(f)
    for b in pf.iter_batches(batch_size=50,columns=["text"]):
        for t in b.column(0).to_pylist():
            t=R2.sub("ʼ",R1.sub(r"\1ʻ",t)).lower()
            c.update(TOK.findall(t))
    with open(out+".tmp","w") as fh:
        for k in sorted(c): fh.write(f"{k}\t{c[k]}\n")
    os.rename(out+".tmp",out);return out
if __name__=="__main__":
    fs=sorted(glob.glob("data/lat-*.parquet"))
    with Pool(int(sys.argv[1]) if len(sys.argv)>1 else 3) as p:
        for o in p.imap_unordered(work,fs): print(o,flush=True)
