"""Split a tall mobile capture into clean pieces that fit a 1080x810 canvas.
Cuts are placed in the middle of blank (uniform) row runs between blocks, never through text.
Usage as module: pieces(path, y0, y1, maxh=810, mingap=18) -> [(a,b), ...]
CLI: python3 pieces.py <img> [y0 y1]  -> prints blank runs and pieces."""
import sys
from PIL import Image

def blank_runs(img, y0, y1, tol=6):
    g = img.convert('L')
    w = g.width
    px = g.load()
    runs, start = [], None
    for y in range(y0, y1):
        row = [px[x, y] for x in range(0, w, 3)]
        blank = max(row) - min(row) <= tol
        if blank and start is None:
            start = y
        if not blank and start is not None:
            runs.append((start, y)); start = None
    if start is not None:
        runs.append((start, y1))
    return runs

def pieces(path, y0=0, y1=None, maxh=810, mingap=18):
    img = Image.open(path)
    y1 = y1 or img.height
    cuts = [y0] + [(a + b) // 2 for a, b in blank_runs(img, y0, y1) if b - a >= mingap and a > y0 and b < y1] + [y1]
    blocks = list(zip(cuts[:-1], cuts[1:]))
    out, cur = [], None
    for a, b in blocks:
        if cur is None:
            cur = [a, b]
        elif b - cur[0] <= maxh:
            cur[1] = b
        else:
            out.append(tuple(cur)); cur = [a, b]
    if cur:
        out.append(tuple(cur))
    return out

if __name__ == '__main__':
    p = sys.argv[1]
    y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    y1 = int(sys.argv[3]) if len(sys.argv) > 3 else None
    img = Image.open(p)
    print('runs>=18:', [(a, b) for a, b in blank_runs(img, y0, y1 or img.height) if b - a >= 18])
    print('pieces:', pieces(p, y0, y1))
