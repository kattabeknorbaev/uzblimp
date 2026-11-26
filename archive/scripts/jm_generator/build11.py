import pandas as pd,json,collections,random,re,pickle
from common8 import tok
LEX=pickle.load(open('lex8.pkl','rb'));f=lambda x:LEX.get(x,0)
V="aeiouʻ"
def verb(st): return f(st+"moq")+f(st+"ish" if st[-1] not in V else st+"sh")>=5
def gans(st): return st+("kan" if st[-1]=="k" else "qan" if st[-1]=="q" else "gan")
def ocr(s):
    for x in s.split():
        t=tok(x)
        if len(t)<3: continue
        for a,b in (("u","oʻ"),("o","oʻ"),("x","h"),("h","x"),("i","y")):
            if a in t:
                for k in range(len(t)):
                    if t[k]==a:
                        alt=t[:k]+b+t[k+1:]
                        if f(alt)>=20*max(f(t),1) and f(alt)>=200: return True
    return False
def passive_fix(gc,bc):
    c=gc.lower().strip(".,!?;:")
    for suf in ("gan","di","moqda","adi","ib","ishi"):
        if not c.endswith(suf): continue
        base=c[:-len(suf)]
        for pas in ("il","in","l","n"):
            if not base.endswith(pas): continue
            st=base[:-len(pas)]
            if len(st)<2 or st in("qi","bi","ki","ke","ko","ye","de","so"): continue
            ok={"il":st[-1] not in V and st[-1]!="l","in":st[-1]=="l","l":st[-1] in V,"n":st[-1] in V}[pas]
            if not ok or not verb(st): continue
            if suf=="gan": nb=gans(st)
            elif suf=="adi": nb=st+("ydi" if st[-1] in V else "adi")
            elif suf=="ishi": nb=st+("shi" if st[-1] in V else "ishi")
            else: nb=st+suf
            if f(nb)>=20: return nb
    return None
def nom_fix(gc):
    c=gc.lower()
    for case in ("ni","ga",""):
        if case and not c.endswith(case): continue
        b=c[:-len(case)] if case else c
        for suf in ("ish","sh"):
            if not b.endswith(suf): continue
            st=b[:-len(suf)]
            if len(st)<2 or (suf=="ish")==(st[-1] in V): continue
            if verb(st) and f(gans(st))>=20: return gans(st)+case
    return None
C=collections.defaultdict(list);log=collections.Counter()
NUMW=set("bir ikki uch toʻrt besh olti yetti sakkiz toʻqqiz oʻn yigirma oʻttiz qirq ellik oltmish yetmish sakson toʻqson yuz ming".split())
def split_ocr(s):
    w=[tok(x) for x in s.split()]
    if re.search(r"[a-zʻʼ][A-Z]",s): return True
    FR={"lib","ladi","lar","gan","dan","ning","ga","dir","lik","ib","adi","moq","dek","di"}
    if any(x in FR for x in w[1:]): return True
    for a,b in zip(w,w[1:]):
        if a and b and f(a+b)>=50 and f(a+b)>min(f(a),f(b)): return True
    return False
def nxt(g):
    w=g[1].split();i=[k for k,x in enumerate(w) if x.strip("(.,!?;:“”«»")==g[3].strip("(.,!?;:“”«»")]
    return w[i[0]+1].lower() if i and i[0]+1<len(w) else "" ,(w[i[0]-1].lower() if i and i[0]>0 else "")
