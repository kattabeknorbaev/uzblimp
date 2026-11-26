"""UzBLiMP v12 = v11 with vowel_glide_y rebuilt (v11 is not modified).
v11 rule9 made bad forms by y->a (qilmaydi->*qilmaadi): the 'aa' hiatus is trivially rejectable.
v12 rule12: drop the glide y (qutlayman->*qutlaman). A pair is kept only if
  (1) the bad word has 0 hits in the full Latin uz-books-v2 word list (26 shards, 1.47B tokens; wf.py),
  (2) it has no known inflected reading (conservative):
      -di/-dilar -> real past tense (qilmadi, ushladi); -san -> conditional/colloquial (yashasan);
      negative -ma- stems -> dialectal/colloquial -maman/-mamiz/-masiz; nominal stem -> copula/possessive (N-man, N-miz),
  (3) good word is frequent (>=20) and its stem is a verb (stem+sh / stem+moq attested).
Replacements are mined from all Latin shards (mine12_glide.py -> cand_v12_glide.jsonl)."""
import pandas as pd,json,re,collections,random,pickle
from wf import F
from common8 import tok
LEX=pickle.load(open('lex8.pkl','rb'));f=lambda x:LEX.get(x,0)
RX=re.compile(r"([a-zʻʼ]{2,}[aeiou])y(di|dilar|man|miz|siz|san)")
def ocr(s):
    for x in s.split():
        t=tok(x)
        if len(t)<3: continue
        for a,b in (("u","oʻ"),("o","oʻ"),("x","h"),("h","x"),("i","y")):
            for k in range(len(t)):
                if t[k]==a:
                    alt=t[:k]+b+t[k+1:]
                    if f(alt)>=20*max(f(t),1) and f(alt)>=200: return True
    return False
def split_ocr(s):
    w=[tok(x) for x in s.split()]
    if re.search(r"[a-zʻʼ][A-Z]",s): return True
    FR={"lib","ladi","lar","gan","dan","ning","ga","dir","lik","ib","adi","moq","dek","di"}
    if any(x in FR for x in w[1:]): return True
    for a,b in zip(w,w[1:]):
        if a and b and f(a+b)>=50 and f(a+b)>min(f(a),f(b)): return True
    return False
ALPH="abdefghijklmnopqrstuvxyzʻʼ"
def typo1(s):
    """a word looks like a scan/typing error if a 1-edit variant (substitution, ʼ/ʻ insertion, deletion) is >=50x more
    frequent and >=100 hits (catches tariflaymiz->taʼriflaymiz, takidlaymiz, lskin->lekin-type noise)."""
    for x in s.split():
        t=tok(x);ft=f(t)
        if len(t)<3 or ft>=300 or not re.fullmatch(r"[a-zʻʼ]+",t): continue
        th=max(30*max(ft,1),100)
        for k in range(len(t)+1):
            for c in ("ʼ","ʻ"):
                if f(t[:k]+c+t[k:])>=th: return x
            if k<len(t):
                if f(t[:k]+t[k+1:])>=th: return x
                for c in ALPH:
                    if c!=t[k] and f(t[:k]+c+t[k+1:])>=th: return x
    return None
def judge(word):
    """returns (bad_word, None) or (None, reason)"""
    t=tok(word);m=RX.fullmatch(t)
    if not m: return None,'cue does not match V-stem+y+suffix'
    st,suf=m.groups();bad=st+suf
    if suf in('di','dilar'): return None,'y-drop gives real past tense -di/-dilar (3rd person -aydi/-aydilar)'
    if suf=='san': return None,'y-drop gives -san: conditional/colloquial reading (yashasan)'
    if st.endswith('ma'): return None,'negative -ma- stem: -maman/-mamiz/-masiz is dialectal/colloquial or verbal noun -ma+POSS'
    if F(bad)>0: return None,'bad form attested in full corpus (>=1 hit)'
    if F(st+'ni')+F(st+'ning')+F(st+'lar')+F(st+'ga')>=5: return None,'stem also nominal: copula/possessive reading (N-man/N-miz/N-siz)'
    if F(t)<20: return None,'good form rare (<20 hits) / likely typo'
    if F(st+'sh')+F(st+'moq')<5: return None,'stem not attested as verb (stem+sh/stem+moq <5)'
    return bad,None
def apply(sent,i,bad):
    w=sent.split();x=w[i];t=tok(x);core_start=x.lower().find(t)
    core=x[core_start:core_start+len(t)]
    nb=bad[0].upper()+bad[1:] if core[0].isupper() else bad
    w[i]=x[:core_start]+nb+x[core_start+len(t):];return ' '.join(w),core,nb
