"""Disassemble Lua 5.1 bytecode (big-endian, 4-byte int/size_t) found embedded in a file.
  luadis.py <file>   -> prints every embedded chunk with constants and annotated instructions
"""
import struct
import sys

OPS = ["MOVE", "LOADK", "LOADBOOL", "LOADNIL", "GETUPVAL", "GETGLOBAL", "GETTABLE", "SETGLOBAL", "SETUPVAL", "SETTABLE",
       "NEWTABLE", "SELF", "ADD", "SUB", "MUL", "DIV", "MOD", "POW", "UNM", "NOT", "LEN", "CONCAT", "JMP", "EQ", "LT", "LE",
       "TEST", "TESTSET", "CALL", "TAILCALL", "RETURN", "FORLOOP", "FORPREP", "TFORLOOP", "SETLIST", "CLOSE", "CLOSURE", "VARARG"]
ABC = {"MOVE": "AB", "LOADBOOL": "ABC", "LOADNIL": "AB", "GETUPVAL": "AB", "GETTABLE": "ABC", "SETUPVAL": "AB",
       "SETTABLE": "ABC", "NEWTABLE": "ABC", "SELF": "ABC", "ADD": "ABC", "SUB": "ABC", "MUL": "ABC", "DIV": "ABC",
       "MOD": "ABC", "POW": "ABC", "UNM": "AB", "NOT": "AB", "LEN": "AB", "CONCAT": "ABC", "EQ": "ABC", "LT": "ABC",
       "LE": "ABC", "TEST": "AC", "TESTSET": "ABC", "CALL": "ABC", "TAILCALL": "ABC", "RETURN": "AB",
       "TFORLOOP": "AC", "SETLIST": "ABC", "VARARG": "AB", "CLOSE": "A"}


class R:
    def __init__(self, d, p):
        self.d, self.p = d, p

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def i32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]; self.p += 4; return v

    def f64(self):
        v = struct.unpack_from("<f", self.d, self.p)[0]; self.p += 4; return v

    def string(self):
        n = self.i32()
        if n == 0:
            return None
        s = self.d[self.p:self.p + n - 1].decode("latin1"); self.p += n
        return s


def func(r):
    f = {}
    f["src"] = r.string(); f["line"] = r.i32(); r.i32()
    f["nup"] = r.u8(); f["np"] = r.u8(); f["va"] = r.u8(); f["ms"] = r.u8()
    f["code"] = [r.i32() for _ in range(r.i32())]
    ks = []
    for _ in range(r.i32()):
        t = r.u8()
        ks.append(None if t == 0 else bool(r.u8()) if t == 1 else r.f64() if t == 3 else r.string())
    f["k"] = ks
    f["p"] = [func(r) for _ in range(r.i32())]
    n = r.i32(); f["lines"] = [r.i32() for _ in range(n)]
    f["locs"] = [(r.string(), r.i32(), r.i32()) for _ in range(r.i32())]
    f["ups"] = [r.string() for _ in range(r.i32())]
    return f


def kname(f, x):
    k = f["k"][x] if x < len(f["k"]) else "?"
    return repr(k)


def rk(f, x):
    return ("K[%s]" % kname(f, x - 256)) if x >= 256 else "R%d" % x


def dump(f, indent=0, name="main"):
    pad = "  " * indent
    print("%sfunction %s (params=%d line=%d)" % (pad, name, f["np"], f["line"]))
    for i, ins in enumerate(f["code"]):
        op = OPS[ins & 0x3F]; A = (ins >> 6) & 0xFF; C = (ins >> 14) & 0x1FF; B = (ins >> 23) & 0x1FF
        Bx = (ins >> 14) & 0x3FFFF; sBx = Bx - 131071
        if op in ("LOADK", "GETGLOBAL", "SETGLOBAL"):
            a = "R%d %s" % (A, kname(f, Bx))
        elif op == "CLOSURE":
            a = "R%d proto#%d" % (A, Bx)
        elif op in ("JMP", "FORLOOP", "FORPREP"):
            a = "R%d -> %d" % (A, i + 1 + sBx)
        elif op in ("GETTABLE", "SELF"):
            a = "R%d R%d %s" % (A, B, rk(f, C))
        elif op == "SETTABLE":
            a = "R%d %s %s" % (A, rk(f, B), rk(f, C))
        elif op in ("ADD", "SUB", "MUL", "DIV", "MOD", "POW", "EQ", "LT", "LE"):
            a = "%s %s %s" % ("R%d" % A if op not in ("EQ", "LT", "LE") else A, rk(f, B), rk(f, C))
        else:
            a = " ".join("%s=%d" % (x, v) for x, v in zip("ABC", (A, B, C)) if x in ABC.get(op, "A"))
        ln = f["lines"][i] if i < len(f["lines"]) else 0
        print("%s  %4d [%4d] %-9s %s" % (pad, i, ln, op, a))
    for j, p in enumerate(f["p"]):
        dump(p, indent + 1, "proto#%d" % j)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    i = 0
    while True:
        i = d.find(b"\x1bLua", i)
        if i < 0:
            break
        r = R(d, i + 12)
        try:
            f = func(r)
            print("==== chunk @%d src=%s" % (i, f["src"]))
            dump(f)
        except Exception as e:  # noqa
            print("ERR", i, e)
        i = r.p if r.p > i else i + 4
