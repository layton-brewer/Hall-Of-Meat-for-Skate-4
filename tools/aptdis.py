"""Rough disassembler for EA APT (Xbox 360, big-endian) action bytecode.
aptdis.py <file.apt> <file.const> [start_hex end_hex]
Scans the .apt for action streams and prints instructions with constant-pool names resolved."""
import struct
import sys

apt = open(sys.argv[1], 'rb').read()
const = open(sys.argv[2], 'rb').read()
count = struct.unpack('>I', const[0x18:0x1c])[0]
table = struct.unpack('>I', const[0x1c:0x20])[0]
items = []
for i in range(count):
    t, v = struct.unpack('>II', const[table + 8 * i:table + 8 * i + 8])
    if t == 1:
        end = const.index(b'\0', v)
        items.append(const[v:end].decode('latin1'))
    else:
        items.append(('num', t, v))

def c(i):
    return repr(items[i]) if i < len(items) else '?%d' % i

def al(o):
    return (o + 3) & ~3

NAMES = {0x00: 'end', 0x04: 'nextframe', 0x06: 'play', 0x07: 'stop', 0x0a: 'add', 0x0b: 'sub', 0x0c: 'mul', 0x0d: 'div',
         0x0e: 'eq', 0x0f: 'lt', 0x10: 'and', 0x11: 'or', 0x12: 'not', 0x17: 'pop', 0x18: 'toint', 0x1c: 'getvar', 0x1d: 'setvar',
         0x20: 'settarget2', 0x21: 'strcat', 0x22: 'getprop', 0x23: 'setprop', 0x26: 'trace', 0x34: 'gettime', 0x3a: 'delete',
         0x3b: 'delete2', 0x3c: 'deflocal', 0x3d: 'callfunc', 0x3e: 'return', 0x3f: 'mod', 0x40: 'new', 0x41: 'deflocal2',
         0x42: 'initarray', 0x43: 'initobject', 0x44: 'typeof', 0x47: 'add2', 0x48: 'less2', 0x49: 'equals2', 0x4a: 'tonumber',
         0x4b: 'tostring', 0x4c: 'dup', 0x4d: 'swap', 0x4e: 'getmember', 0x4f: 'setmember', 0x50: 'inc', 0x51: 'dec', 0x52: 'callmethod',
         0x53: 'newmethod', 0x54: 'instanceof', 0x55: 'enumerate2', 0x60: 'bitand', 0x61: 'bitor', 0x62: 'bitxor', 0x63: 'shl',
         0x64: 'shr', 0x66: 'stricteq', 0x67: 'greater', 0x69: 'extends',
         0x59: 'pushzero', 0x5a: 'pushone', 0x5b: 'callfuncpop', 0x5c: 'callfunc', 0x5d: 'callmethodpop', 0x5e: 'callmethod',
         0x70: 'pushthis', 0x71: 'pushglobal', 0x72: 'zerovar', 0x73: 'pushtrue', 0x74: 'pushfalse', 0x75: 'pushnull', 0x76: 'pushundef'}

ONE = {0xa1: 'pushstring', 0xa2: 'pushconst', 0xa4: 'getstringvar', 0xa5: 'getstringmember', 0xa6: 'setstringvar',
       0xa7: 'setstringmember', 0xae: 'pushvalueofvar', 0xaf: 'getnamedmember', 0xb0: 'callnamedfuncpop', 0xb1: 'callnamedfunc',
       0xb2: 'callnamedmethodpop', 0xb3: 'callnamedmethod'}

def dis(start, end):
    o = start
    while o < end:
        op = apt[o]
        at = o
        o += 1
        arg = ''
        if op in NAMES:
            name = NAMES[op]
        elif op in ONE:
            name = ONE[op]; arg = c(apt[o]); o += 1
        elif op == 0xa3:
            name = 'pushwordconst'; arg = c(struct.unpack('>H', apt[o:o + 2])[0]); o += 2
        elif op == 0xb4:
            name = 'pushfloat'; o = al(o); arg = '%g' % struct.unpack('>f', apt[o:o + 4])[0]; o += 4
        elif op == 0xb5:
            name = 'pushbyte'; arg = str(struct.unpack('>b', apt[o:o + 1])[0]); o += 1
        elif op == 0xb6:
            name = 'pushshort'; o = al(o) if False else o; arg = str(struct.unpack('>h', apt[o:o + 2])[0]); o += 2
        elif op == 0xb7:
            name = 'pushlong'; o = al(o); arg = str(struct.unpack('>i', apt[o:o + 4])[0]); o += 4
        elif op == 0xb9:
            name = 'pushreg'; arg = str(apt[o]); o += 1
        elif op in (0x99, 0x9d, 0xb8):
            name = {0x99: 'jmp', 0x9d: 'iftrue', 0xb8: 'iffalse'}[op]; o = al(o)
            rel = struct.unpack('>i', apt[o:o + 4])[0]; o += 4; arg = '-> %x' % (o + rel)
        elif op == 0x87:
            name = 'setreg'; o = al(o); arg = str(struct.unpack('>I', apt[o:o + 4])[0]); o += 4
        elif op in (0x8e, 0x9b):
            name = 'deffunc'; o = al(o)
            arg = ' '.join('%08x' % v for v in struct.unpack('>7I', apt[o:o + 28])); o += 28
        elif op == 0x96:
            name = 'push'; o = al(o); n, p = struct.unpack('>II', apt[o:o + 8]); o += 8
            arg = 'n=%d @%x' % (n, p)
        elif op == 0x88:
            name = 'constpool'; o = al(o); n, p = struct.unpack('>II', apt[o:o + 8]); o += 8; arg = 'n=%d' % n
        elif op in (0x81, 0x8c, 0x9f, 0x8b, 0x83, 0x9a):
            name = 'op%02x' % op; o = al(o); arg = '%08x' % struct.unpack('>I', apt[o:o + 4])[0]; o += 4
        else:
            name = '??%02x' % op
        print('%05x %-18s %s' % (at, name, arg))
        if op == 0x00:
            return o

if len(sys.argv) > 3:
    dis(int(sys.argv[3], 16), int(sys.argv[4], 16))
