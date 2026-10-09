"""EA RW4 'xb2' arena (big-endian) reader: header, dictionary of objects, base (data) section.
  rw4.py <file.rx2>   -> prints the object dictionary
"""
import struct
import sys

TYPES = {
    0x00010030: "Raster/Texture",
    0x000200E9: "VertexDescriptor?",
    0x000200EA: "VertexBuffer",
    0x000200EB: "IndexBuffer",
    0x00EB0001: "Mesh?",
    0x00EB0005: "MeshHelper?",
    0x00010031: "BaseResource",
}


class Arena:
    def __init__(self, path):
        self.d = d = open(path, "rb").read()
        w = lambda o: struct.unpack(">I", d[o:o + 4])[0]
        self.w = w
        self.count = w(0x20)
        self.dict_off = w(0x30)
        self.base_size = w(0x54)
        self.base_off = len(d) - self.base_size
        self.entries = []
        for i in range(self.count):
            o = self.dict_off + i * 0x18
            ptr, reloc, size, align, tindex, tid = struct.unpack(">6I", d[o:o + 0x18])
            self.entries.append(dict(i=i, ptr=ptr, reloc=reloc, size=size, align=align, tindex=tindex, tid=tid))

    def data(self, e):
        # objects with type ids 0x10030 (raster data) etc. may live in the base section; heuristics:
        return self.d[e["ptr"]:e["ptr"] + e["size"]]


if __name__ == "__main__":
    a = Arena(sys.argv[1])
    print("objects", a.count, "dict", hex(a.dict_off), "base", hex(a.base_off), hex(a.base_size), "file", hex(len(a.d)))
    for e in a.entries:
        print("%3d ptr=%7x size=%7x align=%4x tindex=%2d tid=%08x %s" % (e["i"], e["ptr"], e["size"], e["align"], e["tindex"], e["tid"], TYPES.get(e["tid"], "")))
