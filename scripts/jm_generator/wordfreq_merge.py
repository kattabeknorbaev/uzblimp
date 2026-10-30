import heapq,glob,gzip,sqlite3,os
fs=sorted(glob.glob('cache/wf/lat-*.tsv'));assert len(fs)==26,len(fs)
it=[ (l.rstrip('\n').split('\t') for l in open(f)) for f in fs]
db='cache/wordfreq_lat_full.sqlite'
if os.path.exists(db): os.remove(db)
con=sqlite3.connect(db);con.execute('create table wf(w text primary key, n integer) without rowid')
out=gzip.open('cache/wordfreq_lat_full.tsv.gz','wt');cur=None;n=0;buf=[];types=0;tokens=0
for w,c in heapq.merge(*it,key=lambda x:x[0]):
    c=int(c)
    if w==cur: n+=c;continue
    if cur is not None:
        out.write(f'{cur}\t{n}\n');buf.append((cur,n));types+=1;tokens+=n
        if len(buf)>=200000: con.executemany('insert into wf values(?,?)',buf);buf=[]
    cur,n=w,c
out.write(f'{cur}\t{n}\n');buf.append((cur,n));types+=1;tokens+=n
con.executemany('insert into wf values(?,?)',buf);con.commit();out.close()
print('types',types,'tokens',tokens)
