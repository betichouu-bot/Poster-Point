#!/usr/bin/env python3
"""
Update js/manifest.static.js to prefer .png files for SINGLE STICKERS when the corresponding PNG exists.

Usage: python scripts/update_manifest_for_stickers.py
"""
from pathlib import Path
import re

MANIFEST = Path('js') / 'manifest.static.js'
STICKER_DIR = Path('outputs') / 'SINGLE STICKERS'
if not MANIFEST.exists():
    print('Manifest not found:', MANIFEST)
    raise SystemExit(1)

text = MANIFEST.read_text(encoding='utf-8')

# Find all occurrences inside the SINGLE STICKERS array and replace .jpg -> .png when png exists
start_token = '"SINGLE STICKERS": ['
si = text.find(start_token)
if si == -1:
    print('Could not find SINGLE STICKERS block in manifest')
    raise SystemExit(1)

# find closing bracket of that array by searching from si
ai = text.find(']', si)
if ai == -1:
    print('Malformed manifest — could not find end of SINGLE STICKERS array')
    raise SystemExit(1)

block = text[si:ai+1]

# Replace each outputs/SINGLE STICKERS/..._full.jpg with .png if file exists
replaced = 0

def replace_match(m):
    global replaced
    s = m.group(0)
    jpg_path = s.strip('"')
    candidate = Path(jpg_path)
    png_candidate = candidate.with_suffix('.png')
    if png_candidate.exists():
        replaced += 1
        return '"' + str(png_candidate).replace('\\','/') + '"'
    return s

new_block = re.sub(r'"outputs/SINGLE STICKERS/[^"]+?_full\.(jpg|jpeg)"', replace_match, block)
if replaced > 0:
    new_text = text[:si] + new_block + text[ai+1:]
    MANIFEST.write_text(new_text, encoding='utf-8')
    print('Updated manifest, replaced', replaced, 'entries to .png')
else:
    print('No corresponding PNGs found; manifest unchanged')
