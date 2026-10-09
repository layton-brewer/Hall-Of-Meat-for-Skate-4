"""Export Skate 3's X-ray bone meshes (dem_bones_hom) to HallOfMeat/bones.bin, and a preview.
  bones_export.py <dem_bones_hom dir> <out bones.bin> [preview.png]
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rw4

ORDER = ["Skull", "Neck", "Rib_Cage", "Lower_Spine", "Hips", "Bicep_Left", "Bicep_Right", "Forearm_Left", "Forearm_Right",
         "Hand_Left", "Hand_Right", "Thigh_Left", "Thigh_Right", "Calf_Left", "Calf_Right", "Ankle_Left", "Ankle_Right",
         "Toes_Left", "Toes_Right"]


def dec3n(v):
    out = []
    for shift in (0, 10, 20):
        x = (v >> shift) & 0x3FF
        if x & 0x200:
            x -= 0x400
        out.append(x / 511.0)
    return out


def load(path):
    a = rw4.Arena(path)
    d = a.d
    bases = [e for e in a.entries if e["tid"] == 0x10031]
    ib = [e for e in a.entries if e["tid"] == 0x200EB][0]
    icount = struct.unpack(">I", d[ib["ptr"] + 0x20:ib["ptr"] + 0x24])[0]
    vres, ires = bases[0], bases[1]
    vb = d[a.base_off + vres["ptr"]:a.base_off + vres["ptr"] + vres["size"]]
    n = vres["size"] // 0x18
    verts = []
    for i in range(n):
        x, y, z, _ = struct.unpack(">4h", vb[i * 0x18:i * 0x18 + 8])
        nrm = dec3n(struct.unpack(">I", vb[i * 0x18 + 8:i * 0x18 + 12])[0])
        u, v = struct.unpack(">2h", vb[i * 0x18 + 0xC:i * 0x18 + 0x10])
        verts.append(((x * 2 / 32767, y * 2 / 32767 + 0.8, z * 2 / 32767), nrm, (u / 32767, v / 32767)))
    ibuf = d[a.base_off + ires["ptr"]:a.base_off + ires["ptr"] + ires["size"]]
    icount = min(icount, len(ibuf) // 2)
    icount -= icount % 3
    idx = list(struct.unpack(">%dH" % icount, ibuf[:icount * 2]))
    idx = [i for i in idx]
    assert max(idx) < n
    return verts, idx


def main():
    root, out = sys.argv[1], sys.argv[2]
    meshes = []
    for name in ORDER:
        path = glob.glob(os.path.join(root, "Bones_" + name, "*.rx2"))[0]
        meshes.append((name, *load(path)))
    with open(out, "wb") as f:
        f.write(b"HOM2" + struct.pack("<I", len(meshes)))
        for name, verts, idx in meshes:
            nb = name.encode()
            f.write(struct.pack("<B", len(nb)) + nb)
            f.write(struct.pack("<I", len(verts)))
            for p, nrm, uv in verts:
                f.write(struct.pack("<8f", *p, *nrm, *uv))
            f.write(struct.pack("<I", len(idx)))
            f.write(struct.pack("<%dH" % len(idx), *idx))
    for name, verts, idx in meshes:
        xs = [v[0] for v in verts]
        lo = [min(c[k] for c in xs) for k in range(3)]
        hi = [max(c[k] for c in xs) for k in range(3)]
        print("%-12s v=%5d t=%5d  min(%.3f %.3f %.3f) max(%.3f %.3f %.3f)" % (name, len(verts), len(idx) // 3, *lo, *hi))
    if len(sys.argv) > 3:
        from PIL import Image, ImageDraw
        W, H = 900, 900
        im = Image.new("RGB", (W, H), (20, 20, 30))
        dr = ImageDraw.Draw(im)
        for view, ox in ((0, 0), (2, 450)):
            for name, verts, idx in meshes:
                for t in range(0, len(idx), 3):
                    pts = []
                    for k in range(3):
                        p = verts[idx[t + k]][0]
                        pts.append((ox + 225 + p[view] * 220, H - 20 - p[1] * 220 * 2.0 + 0))
                    dr.polygon(pts, outline=(200, 230, 255))
        im.save(sys.argv[3])


if __name__ == "__main__":
    main()
