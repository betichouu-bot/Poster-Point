#!/usr/bin/env python3
"""
Replace the BOOKMARK array in js/manifest.static.js with original files found in
images/PINTEREST IMAGES/BOOKMARK.

Usage: python scripts/use_original_bookmarks.py
"""
from pathlib import Path
import re

MANIFEST = Path('js') / 'manifest.static.js'
BOOKMARK_DIR = Path('images') / 'PINTEREST IMAGES' / 'BOOKMARK'

if not MANIFEST.exists():
    print('Manifest not found:', MANIFEST)
    raise SystemExit(1)
if not BOOKMARK_DIR.exists():
    print('Bookmark source dir not found:', BOOKMARK_DIR)
    raise SystemExit(1)

# collect image files (keep original filenames as-is)
files = [p.name for p in sorted(BOOKMARK_DIR.iterdir()) if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif')]
print('Found', len(files), 'bookmark source files')

# build new array text
items = [f'    "images/PINTEREST IMAGES/BOOKMARK/{fn}"' for fn in files]
new_array = ',\n'.join(items)
new_block = '"BOOKMARK": [\n' + new_array + '\n  ]'

# replace the existing BOOKMARK block in manifest
text = MANIFEST.read_text(encoding='utf-8')
pattern = re.compile(r'"BOOKMARK"\s*:\s*\[[\s\S]*?\n\s*\]', re.M)
if not pattern.search(text):
    print('Could not find BOOKMARK block in manifest')
    raise SystemExit(1)

new_text = pattern.sub(new_block, text, count=1)
MANIFEST.write_text(new_text, encoding='utf-8')
print('Manifest updated: BOOKMARK now points to original images')
