import sys,os,re; sys.path.insert(0,'.')
from attrib import hash64
T={int(h,16) for h in sys.argv[2:]}
seen=set(); found={}
for root,_,fs in os.walk(sys.argv[1]):
  for f in fs:
    p=os.path.join(root,f)
    if os.path.getsize(p)>60_000_000: continue
    d=open(p,'rb').read()
    for s in set(re.findall(rb'[A-Za-z_][A-Za-z0-9_]{2,60}',d)):
      if s in seen: continue
      seen.add(s); t=s.decode()
      for v in (t,t.lower()):
        h=hash64(v)
        if h in T and h not in found: found[h]=v; print('%016x %s   (%s)'%(h,v,p),flush=True)
print('strings',len(seen),'found',len(found))
