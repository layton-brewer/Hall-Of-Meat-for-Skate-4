"""Offline preview of the new X-ray shading (same rules as hom_bones.cpp / s3hom_hud.cpp) next to
Skate 3's footage: rim colour per bone, core toward white by facing^1.4, bloom round each bone."""
import struct, math, sys
import numpy as np
from PIL import Image, ImageFilter

PKG = r"D:\dev\HallOfMeat-mod\pkg\HallOfMeat"
S = 700

def load():
    d = open(PKG + r"\bones.bin", "rb").read()
    n = struct.unpack_from("<I", d, 4)[0]; o = 8; out = []
    for _ in range(n):
        l = d[o]; name = d[o + 1:o + 1 + l].decode(); o += 1 + l
        nv = struct.unpack_from("<I", d, o)[0]; o += 4
        v = np.frombuffer(d, "<f4", nv * 8, o).reshape(nv, 8).copy(); o += 32 * nv
        ni = struct.unpack_from("<I", d, o)[0]; o += 4
        idx = np.frombuffer(d, "<u2", ni, o).reshape(-1, 3).copy(); o += 2 * ni
        out.append((name, v, idx))
    return out

def rim_for(heat, broken):
    if broken: return np.array([236, 70, 26.])
    m = lambda a, b: a + (b - a) * heat
    return np.array([m(198, 236), m(212, 92), m(234, 40)])

def glow_for(heat, broken):
    if broken: return np.array([255, 70, 25.])
    m = lambda a, b: a + (b - a) * heat
    return np.array([m(190, 255), m(205, 95), m(240, 35)])

# Like the Skate 3 shot: the pelvis and one leg broken, an arm hurt, the rest lightly hurt.
state = {"Hips": (1, True), "Thigh_Right": (1, True), "Calf_Right": (1, True), "Forearm_Right": (0.7, False), "Hand_Right": (0.5, False)}
meshes = load()
yaw, pitch = math.radians(20), math.radians(-55)
cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
R = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
centre = np.array([0, 0.95, 0]); scale = S * 0.42
img = np.zeros((S, S, 3)); img[:] = (16, 20, 34)
zb = np.full((S, S), -1e9); glow = np.zeros((S, S, 3))
for name, v, idx in meshes:
    heat, broken = state.get(name, (0.0, False))
    rim = rim_for(heat, broken)
    warm = np.clip((rim[0] - rim[2]) / 200, 0, 1)
    core = np.array([255, 252 - 47 * warm, 255 - 80 * warm])
    p = (v[:, :3] - centre) @ R.T; n = v[:, 3:6] @ R.T
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    f = np.abs(n[:, 2]) ** (0.8 - 0.3 * warm)
    col = rim[None] + (core - rim)[None] * f[:, None]
    sx = S / 2 + p[:, 0] * scale; syy = S / 2 - p[:, 1] * scale; z = p[:, 2]
    for a, b, c in idx:
        xs = np.array([sx[a], sx[b], sx[c]]); ys = np.array([syy[a], syy[b], syy[c]])
        x0, x1 = max(0, int(xs.min())), min(S - 1, int(xs.max()) + 1); y0, y1 = max(0, int(ys.min())), min(S - 1, int(ys.max()) + 1)
        if x0 > x1 or y0 > y1: continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1; ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]; reg = zb[y0:y1 + 1, x0:x1 + 1]; win = ins & (zz > reg)
        if not win.any(): continue
        cc = w0[..., None] * col[a] + w1[..., None] * col[b] + w2[..., None] * col[c]
        reg[win] = zz[win]; img[y0:y1 + 1, x0:x1 + 1][win] = cc[win]
        glow[y0:y1 + 1, x0:x1 + 1][win] = glow_for(heat, broken) * (0.3 + 0.9 * heat)
g = np.asarray(Image.fromarray(np.clip(glow, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), float)
out = np.clip(img + g * 0.55, 0, 255).astype(np.uint8)
ours = Image.fromarray(out)
ref = Image.open(r"D:\dev\skate3-ref\vid\xray_zoom.png").convert("RGB").resize((S, int(S * 720 / 880)))
sheet = Image.new("RGB", (S * 2, S)); sheet.paste(ours, (0, 0)); sheet.paste(ref, (S, (S - ref.height) // 2))
sheet.save(sys.argv[1]); print("ok")
