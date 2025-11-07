#!/usr/bin/env python3
"""
Remove near-white background from sticker images and save transparent PNGs.
Writes new files replacing the extension: "*_full.png" next to originals.

Usage: python scripts/remove_sticker_backgrounds.py
"""
from PIL import Image, ImageFilter
from pathlib import Path

OUT_DIR = Path('outputs') / 'SINGLE STICKERS'
if not OUT_DIR.exists():
    print('No SINGLE STICKERS outputs directory:', OUT_DIR)
    raise SystemExit(1)

files = sorted(OUT_DIR.glob('*_full.*'))
print('Found', len(files), 'sticker files to process')

for p in files:
    try:
        img = Image.open(p).convert('RGBA')
        rgba = img.split()
        r, g, b, a = img.split()
        # Create mask for near-white pixels
        # Threshold: consider pixel background if r,g,b all > 240
        mask = Image.new('L', img.size, 0)
        pix = img.load()
        mw, mh = img.size
        mdata = mask.load()
        for y in range(mh):
            for x in range(mw):
                pr, pg, pb, pa = pix[x, y]
                if pr >= 245 and pg >= 245 and pb >= 245:
                    mdata[x, y] = 0
                else:
                    mdata[x, y] = 255
        # smooth mask to reduce jagged edges
        mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
        # apply mask as alpha
        new = img.copy()
        new.putalpha(mask)

        new_name = p.with_suffix('.png')
        new.save(new_name, optimize=True)
        print('Wrote:', new_name)
    except Exception as e:
        print('Error processing', p, e)

print('Done')
