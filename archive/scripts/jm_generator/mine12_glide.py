"""Mine new vowel_glide_y seeds for v12: vowel-stem verb + glide y + 1st/2nd person suffix (-yman/-ymiz/-ysiz/-ysan)
from ALL Latin shards. Same sentence filter as mine8 (common8.sents; every word attested >=5x in lex8).
Out: cand_v12_glide.jsonl (good sentence, word index, word, stem, suffix, source). Filtering happens in build12.py."""
import pyarrow.parquet as pq,re,collections,json,pickle,glob
from multiprocessing import Pool
from common8 import sents,tok
RX=re.compile(r"([a-zʻʼ]{2,}[aeiou])y(man|miz|siz|san)")
def init():
    global LEX;LEX=pickle.load(open("lex8.pkl","rb"))
def work(fn):
    sh=fn.split("/")[-1].split(".")[0];out=[]
    for i,t in enumerate(pq.read_table(fn).column("text").to_pylist()):
        for s,w in sents(t):
            if any(LEX.get(tok(x),0)<5 for x in w if tok(x)): continue
            for k,x in enumerate(w):
                m=RX.fullmatch(tok(x))
                if m: out.append(dict(good=s,i=k,word=x,stem=m.group(1),suf=m.group(2),source=f"tahrirchi/uz-books-v2:{sh}:row{i}"))
    return out
if __name__=="__main__":
    fs=sorted(glob.glob("data/lat-*.parquet"))
    with Pool(3,initializer=init) as p: res=p.map(work,fs)
    n=0
    with open("cand_v12_glide.jsonl","w") as fo:
        for r in res:
            for g in r: fo.write(json.dumps(g,ensure_ascii=False)+"\n");n+=1
    print(n,collections.Counter(g['suf'] for r in res for g in r))
