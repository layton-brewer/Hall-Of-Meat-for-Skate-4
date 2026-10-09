import os
import sys

sys.path.insert(0, r"D:\dev\tools")
import ebbig

ROOT = r"D:\dev\skate3-ref\files\data"
E = r"D:\dev\skate3-ref\ex"


def ex(big, subs, out):
    b = ebbig.Big(os.path.join(ROOT, big))
    n = 0
    for e in b.entries:
        if any(s in e[0].lower() for s in subs):
            p = os.path.join(E, out, e[0].lstrip("./").replace("\\", "/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            try:
                open(p, "wb").write(b.read(e))
                n += 1
            except Exception as ex_:
                print("FAIL", e[0], ex_)
    print(big, n)


ex(r"content\marquee.big", ["dem_bones_hom"], "bones")
ex(r"big\miscload.big", ["dem_bones_hom", "wipeout.xml"], "misc")
ex(r"audio\audiofiles.big", ["hom_"], "audio")
ex(r"audio\english\livingworldspeech.big", ["_hom.dat"], "audio_speech")
ex(r"big\db.big", ["hom_challenge"], "db_hom")
