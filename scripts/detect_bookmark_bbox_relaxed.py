#!/usr/bin/env python3
"""
Relaxed detection for white bookmark area in 013.jpg.
Tries multiple thresholds and heuristics and writes outputs/BOOKMARK/detected_bbox.json
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

thresholds = [240, 230, 220, 200, 180, 160]
found = None
for th in thresholds:
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

    # Row/col thresholds are fractions of width/height
    row_thresh = max(1, int(0.01 * w))
    col_thresh = max(1, int(0.01 * h))
    rows = [i for i,c in enumerate(mask_rows) if c >= row_thresh]
    cols = [i for i,c in enumerate(mask_cols) if c >= col_thresh]

    if rows and cols:
        min_y = rows[0]
        max_y = rows[-1]
        min_x = cols[0]
        max_x = cols[-1]
        bbox = {'x':int(min_x),'y':int(min_y),'width':int(max_x-min_x+1),'height':int(max_y-min_y+1),'threshold':th}
        found = bbox
        print('Detected bbox at threshold', th, bbox)
        break
    else:
        print('No detection at threshold', th)

if not found:
    # Fallback: try luminance based detection
    lum = lambda r,g,b: int(0.2126*r + 0.7152*g + 0.0722*b)
    mask_rows = [0]*h
    mask_cols = [0]*w
    for y in range(h):
        cnt = 0
        for x in range(w):
            r,g,b = px[x,y]
            if lum(r,g,b) >= 200:
                cnt += 1
                mask_cols[x] += 1
        mask_rows[y] = cnt
    row_thresh = max(1, int(0.01 * w))
    col_thresh = max(1, int(0.01 * h))
    rows = [i for i,c in enumerate(mask_rows) if c >= row_thresh]
    cols = [i for i,c in enumerate(mask_cols) if c >= col_thresh]
    if rows and cols:
        min_y = rows[0]
        max_y = rows[-1]
        min_x = cols[0]
        max_x = cols[-1]
        bbox = {'x':int(min_x),'y':int(min_y),'width':int(max_x-min_x+1),'height':int(max_y-min_y+1),'method':'luminance'}
        found = bbox
        print('Detected bbox using luminance:', bbox)

if not found:
    print('Failed to detect white region automatically (all heuristics)')
    raise SystemExit(1)

out = Path('outputs') / 'BOOKMARK' / 'detected_bbox.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(found, indent=2), encoding='utf-8')
print('Wrote', out)
