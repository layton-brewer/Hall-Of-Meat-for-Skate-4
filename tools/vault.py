"""Dump Skate 3 attrib collections (vault .vlt) with field names resolved from every string in the schema.
vault.py <collections.vlt> <schema dir> <class> [collection ...]"""
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrib import hash64

vlt = open(sys.argv[1], 'rb').read()
names = {}
for f in glob.glob(os.path.join(sys.argv[2], '*')):
    if os.path.isdir(f):
        continue
    for s in re.findall(rb'[A-Za-z_][A-Za-z0-9_:\.]{1,80}', open(f, 'rb').read()):
        t = s.decode()
        for part in {t, t.split('::')[-1], t.lower()}:
            names[hash64(part)] = part
for s in sys.argv[3:]:
    names[hash64(s)] = s

def name(h):
    return names.get(h, '%016x' % h)

binf = open(sys.argv[1][:-4] + '.bin', 'rb').read()
p = vlt.index(b'PtrN')
fix = {}
for q in range(p + 8, p + struct.unpack('>I', vlt[p + 4:p + 8])[0] - 15, 16):
    at, t, fl, dest = struct.unpack('>IHHQ', vlt[q:q + 16])
    if t == 3:
        fix[at] = dest

def pointed(at, n):
    if at not in fix:
        return 'ptr ?'
    d = fix[at]
    words = struct.unpack('>%dI' % n, binf[d:d + 4 * n])
    return '@%x ' % d + ' '.join('%g' % struct.unpack('>f', struct.pack('>I', w))[0] if 0x30000000 < (w & 0x7fffffff) < 0x50000000 or w == 0 else '%08x' % w for w in words)

cls = hash64(sys.argv[3])
FILTER = os.environ.get('VFILTER', 'HoM').split(',')
wanted = {hash64(c) for c in sys.argv[4:]}
datn = vlt.index(b'DatN')
datn_end = datn + struct.unpack('>I', vlt[datn + 4:datn + 8])[0]
o = datn + 8
found = 0
for o in range(datn + 8, datn_end - 0x30, 4):
    key, klass, parent = struct.unpack('>QQQ', vlt[o:o + 24])
    if (sys.argv[3] != '*' and klass != cls) or (wanted and key not in wanted):
        continue
    reserve, _, count, ntypes, tlen = struct.unpack('>IIIHH', vlt[o + 24:o + 40])
    if count > 400 or ntypes > 64:
        continue
    types = struct.unpack('>%dQ' % ntypes, vlt[o + 48:o + 48 + 8 * ntypes])
    if sys.argv[3] == '*' and not any(k in name(t) for t in types for k in FILTER):
        continue
    e = o + 48 + 8 * tlen
    print('== %s.%s (parent %s) %d fields' % (name(klass), name(key), name(parent) if parent else '-', count))
    for i in range(count):
        fk, val, ti, flags = struct.unpack('>QIHH', vlt[e + 16 * i:e + 16 * i + 16])
        f = struct.unpack('>f', struct.pack('>I', val))[0]
        tname = name(types[ti]) if ti < len(types) else '?'
        print('   %-36s %-28s %s' % (name(fk), tname, ('%08x  %g' % (val, f)) if flags & 0x4000 else pointed(e + 16 * i + 8, 16 if 'Graph' in tname else 4)))
    found += 1
print(found, 'collections')
