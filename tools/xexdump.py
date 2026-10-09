"""Decrypt and decompress a retail XEX2 (Xbox 360) into its PE image.
xexdump.py <default.xex> <out.bin>
AES via Windows BCrypt; LZX by wrapping the chunks in a CAB and running Windows expand.exe."""
import ctypes
import os
import struct
import subprocess
import sys
import tempfile

RETAIL_KEY = bytes.fromhex('20B185A59D28FDC340583FBB0896BF91')
bcrypt = ctypes.WinDLL('bcrypt')


def aes(key, data, mode):
    alg = ctypes.c_void_p()
    assert bcrypt.BCryptOpenAlgorithmProvider(ctypes.byref(alg), 'AES', None, 0) == 0
    m = ('ChainingModeECB' if mode == 'ecb' else 'ChainingModeCBC') + '\0'
    assert bcrypt.BCryptSetProperty(alg, 'ChainingMode', ctypes.c_wchar_p(m), len(m) * 2, 0) == 0
    handle = ctypes.c_void_p()
    assert bcrypt.BCryptGenerateSymmetricKey(alg, ctypes.byref(handle), None, 0, key, len(key), 0) == 0
    out = ctypes.create_string_buffer(len(data))
    got = ctypes.c_ulong()
    iv = ctypes.create_string_buffer(16) if mode == 'cbc' else None
    status = bcrypt.BCryptDecrypt(handle, data, len(data), None, iv, 16 if iv else 0, out, len(data), ctypes.byref(got), 0)
    assert status == 0, hex(status & 0xffffffff)
    return out.raw[:got.value]


def main(src, dst):
    d = open(src, 'rb').read()
    pe_off, sec_off, count = struct.unpack('>I', d[8:12])[0], struct.unpack('>I', d[16:20])[0], struct.unpack('>I', d[20:24])[0]
    headers = dict(struct.unpack('>II', d[24 + 8 * i:32 + 8 * i]) for i in range(count))
    ff = headers[0x3FF]
    info_size, enc, comp = struct.unpack('>IHH', d[ff:ff + 8])
    payload = d[pe_off:]
    if enc:
        session = aes(RETAIL_KEY, d[sec_off + 0x150:sec_off + 0x160], 'ecb')
        payload = aes(session, payload[:len(payload) // 16 * 16], 'cbc')
    if comp == 1:  # basic: (data size, zero size) pairs
        out = bytearray()
        o = 0
        for i in range((info_size - 8) // 8):
            ds, zs = struct.unpack('>II', d[ff + 8 + 8 * i:ff + 16 + 8 * i])
            out += payload[o:o + ds] + b'\0' * zs
            o += ds
        open(dst, 'wb').write(out)
        return
    assert comp == 2, comp
    window = struct.unpack('>I', d[ff + 8:ff + 12])[0]
    block_size = struct.unpack('>I', d[ff + 12:ff + 16])[0]
    chunks = []
    o = 0
    while block_size:
        block = payload[o:o + block_size]
        o += block_size
        block_size = struct.unpack('>I', block[0:4])[0]
        p = 24
        while p + 2 <= len(block):
            n = struct.unpack('>H', block[p:p + 2])[0]
            p += 2
            if n == 0:
                break
            chunks.append(block[p:p + n])
            p += n
    bits = window.bit_length() - 1
    write_cab(chunks, bits, dst)


def write_cab(chunks, bits, dst):
    # One folder (LZX, window 2^bits), one file; each XEX chunk is one CFDATA block of 32 KiB output,
    # the last one shorter: give the file a generous size and let expand stop at the stream's end.
    name = b'image.bin\0'
    total = 0x8000 * len(chunks)
    head = 36
    folder = 8
    file_entry = 16 + len(name)
    data_off = head + folder + file_entry
    body = b''.join(struct.pack('<IHH', 0, len(c), 0x8000) + c for c in chunks)
    cab_size = data_off + len(body)
    cab = struct.pack('<4sIIIIIBBHHHHH', b'MSCF', 0, cab_size, 0, head + folder, 0, 3, 1, 1, 1, 0, 0, 0)
    cab += struct.pack('<IHH', data_off, len(chunks), 3 | (bits << 8))
    cab += struct.pack('<IIHHHH', total, 0, 0, 0x5A21, 0, 0x20) + name
    cab += body
    tmp = tempfile.mkdtemp()
    cab_path = os.path.join(tmp, 'x.cab')
    open(cab_path, 'wb').write(cab)
    out_dir = os.path.join(tmp, 'out')
    os.makedirs(out_dir)
    r = subprocess.run([r'C:\Windows\System32\expand.exe', '-D', cab_path], capture_output=True, text=True)
    print(r.stdout[-400:])
    r = subprocess.run([r'C:\Windows\System32\expand.exe', cab_path, '-F:*', out_dir], capture_output=True, text=True)
    print(r.stdout[-400:], r.stderr[-400:])
    os.replace(os.path.join(out_dir, 'image.bin'), dst)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
