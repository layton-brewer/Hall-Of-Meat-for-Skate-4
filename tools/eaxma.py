"""Decode Skate 3 (Xbox 360) EA SPLC .bnk sound banks of EA-XMA sounds to WAV files.
eaxma.py <bank.bnk> <outdir>"""
import io
import os
import struct
import sys

import av
import numpy as np


def find_sounds(d):
    # Sounds are SNR headers (codec 3 = EA-XMA) each followed by SNS blocks; find them by header shape.
    out = []
    i = 0
    while i < len(d) - 16:
        b0, b1 = d[i], d[i + 1]
        rate = struct.unpack('>I', d[i:i + 4])[0] & 0x3FFFF
        if b0 == 0x03 and b1 in (0x00, 0x04) and rate in (22050, 24000, 32000, 44100, 48000):
            samples = struct.unpack('>I', d[i + 4:i + 8])[0] & 0x3FFFFFFF
            blk = struct.unpack('>I', d[i + 8:i + 12])[0]
            if 0 < samples < 10_000_000 and (blk >> 24) in (0x00, 0x80) and 0x10 < (blk & 0xFFFFFF) < 0x100000:
                out.append((i, rate, samples, (b1 >> 2) + 1))
                i += 8
                continue
        i += 1
    return out


def packets(d, at):
    # SNS blocks: u32 flags|size (size includes this header), u32 samples, u32 EA sub-header, then XMA2
    # packets (0x800 bytes each, the last one cut short). The 0x80 flag marks the last block.
    data = b''
    o = at
    while True:
        hdr = struct.unpack('>I', d[o:o + 4])[0]
        size = hdr & 0xFFFFFF
        body = d[o + 12:o + size]
        while len(body) % 0x800:
            body += b'\0'
        data += body
        o += size
        if hdr >> 24 == 0x80 or o >= len(d):
            break
        nxt = struct.unpack('>I', d[o:o + 4])[0]
        if nxt >> 24 not in (0x00, 0x80) or (nxt & 0xFFFFFF) < 0x10:
            break
    return data


def xma2_wav(data, rate, channels, samples):
    blocks = len(data) // 0x800
    fmt = struct.pack('<HHIIHHH', 0x166, channels, rate, rate * 2 * channels, 0x800, 16, 34)
    fmt += struct.pack('<HIIIIIIIBBH', 1, 4 if channels == 1 else 3, samples, 0x800 * blocks, 0, samples, 0, 0, 0, 3, blocks)
    riff = b'WAVE' + b'fmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(data)) + data
    return b'RIFF' + struct.pack('<I', len(riff)) + riff


def decode(wav):
    box = av.open(io.BytesIO(wav), format='wav')
    pcm = []
    stream = box.streams.audio[0]
    for packet in box.demux(stream):
        try:
            frames = stream.codec_context.decode(packet)
        except av.error.InvalidDataError:
            continue  # a cut-short last packet: keep what decoded
        for frame in frames:
            pcm.append(frame.to_ndarray().reshape(-1))
    return np.concatenate(pcm) if pcm else np.zeros(0, np.float32)


def write_wav(path, pcm, rate):
    s = (np.clip(pcm, -1, 1) * 32767).astype('<i2').tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(s)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, 1, rate, rate * 2, 2, 16))
        f.write(b'data' + struct.pack('<I', len(s)) + s)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    os.makedirs(sys.argv[2], exist_ok=True)
    stem = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    for n, (at, rate, samples, ch) in enumerate(find_sounds(d)):
        try:
            pcm = decode(xma2_wav(packets(d, at + 8), rate, ch, samples))[:samples]
            write_wav(os.path.join(sys.argv[2], '%s_%02d.wav' % (stem, n)), pcm, rate)
            print('%s_%02d @%x %d Hz %d samples (%.2fs) peak %.2f' % (stem, n, at, rate, samples, samples / rate, float(np.abs(pcm).max()) if len(pcm) else 0))
        except Exception as e:
            print('%s_%02d @%x failed: %s' % (stem, n, at, e))
