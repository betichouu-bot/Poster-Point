#!/usr/bin/env python3
"""
Scan outputs/SPLIT POSTERS for triptych image files and update the
"SPLIT POSTERS" array inside js/manifest.static.js to list only existing
image files.

Usage:
    python scripts/rebuild_split_posters_manifest.py

This script will print a short summary and overwrite js/manifest.static.js
in-place. It makes a single regex-based replacement of the array contents.
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'outputs' / 'SPLIT POSTERS'
MANIFEST = ROOT / 'js' / 'manifest.static.js'

def collect_images():
    exts = {'.jpg', '.jpeg', '.png', '.webp'}
    files = []
    if not OUT_DIR.exists():
        print(f"Error: outputs folder not found: {OUT_DIR}")
        return files
    for p in sorted(OUT_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in exts and 'triptych' in p.name.lower():
            # Use forward slashes in manifest paths for browser compatibility
            rel = os.path.join('outputs', 'SPLIT POSTERS', p.name).replace('\\', '/')
            files.append(rel)
    return files

def build_array_literal(items):
    lines = ['  "SPLIT POSTERS": [']
    for i, it in enumerate(items):
        comma = ',' if i < len(items)-1 else ''
        lines.append(f'    "{it}"{comma}')
    lines.append('  ],')
    return '\n'.join(lines)

def replace_manifest(array_literal):
    txt = MANIFEST.read_text(encoding='utf-8')
    # Replace the SPLIT POSTERS array using a DOTALL regex
    pattern = re.compile(r'("SPLIT POSTERS"\s*:\s*)\[[\s\S]*?\]\s*,', re.MULTILINE)
    if not pattern.search(txt):
        print('Error: could not find "SPLIT POSTERS" array in manifest.static.js')
        return False
    new_txt = pattern.sub(array_literal, txt, count=1)
    MANIFEST.write_text(new_txt, encoding='utf-8')
    return True

def main():
    print('Scanning', OUT_DIR)
    items = collect_images()
    print(f'Found {len(items)} triptych image(s) in outputs/SPLIT POSTERS')
    if len(items) == 0:
        print('No images found — aborting manifest update.')
        return 1
    array_literal = build_array_literal(items)
    ok = replace_manifest(array_literal)
    if ok:
        print('Updated', MANIFEST)
        print('Wrote', len(items), 'entries under "SPLIT POSTERS"')
        # Print first 10 entries as a quick preview
        for e in items[:10]:
            print('  ', e)
        return 0
    else:
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
