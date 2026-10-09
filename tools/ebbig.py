"""Reader for EA Skate 'EB' .big archives (Xbox 360, big-endian). Port of GHFear's RW4ArchiveTool parser.

  ebbig.py list <big>
  ebbig.py extract <big> <outdir> [substring ...]
"""
import os
import struct
import sys
import zlib


def refpack_decompress(data):
    # EA RefPack ("0x10FB"). Header: flags(1) 0xFB(1), then size (3 or 4 bytes, big-endian).
    flags = data[0]
    p = 2
    if flags & 0x01:
        p += 4 if flags & 0x80 else 3  # compressed size present
    n = 4 if flags & 0x80 else 3
    size = int.from_bytes(data[p:p + n], "big")
    p += n
    out = bytearray()
    while p < len(data):
        c = data[p]
        p += 1
        if c < 0x80:
            b1 = data[p]; p += 1
            lit = c & 3
            out += data[p:p + lit]; p += lit
            ln = ((c & 0x1C) >> 2) + 3
            off = ((c & 0x60) << 3) + b1 + 1
        elif c < 0xC0:
            b1, b2 = data[p], data[p + 1]; p += 2
            lit = b1 >> 6
            out += data[p:p + lit]; p += lit
            ln = (c & 0x3F) + 4
            off = ((b1 & 0x3F) << 8) + b2 + 1
        elif c < 0xE0:
            b1, b2, b3 = data[p], data[p + 1], data[p + 2]; p += 3
            lit = c & 3
            out += data[p:p + lit]; p += lit
            ln = ((c & 0x0C) << 6) + b3 + 5
            off = ((c & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif c < 0xFC:
            lit = ((c & 0x1F) << 2) + 4
            out += data[p:p + lit]; p += lit
            continue
        else:
            lit = c & 3
            out += data[p:p + lit]; p += lit
            break
        for _ in range(ln):
            out.append(out[-off])
    return bytes(out)


def round_up(v, m):
    return (v + m - 1) // m * m


def chunk_decompress(f, start):
    f.seek(start)
    hdr = f.read(0x1C)
    ident = hdr[:8]
    ver, ulen, block, nseg, align = struct.unpack(">5I", hdr[8:28])
    out = bytearray()
    for i in range(nseg):
        loc = f.tell()
        last = loc % 0x10
        if last > 0x08 or last == 0:
            loc = round_up(loc, align) + 8
        else:
            loc = round_up(loc, 8)
        f.seek(loc)
        csize, ctype = struct.unpack(">II", f.read(8))
        raw = f.read(csize)
        if ctype == 1:
            out += zlib.decompress(raw, -15)
        elif ctype == 2:
            out += refpack_decompress(raw)
        elif ctype == 4:
            out += raw
        elif ctype == 3:
            raise NotImplementedError("LZX chunk")
        else:
            raise ValueError("chunk type %d" % ctype)
    return bytes(out[:ulen]), ident


class Big:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        f = self.f
        h = f.read(0x30)
        sig, ver, nfiles, flags, align, _res, names_off, names_size, fnlen, dirlen, ndirs, asize, fat = struct.unpack(
            ">HHIHBBIIBBHQI", h[:0x24])
        if sig != 0x4542:
            raise ValueError("not an EB archive")
        self.align = align
        folders_off = round_up(nfiles * fnlen + names_off, 0x10)
        h64 = bool(flags & 1)
        f.seek(0x30)
        toc = []
        for _ in range(nfiles):
            n = 5 if h64 else 4
            toc.append(struct.unpack(">%dI" % n, f.read(4 * n)))
        ctypes = f.read(nfiles)
        f.seek(names_off)
        self.entries = []
        names = f.read(nfiles * fnlen)
        folders = None
        for i in range(nfiles):
            rec = names[i * fnlen:(i + 1) * fnlen]
            folder = struct.unpack(">H", rec[:2])[0]
            name = rec[2:].split(b"\0")[0].decode("latin1")
            f.seek(folders_off + folder * dirlen)
            d = f.read(dirlen).split(b"\0")[0].decode("latin1")
            off, csize, size = toc[i][0] << align, toc[i][1], toc[i][2]
            self.entries.append((d + "/" + name if d else name, off, csize, size, ctypes[i]))

    def read(self, entry):
        name, off, csize, size, ct = entry
        f = self.f
        if size == 0:
            return b""
        f.seek(off)
        head = f.read(8)
        if head in (b"chunkref", b"chunkzip", b"chunklzx"):
            return chunk_decompress(f, off)[0]
        f.seek(off)
        raw = f.read(csize if csize else size)
        if len(raw) >= 2 and raw[0] & 0xFE == 0x10 and raw[1] == 0xFB:
            return refpack_decompress(raw)
        return raw[:size] if size else raw


if __name__ == "__main__":
    cmd = sys.argv[1]
    b = Big(sys.argv[2])
    if cmd == "list":
        for e in b.entries:
            print("%10d %10d t%d  %s" % (e[3], e[2], e[4], e[0]))
    elif cmd == "extract":
        out = sys.argv[3]
        filt = sys.argv[4:]
        for e in b.entries:
            if filt and not any(s.lower() in e[0].lower() for s in filt):
                continue
            try:
                data = b.read(e)
            except Exception as ex:  # noqa
                print("FAIL", e[0], ex)
                continue
            p = os.path.join(out, e[0].replace("\\", "/").lstrip("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(data)
            print("ok", e[0], len(data))