for l in open('cand_v8.jsonl'):
    g=json.loads(l);p=g[0]
    if p=='passives':
        nb=passive_fix(g[3],g[4])
        if not nb: log['passives: dropped (no clean active form)']+=1;continue
        if nb!=g[4].lower().strip(".,!?"): log['passives: bad form regenerated']+=1
        g[2]=g[1].replace(g[3],nb,1) if g[3] in g[1] else g[2];g[4]=nb
    if p=='nominalization':
        nb=nom_fix(g[3])
        if not nb: log['nominalization: dropped (stem cut)']+=1;continue
        if nb!=g[4]: log['nominalization: bad form regenerated']+=1
        g[2]=g[1].replace(g[3],nb,1);g[4]=nb
    if p=='quantifiers':
        pass
    if p=='quantifiers':
        n=g[3].lower()
        if re.search(r"(sa|ssa|da|ma)$",n) or f(n+"lar")<50 or n in("hissa","boʻlsa","emas","edi","ekan"): log['quantifiers: dropped non-noun']+=1;continue
        g[7]='low';g[5]+=' EXPLORATORY: bir necha + N-lar is borderline; hold out of headline scores'
    if p=='argument_structure_ditransitive' and g[7]!='high': log['ditransitive: noun-recipient dropped']+=1;continue
    if p=='relative_clauses':
        w=g[1].split();i=[k for k,x in enumerate(w) if x.strip(".,!?")==g[3]]
        if i and i[0]+1<len(w) and re.match(r"(edi|ekan|emish|edim|edik|eding|edingiz|edilar)",w[i[0]+1].lower()): log['relative_clauses: -gan edi dropped']+=1;continue
    nx,pv=nxt(g)
    if p=='relative_clauses' and re.match(r"(holda|holatda|sari|sayin|kabi|uchun|bilan|keyin|soʻng|beri|zahoti|hamon|chogʻda|paytda|vaqtda|taqdirda|darajada|qadar|sababli|tufayli|uchun|singari|yangligʻ|dek|day)[.,!?]?$",nx): log['v11 relative_clauses: V-gan + adverbial postposition dropped']+=1;continue
    if p=='relative_clauses' and re.match(r"(boʻl|edi|ekan|emish|ed)",nx): log['v10 relative_clauses: -gan boʻl-/edi dropped']+=1;continue
    if p=='numeral_noun_number':
        c=g[3].lower().strip(".,!?")
        if c in NUMW or pv.strip(".,")=="ellik" or c in("tur","xil","baho","barmoq","parallel","qator","xona","qavat","karra","hissa","ball","pog‘ona","bosqich","dona","marta","pul","oʻz","yot","buyuk","ellik","chet","boʻlsa","dona","yarim","nafar","juft","tup","bosh") or c.endswith("sa") or f(c+"roq")>=5 or (nx.strip(".,") in NUMW) or pv.strip(".,")=="chet":
            log['v10 numeral: numeral/adjective/idiom dropped']+=1;continue
    if p=='numeral_noun_number' and re.search(r"(ichak|baho)",g[1].split(g[3])[1][:12] if g[3] in g[1] else ""): log['v11 numeral: idiom dropped']+=1;continue
    if p=='determiners' and (g[3].lower() in NUMW or re.search(r"\bhar bir (bir|"+"|".join(NUMW)+r")\b",g[1].lower())): log['v11 determiners: numeral cue dropped']+=1;continue
    if p=='quantifiers' and (g[3].lower() in NUMW or f(g[3].lower()+"roq")>=5): log['v10 quantifiers: numeral/adjective dropped']+=1;continue
    if split_ocr(g[1]): log['v10 split-word / mixed-case scan error dropped']+=1;continue
    g[3]=g[3].strip("(“”«»\"");g[4]=g[4].strip("(“”«»\"")
    if not re.fullmatch(r"[A-Za-zʻʼ\- ]+",g[3]) or not re.fullmatch(r"[A-Za-zʻʼ\- ]+",g[4]): log['v10 truncated/odd cue dropped']+=1;continue
    if p=='irregular_forms': log['irregular_forms: de-/ye- dialectal pairs dropped']+=1;continue
    if p=='binding':
        w=g[2].split()
        g[2]=" ".join([x if k==0 or w[k-1][-1] in ".!?" or not re.match(r"(Bizni|Meni|Seni|Sizni|Bizga|Menga)",x) else x[0].lower()+x[1:] for k,x in enumerate(w)]);g[4]=g[4].lower() if g[4] in("Bizni","Meni","Seni","Sizni") and not g[2].startswith(g[4]) else g[4]
    if g[2]==g[1]: continue
    if ocr(g[1]): log['scan-error (OCR) sentence dropped']+=1;continue
    C[p].append(g)
