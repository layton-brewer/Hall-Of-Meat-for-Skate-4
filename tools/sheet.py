import sys,glob
from PIL import Image
d=sys.argv[1]; pre=sys.argv[2] if len(sys.argv)>2 else ''
fs=sorted(glob.glob(d+'/*.png'))
fs=[f for f in fs if not f.endswith('sheet.png')]
W=1100; x=y=0; rowh=0; pos=[]
for f in fs:
    im=Image.open(f); s=3 if im.width<=48 else 2 if im.width<=128 else 1
    iw,ih=im.width*s,im.height*s
    if x+iw>W: x=0; y+=rowh+16; rowh=0
    pos.append((f,x,y,s)); x+=iw+12; rowh=max(rowh,ih)
sheet=Image.new('RGBA',(W,y+rowh+16),(90,90,110,255))
for f,x,y,s in pos:
    im=Image.open(f).convert('RGBA')
    if s>1: im=im.resize((im.width*s,im.height*s),Image.NEAREST)
    sheet.alpha_composite(im,(x,y))
sheet.save(d+'/sheet.png'); print(sheet.size,len(fs))
