import pyarrow.parquet as pq,re,collections,json,pickle,glob
from multiprocessing import Pool
from common8 import sents,tok
LEX=None
def f(x): return LEX.get(x,0)
W="[a-zʻʼ]"
NUM=r"(ikki|uch|toʻrt|besh|olti|yetti|sakkiz|toʻqqiz|oʻn|yigirma|oʻttiz|qirq|ellik|oltmish|yetmish|sakson|toʻqson)"
CASE=r"(ga|ka|qa|da|ta|dan|tan|ni|ning|dek|day|cha|gacha|lar|niki)$"
ADJ=r"(iy|viy|ik|al|ion|ar|li|siz|gi|ki|qi|dagi|simon|chi|roq|lik|liq|ma|lama|ali|ont|on|ent|ant|in|ish|ish|gan|kor|parvar|dor)$"
PREF=re.compile(r"[.,!?;:“”\"«»()…—–]+$")
def lar(n):
    p=n[:-1]+"lar" if n.endswith("ll") else n+"lar"
    return p
MEAS=set("ming yuz million milliard kilometr metr santimetr millimetr gramm kilogramm tonna litr soʻm dollar yil oy kun hafta soat daqiqa minut sekund marta marotaba xil bor foiz gektar baravar qadam".split())
def nounish(n):
    return (n not in MEAS and re.fullmatch(W+"{3,}",n) and not re.search(CASE,n) and not re.search(ADJ,n)
            and not re.search(r"(i|si)$",n) and f(n)>=20 and f(lar(n))>=20 and f(lar(n)+"ni")+f(lar(n)+"ga")+f(lar(n)+"da")>=5)
def rep(w,i,new):
    w=list(w);m=PREF.search(w[i]);tail=m.group(0) if m else "";core=w[i][:len(w[i])-len(tail)]
    w[i]=new+tail;return " ".join(w)
def core(x): return PREF.sub("",x).strip("“\"«(")
def gans(stem):
    if stem[-1]=="k": return stem+"kan"
    if stem[-1]=="q": return stem+"qan"
    return stem+"gan"
def dis(stem):
    return stem+("ti" if stem[-1] in "kqptsfxch" and False else "di")
PRON={"men":"1sg","biz":"1pl","sen":"2sg","siz":"2pl"}
END={"1sg":r"(man|dim)$","1pl":r"(miz|dik)$","2sg":r"(san|ding)$","2pl":r"(siz|dingiz)$"}
SWAP={"1sg":[("aman","amiz"),("yman","ymiz"),("dim","dik"),("ganman","ganmiz"),("yapman","yapmiz")],
      "1pl":[("amiz","aman"),("ymiz","yman"),("dik","dim"),("ganmiz","ganman"),("yapmiz","yapman")],
      "2sg":[("asan","aman"),("ysan","yman"),("ding","dim"),("gansan","ganman")],
      "2pl":[("asiz","aman"),("ysiz","yman"),("dingiz","dim"),("gansiz","ganman")]}
def clause_ok(low,a,b):
    return not any(x in ("va","ki","deb","agar","lekin","ammo","chunki","esa","balki") for x in low[a+1:b]) and not any(PREF.search(w_) and "," in w_ for w_ in RAW[a:b])
