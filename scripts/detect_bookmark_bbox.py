#!/usr/bin/env python3
"""
Detect the largest near-white area in template 013.jpg and output a bounding box.
This uses a simple heuristic: threshold near-white pixels and take rows/cols where
white pixel count exceeds a small fraction of image width/height.

Usage: python scripts/detect_bookmark_bbox.py
"""
from PIL import Image
from pathlib import Path
import json

TPL = Path('013.jpg')
if not TPL.exists():
    print('Template not found:', TPL)
    raise SystemExit(1)

img = Image.open(TPL).convert('RGB')
w,h = img.size
px = img.load()

# Build white mask where r,g,b >= threshold
th = 240
mask_rows = [0]*h
mask_cols = [0]*w
for y in range(h):
    cnt = 0
    for x in range(w):
        r,g,b = px[x,y]
        if r>=th and g>=th and b>=th:
            cnt += 1
            mask_cols[x] += 1
    mask_rows[y] = cnt

# Row/col thresholds (fraction of width/height)
row_thresh = max(1, int(0.02 * w))
col_thresh = max(1, int(0.02 * h))

rows = [i for i,c in enumerate(mask_rows) if c >= row_thresh]
cols = [i for i,c in enumerate(mask_cols) if c >= col_thresh]

if not rows or not cols:
    print('No white region detected using threshold; trying relaxed threshold')
    row_thresh = max(1, int(0.01 * w))
    col_thresh = max(1, int(0.01 * h))
    rows = [i for i,c in enumerate(mask_rows) if c >= row_thresh]
    cols = [i for i,c in enumerate(mask_cols) if c >= col_thresh]

if not rows or not cols:
    print('Failed to detect white region automatically')
    raise SystemExit(1)

min_y = rows[0]
max_y = rows[-1]
min_x = cols[0]
max_x = cols[-1]

bbox = {
    'x': int(min_x),
    'y': int(min_y),
    'width': int(max_x - min_x + 1),
    'height': int(max_y - min_y + 1)
}
print('Detected bbox:', bbox)
# write to file for reuse
out = Path('outputs') / 'BOOKMARK' / 'detected_bbox.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(bbox, indent=2), encoding='utf-8')
print('Wrote', out)
