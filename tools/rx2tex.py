"""Extract Xbox 360 textures from an EA RW4 'xb2' arena (.rx2) into PNG files.
  rx2tex.py <file.rx2> <outdir>
"""
import io
import os
import struct
import sys

from PIL import Image

FMT = {0x12: ("DXT1", 3), 0x13: ("DXT3", 4), 0x14: ("DXT5", 4)}


def tiled_offset(x, y, pitch, bpb_log2):
    # Xenia's texture_address TiledOffset2DOuter/Inner.
    pitch = (pitch + 31) & ~31
    macro = ((y >> 5) * (pitch >> 5)) << (bpb_log2 + 7)
    micro = ((y & 6) << 2) << bpb_log2
    outer = macro + ((micro & ~0xF) << 1) + (micro & 0xF) + ((y & 8) << (3 + bpb_log2)) + ((y & 1) << 4)
    macro = (x >> 5) << (bpb_log2 + 7)
    micro = (x & 7) << bpb_log2
    off = outer + macro + ((micro & ~0xF) << 1) + (micro & 0xF)
    return ((off & ~0x1FF) << 3) + ((off & 0x1C0) << 2) + (off & 0x3F) + ((y & 16) << 7) + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6)


def untile_dxt(data, w, h, bpb_log2):
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 1 << bpb_log2
    pitch = (bw + 31) & ~31
    rows = (bh + 31) & ~31
    out = bytearray(bw * bh * bs)
    for y in range(bh):
        for x in range(bw):
            o = tiled_offset(x, y, pitch, bpb_log2)
            if o + bs <= len(data):
                out[(y * bw + x) * bs:(y * bw + x + 1) * bs] = data[o:o + bs]
    return bytes(out)


def swap16(b):
    b = bytearray(b)
    b[0::2], b[1::2] = b[1::2], b[0::2]
    return bytes(b)


def dds(w, h, fourcc, payload):
    hdr = struct.pack("<4sI", b"DDS ", 124)
    hdr += struct.pack("<IIIIII", 0x81007, h, w, len(payload), 0, 1) + b"\0" * 44
    hdr += struct.pack("<II4s5I", 32, 4, fourcc.encode(), 0, 0, 0, 0, 0)
    hdr += struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
    return hdr + payload


def main(path, outdir):
    d = open(path, "rb").read()
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    # data section: last N bytes where N is the big dword at 0x54
    data_len = struct.unpack(">I", d[0x54:0x58])[0]
    data_start = len(d) - data_len
    w32 = lambda o: struct.unpack(">I", d[o:o + 4])[0]
    n = 0
    for o in range(0x100, data_start - 0x20, 4):
        if w32(o) == 0xFFFF0000 and w32(o + 4) == 0xFFFF0000:
            dw = [w32(o + 8 + 4 * i) for i in range(6)]
            fmt = dw[1] & 0x3F
            endian = (dw[1] >> 6) & 3
            w = (dw[2] & 0x1FFF) + 1
            h = ((dw[2] >> 13) & 0x1FFF) + 1
            addr = (dw[1] >> 12) * 0x1000
            info = FMT.get(fmt)
            if not info or w > 4096 or h > 4096:
                print("skip rec @%#x fmt=%#x %dx%d" % (o, fmt, w, h))
                continue
            name, bpl = info
            bw, bh = (w + 3) // 4, (h + 3) // 4
            raw = d[data_start + addr: data_start + addr + (max(((dw[0] >> 22) & 0x1FF) * 8, bw) * bh << bpl)]
            raw = raw + bytes(max(0, (max(((dw[0] >> 22) & 0x1FF) * 8, bw) * bh << bpl) - len(raw)))
            if endian == 1:
                raw = swap16(raw)
            pitch_blocks = ((dw[0] >> 22) & 0x1FF) * 8
            bsz = 1 << bpl
            rows = []
            for yy in range(bh):
                rows.append(raw[yy * pitch_blocks * bsz: yy * pitch_blocks * bsz + bw * bsz])
            lin = b"".join(rows)
            if dw[0] >> 31:  # tiled
                lin = untile_dxt(raw, w, h, bpl)
            img = Image.open(io.BytesIO(dds(w, h, name, lin))).convert("RGBA")
            fn = os.path.join(outdir, "%s_%02d_%dx%d_%s.png" % (base, n, w, h, name))
            img.save(fn)
            print("wrote", fn)
            n += 1


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