# new irregular_forms: vowel-stem present -ydi glide -> *-adi hiatus (clearly ungrammatical)
seen=set()
for p,L in list(C.items()):
    for g in L:
        s=g[1]
        if s in seen: continue
        seen.add(s);w=s.split()
        for i,x in enumerate(w):
            t=tok(x);m=re.fullmatch(r"([a-zʻʼ]{2,}[aeiou])(ydi|yman|ymiz|ysan|ysiz|ydilar)",t)
            if m and not t.startswith(("de","ye")) and verb(m.group(1)) and f(t)>=20 and f(m.group(1)+"a"+m.group(2)[1:])==0:
                nb=m.group(1)+"a"+m.group(2)[1:]
                core=x[:len(t)];nb2=nb[0].upper()+nb[1:] if core[0].isupper() else nb
                bad=" ".join(w[:i]+[nb2+x[len(t):]]+w[i+1:])
                if ocr(s) or split_ocr(s) or not re.fullmatch(r'[A-Za-zʻʼ]+',core): break
                C['vowel_glide_y'].append(['vowel_glide_y',s,bad,core,nb2,'present -y- glide after vowel stem -> unattested *-a- (hiatus)','rule9:V-stem+ydi -> *V-stem+adi (0 corpus hits)','high',g[8]]);break
print(log);print({p:len(L) for p,L in C.items()})
v8=pd.read_csv('uzblimp_v8.tsv',sep='\t',dtype=str,keep_default_na=False,quoting=3)
o=v8[v8.batch=='__none__']  # v10: 7 legacy rows without shard refs dropped
rows=[];used=set(o.good)
for p,L in C.items():
    random.Random(9).shuffle(L);L.sort(key=lambda g:{'high':0,'medium':1,'low':2}[g[7]])
    cue=collections.Counter();bk=collections.Counter();n=(o.phenomenon==p).sum()
    cap=100 if p in('argument_structure_ditransitive','binding','anaphor_agreement','npi_licensing') else 3
    for ph,good,bad,gc,bc,note,meth,conf,src in L:
        if n>=300: break
        kk=gc.lower()
        if good in used or good==bad or cue[kk]>=cap or bk[src]>=1: continue
        if p=='passives' and (re.match(r'(boʻl|bul|kel|qol|bil|sol|toʻl|yon|kon|tal|chal|yul)',kk)): continue
        cue[kk]+=1;bk[src]+=1;used.add(good);n+=1
        rows.append(dict(id=f"v11_{p}_{n:04d}",phenomenon=p,good=good,bad=bad,good_cue=gc,bad_cue=bc,source=src,batch='v11_hf',notes=note,method=meth,confidence=conf,review_flag=''))
cols=list(v8.columns)
v=pd.concat([o[cols],pd.DataFrame(rows)[cols]]).reset_index(drop=True)
v['id']=v.id.str.replace('v10_','v11_');v.to_csv('uzblimp_v11.tsv',sep='\t',index=False)
t=pd.crosstab(v.phenomenon,v.confidence);t['available_after_filters']=pd.Series({p:len(L) for p,L in C.items()});t=t.fillna(0).astype(int);t['total']=v.phenomenon.value_counts();t.loc['TOTAL']=t.sum()
t.to_csv('uzblimp_v11_counts.tsv',sep='\t');print(t.to_string())
with pd.ExcelWriter('uzblimp_v11_review.xlsx') as x:
    v.assign(keep='').to_excel(x,sheet_name='all_pairs',index=False);t.to_excel(x,sheet_name='counts')
    pd.DataFrame(list(log.items()),columns=['change','candidates']).to_excel(x,sheet_name='changes',index=False)
    for p,g in v.groupby('phenomenon'): g.assign(keep='').to_excel(x,sheet_name=p[:31],index=False)
