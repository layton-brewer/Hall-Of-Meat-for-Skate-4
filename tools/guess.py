"""Guess attrib field names: guess.py <hex hash> ... ; tries word combinations in several casings."""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrib import hash64

targets = {int(h, 16) for h in sys.argv[1:]}
words = '''saturation desaturation sat desat brightness bright contrast gamma tint colour color col black white blacks whites
level levels point lift gain offset shadow shadows midtone midtones mid highlight highlights high low scale bias weight amount
intensity strength blend lerp fade time duration in out luminance luma hue grey gray mono monochrome sepia
noise grain film vignette blur radius size speed slomo slo mo slow motion rate factor min max start end target value threshold
red green blue alpha rgb dark light exposure key filter matrix adjust adjustment base add mul multiply power pow curve range
centre center edge inner outer falloff fish eye distortion zoom focus depth dof near far amp amplitude frequency freq scroll
overlay opacity mix ratio cutoff clamp lum colourise colorize tone toning cross process bloom glow threshhold bleach bypass
default enable enabled on off use pct percent screen dither dirt scratch scratches flicker jitter shake'''.split()
seps = ['', '_']
found = {}

def cases(ws, sep):
    yield sep.join(ws)
    yield sep.join(w.capitalize() for w in ws)
    yield ws[0] + ''.join(w.capitalize() for w in ws[1:])
    yield sep.join(w.upper() for w in ws)

for n in (1, 2):
    for ws in itertools.product(words, repeat=n):
        for sep in seps if n > 1 else ['']:
            for t in cases(list(ws), sep):
                for pre in ('', 'm', 'f', 'm_'):
                    h = hash64(pre + t)
                    if h in targets and h not in found:
                        found[h] = pre + t
                        print('%016x %s' % (h, pre + t), flush=True)
print('found', len(found), 'of', len(targets))
