import sys,itertools; sys.path.insert(0,'.')
from attrib import hash64
T={int(h,16) for h in sys.argv[1:]}
w='''score points bones bone damage time speed bail duration intensity effect blur radial motion zoom fov camera slomo slow slowmo
time_scale timescale scale rate blend fade in out vignette colour color tint noise grain amount strength size radius alpha
saturation contrast brightness desaturation bloom glow threshold exposure fisheye fish_eye distortion vs to from over by graph
curve func function factor min max start end target delay length impact velocity force hit pain red flash pulse frequency
inner outer edge centre center darkness dark light lum luminance x y z pos position offset width height falloff power
near far focus dof depth chromatic aberration ghost trail streak sharp sharpen'''.split()
found={}
for n in (1,2,3):
  for ws in itertools.product(w,repeat=n):
    for s in ('_'.join(ws),''.join(ws)):
      h=hash64(s)
      if h in T and h not in found: found[h]=s; print('%016x %s'%(h,s),flush=True)
print('found',len(found),'of',len(T))
