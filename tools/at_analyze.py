"""Analyse an autotest log: map physics bodies to X-ray joints, then measure body-vs-joint gaps over the fall."""
import re
import sys
import math

log = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
frames = {}
order = []
for line in log:
    m = re.search(r"HoM rig: (AT [^ ]+(?: [^ ]+)?) (body|xray|root)", line)
    if not m:
        continue
    tag = m.group(1).replace(" body", "").replace(" xray", "").replace(" root", "")
    tag = re.match(r"(AT (?:stand|[0-9.]+))", line[line.index("AT "):]).group(1)
    fr = frames.setdefault(tag, {"bodies": {}, "xray": {}})
    if tag not in order:
        order.append(tag)
    b = re.search(r"body +(\d+): (.*)$", line)
    if b:
        vals = b.group(2).split()
        f = [float(v) if v != "*" else float("nan") for v in vals]
        fr["bodies"][int(b.group(1))] = f
    x = re.search(r"xray +(\d+): \(([-\d.]+),([-\d.]+),([-\d.]+)\) \(([-\d.]+),([-\d.]+),([-\d.]+)\)", line)
    if x:
        v = [float(x.group(k)) for k in range(2, 8)]
        fr["xray"][int(x.group(1))] = (v[:3], v[3:])

# named joints from the X-ray segments
def joints(fr):
    X = fr["xray"]
    if len(X) < 19:
        return {}
    return {
        "head103": X[0][0], "headtop": X[0][1], "neck101": X[1][0], "chest44": X[2][0], "pelvis7": X[3][0], "spine43": X[3][1],
        "Lhip341": X[4][0], "Rhip8": X[4][1], "Lsho276": X[5][0], "Lelb277": X[5][1], "Rsho47": X[6][0], "Relb48": X[6][1],
        "Lwri278": X[7][1], "Rwri49": X[8][1], "Lhand": X[9][1], "Rhand": X[10][1], "Lknee342": X[11][1], "Rknee9": X[12][1],
        "Lank343": X[13][1], "Rank10": X[14][1], "Lball344": X[17][0], "Rball11": X[18][0],
    }

def pos(f):
    return f[20:23]

def d(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

st = frames[order[0]]
J = joints(st)
mapping = {}
print("standing: body -> nearest joint")
for k in sorted(st["bodies"]):
    p = pos(st["bodies"][k])
    best = sorted(J.items(), key=lambda kv: d(kv[1], p))[:2]
    mass = st["bodies"][k][44] if len(st["bodies"][k]) > 44 else 0
    mapping[k] = best[0][0]
    print("  body %2d mass %.3f -> %-9s %.3f   (next %-9s %.3f)" % (k, mass, best[0][0], d(best[0][1], p), best[1][0], d(best[1][1], p)))

print("\nover the fall: mean gap body->its joint (m), and pelvis height")
for tag in order[1:]:
    fr = frames[tag]
    Jf = joints(fr)
    if not Jf or len(fr["bodies"]) < 23:
        continue
    gaps = [d(pos(fr["bodies"][k]), Jf[mapping[k]]) for k in fr["bodies"]]
    worst = max(range(len(gaps)), key=lambda i: gaps[i])
    print("  %-8s mean %.3f max %.3f (body %d %s)  pelvis y %.2f" % (tag, sum(gaps) / len(gaps), gaps[worst], list(fr["bodies"])[worst], mapping[list(fr["bodies"])[worst]], Jf["pelvis7"][1]))
