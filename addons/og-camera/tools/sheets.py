"""Contact sheets from a video: sheets.py <video> <outPrefix> <everySeconds> [start] [end] [cols] [tileWidth]"""
import sys

import av
from PIL import Image, ImageDraw

video, prefix, every = sys.argv[1], sys.argv[2], float(sys.argv[3])
start = float(sys.argv[4]) if len(sys.argv) > 4 else 0
end = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 3
tile = int(sys.argv[7]) if len(sys.argv) > 7 else 640
rows = 3
container = av.open(video)
stream = container.streams.video[0]
print('duration', float(container.duration) / 1e6, 'size', stream.width, stream.height, 'fps', float(stream.average_rate))
tiles, sheet_no, next_t = [], 0, start


def flush():
    global tiles, sheet_no
    if not tiles:
        return
    w, h = tiles[0][1].size
    sheet = Image.new('RGB', (cols * w, rows * h))
    d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(tiles):
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 70, y + 22], fill=(0, 0, 0))
        d.text((x + 4, y + 4), '%.1fs' % t, fill=(255, 255, 0))
    path = '%s_%02d.jpg' % (prefix, sheet_no)
    sheet.save(path, quality=85)
    print(path, [round(t, 1) for t, _ in tiles])
    sheet_no += 1
    tiles = []


if start > 0:
    container.seek(int(start / stream.time_base), stream=stream)
for frame in container.decode(stream):
    t = float(frame.pts * stream.time_base)
    if t < next_t:
        continue
    if t > end:
        break
    im = frame.to_image()
    im = im.resize((tile, int(im.height * tile / im.width)))
    tiles.append((t, im))
    next_t = t + every
    if len(tiles) == cols * rows:
        flush()
flush()
