#!/usr/bin/env python3
"""
Replace the SINGLE STICKERS array in js/manifest.static.js with original files found in
images/PINTEREST IMAGES/SINGLE STICKERS.

Usage: python scripts/use_original_stickers.py
"""
from pathlib import Path
import re

MANIFEST = Path('js') / 'manifest.static.js'
STICKER_DIR = Path('images') / 'PINTEREST IMAGES' / 'SINGLE STICKERS'

if not MANIFEST.exists():
    print('Manifest not found:', MANIFEST)
    raise SystemExit(1)
if not STICKER_DIR.exists():
    print('Sticker source dir not found:', STICKER_DIR)
    raise SystemExit(1)

# collect image files (keep original filenames as-is)
files = [p.name for p in sorted(STICKER_DIR.iterdir()) if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif')]
print('Found', len(files), 'sticker source files')

# build new array text
items = [f'    "images/PINTEREST IMAGES/SINGLE STICKERS/{fn}"' for fn in files]
new_array = ',\n'.join(items)
new_block = '"SINGLE STICKERS": [\n' + new_array + '\n  ]'

# replace the existing SINGLE STICKERS block in manifest
text = MANIFEST.read_text(encoding='utf-8')
pattern = re.compile(r'"SINGLE STICKERS"\s*:\s*\[[\s\S]*?\n\s*\]', re.M)
if not pattern.search(text):
    print('Could not find SINGLE STICKERS block in manifest')
    raise SystemExit(1)

new_text = pattern.sub(new_block, text, count=1)
MANIFEST.write_text(new_text, encoding='utf-8')
print('Manifest updated: SINGLE STICKERS now points to original images')