RAW=[]
def gens(s,w):
    global RAW;RAW=w
    o=[];L=len(w);low=[tok(x) for x in w]
    def add(ph,i,new,note,meth,conf):
        if new==low[i] or new==core(w[i]).lower(): return
        c=core(w[i]); new2=new[0].upper()+new[1:] if c[:1].isupper() else new
        o.append((ph,s,rep(w,i,new2),c,new2,note,meth,conf))
    # numeral / determiners / quantifiers
    for i in range(L-1):
        if re.fullmatch(NUM,low[i]) and nounish(low[i+1]) and core(w[i+1])==w[i+1].rstrip(".,!?;:") and (i+2>=L or not re.search(r"(i|si)$",low[i+2])):
            add("numeral_noun_number",i+1,lar(low[i+1]),"bare noun after numeral -> plural","rule8:NUM+N(lex-noun)+lar","high");break
    for i in range(L-2):
        if low[i]=="har" and low[i+1]=="bir" and nounish(low[i+2]) and (i+3>=L or not re.search(r"(i|si)$",low[i+3])):
            add("determiners",i+2,lar(low[i+2]),"har bir + singular N -> plural","rule8:har_bir+N+lar","medium");break
        if low[i]=="bir" and low[i+1]=="necha" and nounish(low[i+2]) and low[i+2] not in("marta","bor","xil","kun","yil","oy","soat","marotaba","daqiqa","hafta") and (i+3>=L or not re.search(r"(i|si)$",low[i+3])):
            add("quantifiers",i+2,lar(low[i+2]),"bir necha + singular N -> plural","rule8:bir_necha+N+lar","medium");break
    # SVA with overt pronoun subject in same clause
    for i in range(L):
        p=PRON.get(low[i])
        if not p: continue
        for j in range(i+1,min(L,i+8)):
            if "," in w[j-1] or low[j] in("va","ki","deb","agar","lekin","ammo","chunki"): break
            if re.search(END[p],low[j]) and (j==L-1 or w[j][-1] in ".!?"):
                for a,b in SWAP[p]:
                    if low[j].endswith(a) and f(low[j][:-len(a)]+b)>=5:
                        add("subject_verb_agreement",j,low[j][:-len(a)]+b,f"overt {low[i]} subject; verb person/number flipped","rule8:PRON...V-agr -> flipped","high");break
                break
        break
    # anaphor + binding: Men/Biz/Sen/U ... reflexive-ACC ... agreeing V, same clause
    RF={"1sg":"oʻzimni","1pl":"oʻzimizni","2sg":"oʻzingni","2pl":"oʻzingizni"}
    AN={"1sg":"oʻzini","1pl":"oʻzimni","2sg":"oʻzimni","2pl":"oʻzimni"}
    BD={"1sg":"meni","1pl":"bizni","2sg":"seni","2pl":"sizni"}
    for i in range(L):
        p=PRON.get(low[i])
        if not p: continue
        for j in range(i+1,min(L,i+4)):
            if "," in w[j-1]: break
            if low[j]==RF[p]:
                for k in range(j+1,min(L,j+4)):
                    if "," in w[k-1] or low[k] in("va","ki","deb"): break
                    if re.search(END[p],low[k]) and (k==L-1 or w[k][-1] in ".!?"):
                        add("anaphor_agreement",j,AN[p],f"{low[i]} ... reflexive person/number mismatch","rule8:PRON refl-ACC V-agr -> refl wrong person","high")
                        add("binding",j,BD[p],f"{low[i]} ... reflexive -> clause-mate pronoun (Principle B)","rule8:PRON refl-ACC V-agr -> pronoun","high")
                        break
                break
        break
    if low and low[0]=="u" and L>3:
        for j in range(1,4):
            if "," in w[j-1]: break
            if low[j]=="oʻzini":
                for k in range(j+1,min(L,j+4)):
                    if "," in w[k-1]: break
                    if re.search(r"(di|adi|ydi|moqda|yapti)$",low[k]) and not re.search(r"(dim|dik|ding)$",low[k]) and w[k][-1] in ".!?":
                        add("anaphor_agreement",j,"oʻzimni","u ... oʻzini -> oʻzimni (person mismatch)","rule8:U refl3 V3 -> refl1","high");break
                break
    # npi: first verb after hech, no comma
    if "hech" in low:
        h=low.index("hech")
        for i in range(h+1,min(L,h+8)):
            if "," in w[i-1] and i>h+1: break
            x=low[i]
            m=re.fullmatch("("+W+"{2,}?)(ma|may)(di|dim|ding|dik|dingiz|dilar|gan|ganman|ganmiz|man|miz|san|siz|di|dilar)",x) if not x.endswith("may") else None
            if m:
                st=m.group(1);suf=m.group(3)
                cands=[st+suf] if m.group(2)=="ma" else [st+"a"+suf,st+"y"+suf]
                if m.group(2)=="may" and suf in("di","dilar"): cands=[st+"a"+suf,st+"y"+suf]
                if m.group(2)=="may" and suf in("man","miz","san","siz"): cands=[st+"a"+suf,st+"y"+suf]
                cs=[c for c in cands if f(c)>=5]
                if cs: add("npi_licensing",i,cs[0],"hech-NPI: negation removed from first verb after hech","rule8:hech ... first V-ma -> V","high")
                break
            if re.search(r"(di|adi|ydi|gan|moqda|yapti|ib|sa|ish|sh|mas|emas|yoʻq)$",x): break
    # transitive
    TV=r"(koʻr|oʻqi|yoz|top|ich|sot|yop|och|yuv|kiy|tashla|ushla|sev|oʻldir|yasa|sindir|eshit|koʻtar|chiz|tikla|qur)(di|dim|ding|dik|dilar|adi|ydi|aman|yman|yapti|moqda)$"
    for i in range(1,L):
        if re.fullmatch(TV,low[i]) and re.fullmatch(W+"{3,}ni",low[i-1]) and not re.search(r"(gan|yotgan|ligi|lik|ish|sh|ini|si|ini|imni|ingni|mizni)ni$",low[i-1]) and not low[i-1].endswith("ini"):
            st=low[i-1][:-2]; nb=st+("ka" if st[-1]=="k" else "qa" if st[-1]=="q" else "ga")
            if f(nb)>=5: add("argument_structure_transitive",i-1,nb,"acc object of transitive verb -> dat","rule8:N-ni+TV -> N-ga","high")
            break
    # ditransitive
    PM={"menga":"meni","unga":"uni","senga":"seni","sizga":"sizni","bizga":"bizni","ularga":"ularni"}
    GV=r"(ber|uzat|tutqaz|topshir)(di|dim|dik|ding|dilar|adi|aman|amiz|ib|gan)$"
    for i in range(2,L):
        if re.fullmatch(GV,low[i]) and re.fullmatch(W+"{2,}ni",low[i-1]) and not re.search(r"(imkon|imkoniyat|ruxsat|javob|taʼsir|baho|eʼtibor|natija|maʼno|tus|yoʻl|dars|savol|xabar)",low[i-1]):
            for j in range(i-2,max(-1,i-4),-1):
                if "," in w[j]: break
                if low[j] in PM:
                    add("argument_structure_ditransitive",j,PM[low[j]],"pronoun recipient dat -> acc (double acc)","rule8:PRON-ga N-ni V(give) -> PRON-ni","high");break
                if j==i-2 and not re.search(r"(i|si|ligi)ni$",low[i-1]) and re.fullmatch(W+"{3,}(ga|ka|qa)",low[j]) and f(low[j][:-2]+"lar")>=20 and not re.search(r"(xona|joy|uy|shahar|qishloq|yer|tomon|maktab|bozor|ish|oʻrin|vaqt|kun|yil)(ga|ka|qa)$",low[j]) and w[j][0].islower():
                    st=low[j][:-2];nb=st+"ni"
                    if f(nb)>=5: add("argument_structure_ditransitive",j,nb,"N-ga N-ni give -> N-ni N-ni","rule8:N-ga N-ni V(give) tight","medium")
                    break
            break
    # passives
    if "tomonidan" in low:
        i=low.index("tomonidan")
        for j in range(i+1,min(L,i+4)):
            m=re.fullmatch("("+W+"{2,})(il|in|l|n)(gan|di|moqda|adi|ib|ishi|adi)",low[j])
            if m and f(low[j])>=5:
                st=m.group(1);suf=m.group(3)
                if suf=="adi" and st[-1] in "aeiou": suf="ydi"
                nb=st+suf
                if suf=="gan": nb=gans(st)
                if f(nb)>=5 and f(st)>=1: add("passives",j,nb,"tomonidan agent + active verb","rule8:tomonidan+drop_passive","high")
                break
    # irregular
    for i,x in enumerate(low):
        m=re.fullmatch(r"(de|ye)(ydi|yman|ymiz|ysan|ysiz|ydilar)",x)
        if m: add("irregular_forms",i,m.group(1)+"ya"+m.group(2)[1:],"irregular de-/ye- present -> regularized","rule8:de/ye -ydi -> -yadi","medium");break
    # nominalization
    for i in range(L-1):
        x=low[i];nx=low[i+1];m=None
        for suf in("ish","sh"):
            for c in ("","ni","ga"):
                if x.endswith(suf+c) and len(x)>len(suf+c)+1:
                    if (c=="" and nx in("kerak","lozim","mumkin","shart")) or (c=="ni" and re.match("boshla|davom",nx)) or (c=="ga" and re.match("qaror|majbur|tayyor",nx)):
                        st=x[:-len(suf+c)]
                        if suf=="sh" and st[-1] not in "aeiouʻ": continue
                        if suf=="ish" and st[-1] in "aeiou": continue
                        g=gans(st)
                        if f(g)>=5 and f(x)>=5 and (m is None or f(g)>f(m[:-len(c)] if c else m)): m=(g+c)
        if m: add("nominalization",i,m,"-ish/-sh nominal required -> -gan","rule8:V-ish+(kerak|boshla|qaror) -> V-gan (lex-checked)","medium");break
    # relative clauses
    for i in range(1,L-1):
        x=low[i]
        if re.fullmatch(W+"{3,}(gan|kan|qan)",x) and not re.search(r"(digan|yotgan|ayotgan|moqchi)",x) and core(w[i])==w[i] and nounish(low[i+1].rstrip("ni")) if False else (re.fullmatch(W+"{3,}(gan|kan|qan)",x) and not re.search(r"(digan|yotgan|ayotgan)$",x) and core(w[i])==w[i]):
            n=low[i+1]
            nb=n
            for c in ("ning","ni","ga","da","dan",""):
                if n.endswith(c): nb=n[:-len(c)] if c else n;break
            if nb in("bu","shu","u","oʻsha","har","bir","barcha","hamma","ham","biror","hech","eng","juda","yana","bunday","shunday") or n in("bu","shu","oʻsha","har","bir","ham"): continue
            if not(nb and f(nb)>=20 and f(lar(nb))>=20 and not re.search(ADJ,nb)): continue
            st=x[:-3];fin=st+("di" if x.endswith("gan") else "di")
            if f(fin)>=10: add("relative_clauses",i,fin,"participle -gan before head N -> finite -di","rule8:V-gan N -> V-di N (lex-checked)","medium");break
    # suspended affixation
    for i in range(1,L-1):
        if low[i]=="va" and "," not in w[i-1]:
            a,b=low[i-1],low[i+1]
            m=re.fullmatch("("+W+"{3,}?)(lar)?(ni|ga|da|dan|ning)",b)
            if m and nounish(a) and f(m.group(1))>=20 and f(lar(m.group(1)))>=20 and not re.search(ADJ,m.group(1)):
                suf=(m.group(2) or "")+m.group(3)
                if f(a+suf)<5: continue
                bad=" ".join(w[:i-1]+[w[i-1]+suf,"va",w[i+1][:len(m.group(1))]+w[i+1][len(b):]]+w[i+2:])
                o.append(("suspended_affixation",s,bad,f"{a} va {b}",f"{a+suf} va {m.group(1)}","affix moved to first conjunct only","rule8:N1 va N2-SUF -> N1-SUF va N2 (lex nouns)","medium"));break
    # postposition order
    for i in range(1,L):
        pp=low[i]
        if pp in("bilan","uchun","haqida","sari","kabi","orqali") and core(w[i-1])==w[i-1] and re.fullmatch(W+"{3,}",low[i-1]) and w[i-1][0].islower() and f(low[i-1])>=20 and f(lar(low[i-1]))>=20 and not re.search(r"(gan|ish|sh|moq|ib|lik|ligi)$",low[i-1]) and not re.search(ADJ,low[i-1]):
            bad=" ".join(w[:i-1]+[core(w[i]),w[i-1]+w[i][len(core(w[i])):]]+w[i+1:])
            o.append(("postposition_order",s,bad,f"{w[i-1]} {pp}",f"{pp} {w[i-1]}","postposition moved before its complement (head-finality)","rule8:N PostP -> PostP N","medium"));break
    return o
def init():
    global LEX;LEX=pickle.load(open("lex8.pkl","rb"))
def work(fn):
    sh=fn.split("/")[-1].split(".")[0];c=collections.Counter();out=[]
    for i,t in enumerate(pq.read_table(fn).column("text").to_pylist()):
        for s,w in sents(t):
            if any(f(tok(x))<5 for x in w if tok(x)): continue   # OCR/noise: every word must be attested >=5x
            for g in gens(s,w):
                if c[g[0]]<3000: c[g[0]]+=1;out.append(g+(f"tahrirchi/uz-books-v2:{sh}:row{i}",))
    return out
if __name__=="__main__":
    fs=sorted(glob.glob("data/lat-*.parquet"))
    with Pool(4,initializer=init) as p: res=p.map(work,fs)
    with open("cand_v8.jsonl","w") as fo:
        for r in res:
            for g in r: fo.write(json.dumps(g,ensure_ascii=False)+"\n")
    print(len(fs),collections.Counter(g[0] for r in res for g in r))
