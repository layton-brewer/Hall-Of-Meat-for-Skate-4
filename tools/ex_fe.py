import os, sys
sys.path.insert(0, r"D:\dev\tools")
import ebbig
b = ebbig.Big(r"D:\dev\skate3-ref\files\data\big\fedynamic.big")
want = ("sponsor_logos/thrasher.rx2", "hud2/hudobjective2.rx2", "hud2/hudcountdown.rx2", "hud2/hudcentral.rx2", "hud2/dpo.rx2", "hud2/leaderboardhud.rx2", "hud2/hudtimer", "hud2/actionoverlay2.rx2", "hud2/hudbase", "hud2/huddistance")
for e in b.entries:
    n = e[0].lower().replace("\\", "/")
    if any(w in n for w in want):
        p = os.path.join(r"D:\dev\skate3-ref\ex\fe_hom", e[0].lstrip("./"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(b.read(e)); print(e[0])
