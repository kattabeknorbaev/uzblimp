import re
AP="‘’'`ʼʻ"
def norm(s):
    s=re.sub(r"([OoGg])["+AP+"]",r"\1ʻ",s)          # oʻ gʻ
    s=re.sub(r"(?<=[A-Za-z])["+AP.replace("ʻ","")+r"](?=[a-z])","ʼ",s)  # tutuq belgisi
    return s
OK=re.compile(r"^[A-Za-zʻʼ\-]+$")
def tok(x): return x.strip(".,!?;:“”\"«»()…—–").lower()
def sents(t):
    for s in re.split(r"(?<=[.!?])\s+",t):
        if "-\n" in s or "\n\n" in s: continue
        s=re.sub(r"\s*\n\s*"," ",s).strip()
        w=s.split()
        if not(5<=len(w)<=22) or s[-1] not in ".!?" or not re.match(r"^[A-Z“\"—–«]",s): continue
        if re.search(r"[^\x20-\x7E‘’ʼʻ“”«»…—–]",s): continue   # any non-ASCII lookalike/Cyrillic/ü
        if re.search(r"\d|http|www|[|_=<>{}\[\]@#/\\]|\s[‘’'`ʼʻ]|[‘’'`ʼʻ]\s|[wW]|\b[IVX]{2,}\b",s): continue
        if sum(1 for x in w if x.isupper() and len(x)>1)>0: continue
        s=norm(s);w=s.split()
        if not all(OK.match(x.strip(".,!?;:“”\"«»()…—–")) or x in("—","–") for x in w): continue
        yield s,w
