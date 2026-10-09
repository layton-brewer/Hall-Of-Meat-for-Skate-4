"""EA Attrib (vault) helpers for Skate 3: 64-bit name hash."""
M = (1 << 64) - 1


def _mix(a, b, c):
    a = (a - b - c) & M; a ^= c >> 43
    b = (b - c - a) & M; b ^= (a << 9) & M
    c = (c - a - b) & M; c ^= b >> 8
    a = (a - b - c) & M; a ^= c >> 38
    b = (b - c - a) & M; b ^= (a << 23) & M
    c = (c - a - b) & M; c ^= b >> 5
    a = (a - b - c) & M; a ^= c >> 35
    b = (b - c - a) & M; b ^= (a << 49) & M
    c = (c - a - b) & M; c ^= b >> 11
    a = (a - b - c) & M; a ^= c >> 12
    b = (b - c - a) & M; b ^= (a << 18) & M
    c = (c - a - b) & M; c ^= b >> 22
    return a, b, c


def hash64(text, level=0xABCDEF0011223344):
    k = text.encode('latin1') if isinstance(text, str) else text
    n = len(k)
    a = b = level
    c = 0x9E3779B97F4A7C13
    i = 0
    while n - i >= 24:
        a = (a + int.from_bytes(k[i:i + 8], 'little')) & M
        b = (b + int.from_bytes(k[i + 8:i + 16], 'little')) & M
        c = (c + int.from_bytes(k[i + 16:i + 24], 'little')) & M
        a, b, c = _mix(a, b, c)
        i += 24
    c = (c + n) & M
    rest = k[i:]
    for j, ch in enumerate(rest):
        if j >= 16:
            c = (c + (ch << (8 * (j - 16 + 1)))) & M
        elif j >= 8:
            b = (b + (ch << (8 * (j - 8)))) & M
        else:
            a = (a + (ch << (8 * j))) & M
    return _mix(a, b, c)[2]


def hash32(text, level=0xABCDEF00):
    k = text.encode('latin1') if isinstance(text, str) else text
    m = 0xFFFFFFFF

    def mix(a, b, c):
        a = (a - b - c) & m; a ^= c >> 13
        b = (b - c - a) & m; b ^= (a << 8) & m
        c = (c - a - b) & m; c ^= b >> 13
        a = (a - b - c) & m; a ^= c >> 12
        b = (b - c - a) & m; b ^= (a << 16) & m
        c = (c - a - b) & m; c ^= b >> 5
        a = (a - b - c) & m; a ^= c >> 3
        b = (b - c - a) & m; b ^= (a << 10) & m
        c = (c - a - b) & m; c ^= b >> 15
        return a, b, c

    n = len(k)
    a = b = 0x9E3779B9
    c = level
    i = 0
    while n - i >= 12:
        a = (a + int.from_bytes(k[i:i + 4], 'little')) & m
        b = (b + int.from_bytes(k[i + 4:i + 8], 'little')) & m
        c = (c + int.from_bytes(k[i + 8:i + 12], 'little')) & m
        a, b, c = mix(a, b, c)
        i += 12
    c = (c + n) & m
    for j, ch in enumerate(k[i:]):
        if j >= 8:
            c = (c + (ch << (8 * (j - 7)))) & m
        elif j >= 4:
            b = (b + (ch << (8 * (j - 4)))) & m
        else:
            a = (a + (ch << (8 * j))) & m
    return mix(a, b, c)[2]
