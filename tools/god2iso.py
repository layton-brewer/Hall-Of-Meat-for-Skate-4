"""Join the Data#### parts of an Xbox 360 Games-on-Demand package into one raw image.

Each part is: 1 master hash block, then 203 groups of (1 sub-hash block + 204 data blocks),
all blocks 0x1000 bytes. The hash blocks are dropped; the data blocks are the game partition.
"""
import os
import sys

BLOCK = 0x1000
PER_SUB = 0xCC
SUBS = 0xCB


def join(data_dir, out_path):
    parts = sorted(f for f in os.listdir(data_dir) if f.startswith("Data"))
    with open(out_path, "wb") as out:
        for name in parts:
            with open(os.path.join(data_dir, name), "rb") as f:
                f.seek(BLOCK)  # master hash table
                for _ in range(SUBS):
                    f.seek(BLOCK, 1)  # sub hash table
                    chunk = f.read(BLOCK * PER_SUB)
                    if not chunk:
                        break
                    out.write(chunk)
            print(name, flush=True)


if __name__ == "__main__":
    join(sys.argv[1], sys.argv[2])