v=pd.read_csv('uzblimp_v11.tsv',sep='\t',dtype=str,keep_default_na=False)
cols=list(v.columns)
NOTE='present-future glide -y- dropped after vowel stem -> unattested *V-stem+PERS (subtle, no hiatus)'
METH='rule12:V-stem+y+PERS -> *V-stem+PERS (glide dropped; 0 hits in full uz-books-v2 Latin, 1.47B tokens; no -di/-san/-ma/nominal reading)'
g=v[v.phenomenon=='vowel_glide_y'];rej=collections.Counter();keep=[];rejrows=[]
for _,r in g.iterrows():
    gw=r.good.split();bw=r.bad.split()
    idx=[k for k,(a,b) in enumerate(zip(gw,bw)) if a!=b]
    bad,why=judge(gw[idx[0]]) if len(idx)==1 else (None,'pair not single-word')
    if why:
        nbw=RX.sub(r'\1\2',tok(r.good_cue));rej[why]+=1
        rejrows.append(dict(id=r.id,good_cue=r.good_cue,v11_bad=r.bad_cue,new_bad=nbw,reason=why,corpus_hits=F(nbw)));continue
    nbsent,core,nb=apply(r.good,idx[0],bad)
    d=r.to_dict();d.update(bad=nbsent,bad_cue=nb,notes=NOTE+f' (v11 bad was {r.bad_cue})',method=METH,confidence='high',batch='v12_from_v11')
    keep.append(d)
print('v11 vowel_glide_y survived:',len(keep),'rejected:',sum(rej.values()));print(rej)
used=set(v.good);bk=collections.Counter(d['source'] for d in keep);cue=collections.Counter(tok(d['good_cue']) for d in keep);stemc=collections.Counter()
cands=[json.loads(l) for l in open('cand_v12_glide.jsonl')]
random.Random(12).shuffle(cands)
mrej=collections.Counter();pool=collections.defaultdict(list)
for c in cands:
    s=c['good']
    if s in used: mrej['sentence already in v11']+=1;continue
    bad,why=judge(c['word'])
    if why: mrej[why]+=1;continue
    x=c['word'];t=tok(x)
    if not re.fullmatch(r"[A-Za-zʻʼ]+",x[x.lower().find(t):x.lower().find(t)+len(t)]): mrej['odd token']+=1;continue
    if ocr(s) or split_ocr(s): mrej['OCR/split-word sentence']+=1;continue
    if sum(tok(y)==t for y in s.split())>1: mrej['cue word repeated in sentence']+=1;continue
    if c['i']>0 and x[0].isupper(): mrej['cue capitalised mid-sentence']+=1;continue
    if len(t)>16: mrej['cue >16 chars (likely fused OCR word)']+=1;continue
    if any(f(tok(y))<20 for y in s.split() if tok(y)): mrej['sentence has a word with <20 corpus hits (noise/rare spelling)']+=1;continue
    if typo1(s): mrej['sentence has a likely typo/scan error (1-edit variant >=30x more frequent)']+=1;continue
    pool[c['suf']].append((c,bad))
print('mined candidate rejections:',dict(mrej));print('clean mined candidates by suffix:',{k:len(x) for k,x in pool.items()})
new=[];order=sorted(pool,key=lambda k:len(pool[k]));need=300-len(keep);ptr={k:0 for k in pool}
while len(new)<need and any(ptr[k]<len(pool[k]) for k in pool):
    for k in order:
        while ptr[k]<len(pool[k]):
            c,bad=pool[k][ptr[k]];ptr[k]+=1;t=tok(c['word']);st=t[:-len(k)-1]
            if c['good'] in used or bk[c['source']]>=1 or cue[t]>=3 or stemc[st]>=5: continue
            nbsent,core,nb=apply(c['good'],c['i'],bad)
            used.add(c['good']);bk[c['source']]+=1;cue[t]+=1;stemc[st]+=1
            new.append(dict(phenomenon='vowel_glide_y',good=c['good'],bad=nbsent,good_cue=core,bad_cue=nb,source=c['source'],batch='v12_hf',notes=NOTE,method=METH,confidence='high',review_flag=''));break
        if len(new)>=need: break
for n,d in enumerate(new,1): d['id']=f'v12_vowel_glide_y_{n:04d}'
G=pd.DataFrame(keep+new)[cols]
v12=pd.concat([v[v.phenomenon!='vowel_glide_y'],G]).reset_index(drop=True)
v12.to_csv('uzblimp_v12.tsv',sep='\t',index=False)
v12.to_csv('uzblimp_v12.csv',index=False,encoding='utf-8-sig')
v12.to_json('uzblimp_v12.json',orient='records',force_ascii=False,indent=1)
pd.DataFrame(rejrows).to_csv('vowel_glide_y_v11_rejections.tsv',sep='\t',index=False)
t=pd.crosstab(v12.phenomenon,v12.confidence);t['total']=v12.phenomenon.value_counts();t.loc['TOTAL']=t.sum();t.to_csv('uzblimp_v12_counts.tsv',sep='\t')
print('v12 vowel_glide_y:',len(G),'=',len(keep),'from v11 +',len(new),'new; suffixes:',collections.Counter(RX.fullmatch(tok(x)).group(2) for x in G.good_cue))
json.dump(dict(v11_survived=len(keep),v11_rejected=dict(rej),new=len(new),mined_rejections=dict(mrej),clean_pool={k:len(x) for k,x in pool.items()}),open('vowel_glide_y_v12_stats.json','w'),ensure_ascii=False,indent=1)
print(t.to_string())
