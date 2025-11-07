#!/usr/bin/env python3
"""Scan js/manifest.static.js for duplicate entries per category and report them."""
import re, json, sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MANIFEST = os.path.join(ROOT, 'js', 'manifest.static.js')

if not os.path.isfile(MANIFEST):
    print('Manifest not found at', MANIFEST)
    sys.exit(2)

txt = open(MANIFEST, 'r', encoding='utf-8').read()
# Extract the JSON assigned to window.imageCatalog
m = re.search(r'window\.imageCatalog\s*=\s*(\{.*\})\s*;', txt, flags=re.S)
if not m:
    print('Could not parse manifest JSON from', MANIFEST)
    sys.exit(3)

try:
    data = json.loads(m.group(1))
except Exception as e:
    print('JSON parse error:', e)
    sys.exit(4)

found_any = False
for cat in sorted(data.keys()):
    items = data[cat]
    seen = set()
    dups = []
    for it in items:
        if it in seen:
            dups.append(it)
        else:
            seen.add(it)
    if dups:
        found_any = True
        print(f'Category: {cat} — {len(dups)} duplicate(s)')
        for d in dups:
            print('  ', d)

if not found_any:
    print('No duplicates found in manifest.')

sys.exit(0)
