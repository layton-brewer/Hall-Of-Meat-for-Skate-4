"""Decode a Skate 3 attrib class: definitions + every collection's layout and entries.
s3cls.py <class> [names...]"""
import sys,struct,re,glob,os
sys.path.insert(0,'D:/dev/tools')
from attrib import hash64
DB='D:/dev/skate3-ref/ex/db/data/db/'
sv=open(DB+'skaterschema.vlt','rb').read(); sb=open(DB+'skaterschema.bin','rb').read()
cv=open(DB+'skatercollections.vlt','rb').read(); cb=open(DB+'skatercollections.bin','rb').read()
names={}
def add(s):
    for part in {s,s.lower()}: names[hash64(part)]=part
for line in open(DB+'skatercollections_summaryreport.txt',errors='ignore'):
    for t in re.findall(r'[A-Za-z_][A-Za-z0-9_]*',line): add(t)
extra='D:/dev/ogcam/fieldnames.txt'
if os.path.exists(extra):
    for t in open(extra).read().split(): add(t)
for t in ['EA::Reflection::Float','EA::Reflection::Bool','EA::Reflection::Int32','EA::Reflection::UInt32','EA::Reflection::UInt8','EA::Reflection::Int8','EA::Reflection::Text','Math::Vector3','Math::Vector4','Math::Vector2','Attrib::RefSpec','Attrib::Types::Matrix','EA::Reflection::Int16','EA::Reflection::UInt16','Attrib::StringKey','Attrib::Graph','GraphFloat','Attrib::Types::GraphFloat']: add(t)
def nm(h): return names.get(h,'%016x'%h)
def ptrs(v):
    p=v.index(b'PtrN'); n=struct.unpack('>I',v[p+4:p+8])[0]; d={}
    for q in range(p+8,p+n-15,16):
        at,t,fl,dest=struct.unpack('>IHHQ',v[q:q+16]); d[at]=(t,dest)
    return d
sp=ptrs(sv); cp=ptrs(cv)
cls=sys.argv[1]; ck=hash64(cls); kb=struct.pack('>Q',ck)
# class record in schema DatN
d=sv.index(b'DatN'); rec=None
for o in range(d+8, d+struct.unpack('>I',sv[d+4:d+8])[0]-40, 4):
    if sv[o:o+8]==kb and (o+0x10) in sp: rec=o; break
ncol,ndef=struct.unpack('>II',sv[rec+8:rec+16]); lsize=struct.unpack(">I",sv[rec+0x1c:rec+0x20])[0]
dp=sp[rec+0x10][1]
defs=[]
for i in range(ndef):
    k,t,off,sz,mx,fl,al=struct.unpack('>QQHHHBB',sb[dp+24*i:dp+24*i+24]); defs.append((k,t,off,sz,mx,fl,al))
print('class',cls,'collections',ncol,'defs',ndef,'layout',lsize)
for k,t,off,sz,mx,fl,al in sorted(defs,key=lambda x:(x[5]&2==0,x[2])):
    print('  def %-30s %-28s off %4d size %3d max %d flags %02x'%(nm(k),nm(t),off,sz,mx,fl))
deft={k:(t,off,sz,mx,fl) for k,t,off,sz,mx,fl,al in defs}
def fmt(t,b):
    tn=nm(t)
    if 'Float' in tn and len(b)>=4 and 'Graph' not in tn: return ' '.join('%g'%x for x in struct.unpack('>%df'%(len(b)//4),b[:len(b)//4*4]))
    if 'Vector' in tn: return ' '.join('%g'%x for x in struct.unpack('>%df'%(len(b)//4),b))
    if 'Bool' in tn or 'UInt8' in tn or 'Int8' in tn: return ' '.join(str(x) for x in b)
    if 'Int32' in tn or 'UInt32' in tn: return ' '.join(str(x) for x in struct.unpack('>%di'%(len(b)//4),b))
    words=struct.unpack('>%dI'%(len(b)//4),b[:len(b)//4*4])
    return ' '.join(('%g'%struct.unpack('>f',struct.pack('>I',w))[0]) if 0x30000000<(w&0x7fffffff)<0x50000000 or w==0 else '%08x'%w for w in words)
d=cv.index(b'DatN'); dend=d+struct.unpack('>I',cv[d+4:d+8])[0]
want={hash64(x) for x in sys.argv[2:]}
for o in range(d+8,dend-0x30,4):
    key,klass,parent=struct.unpack('>QQQ',cv[o:o+24])
    if klass!=ck: continue
    if want and key not in want: continue
    reserve,_,count,ntypes,tlen=struct.unpack('>IIIHH',cv[o+24:o+40])
    if count>400 or ntypes>64: continue
    types=struct.unpack('>%dQ'%ntypes,cv[o+48:o+48+8*ntypes])
    print('== %s (parent %s) entries %d'%(nm(key),nm(parent) if parent else '-',count))
    if (o+40) in cp:
        lp=cp[o+40][1]; L=cb[lp:lp+lsize]
        for k,t,off,sz,mx,fl,al in sorted(defs,key=lambda x:x[2]):
            if fl&2==0 or k in [0]: continue
            n=sz*max(mx,1) if mx>1 else sz
            print('   L %-30s %s'%(nm(k),fmt(t,L[off:off+n])))
    e=o+48+8*tlen
    for i in range(count):
        fk,val,ti,flags=struct.unpack('>QIHH',cv[e+16*i:e+16*i+16])
        t=types[ti] if ti<len(types) else 0
        if flags&0x4000: s=fmt(t,struct.pack('>I',val))
        elif (e+16*i+8) in cp:
            dd=cp[e+16*i+8][1]; sz=deft.get(fk,(0,0,16))[2]; s='@%x '%dd+fmt(t,cb[dd:dd+max(sz,4)*(1 if 'Graph' not in nm(t) else 4)])
        else: s='?'
        print('   E %-30s %s'%(nm(fk),s))
