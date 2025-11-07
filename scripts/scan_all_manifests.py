#!/usr/bin/env python3
"""
Scan all JS manifest files under `js/manifest*.js` for duplicate entries per category.
This script attempts to parse two formats:
 - a static manifest where window.imageCatalog = { ... } (JSON)
 - per-category assignments like window.imageCatalog['CAT'] = [ 'a', 'b', ... ];

Usage: python scripts/scan_all_manifests.py
"""
import re, json, sys, os, glob
from pathlib import Path

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
MANIFEST_GLOB = ROOT / 'js' / 'manifest*.js'

files = sorted(glob.glob(str(MANIFEST_GLOB)))
if not files:
    print('No manifest files found matching', MANIFEST_GLOB)
    sys.exit(1)

any_issues = False
for f in files:
    print('\nScanning', f)
    txt = open(f, 'r', encoding='utf-8').read()
    # First, try to extract window.imageCatalog = { ... } JSON
    m = re.search(r'window\.imageCatalog\s*=\s*(\{[\s\S]*?\})\s*;', txt)
    data = None
    if m:
        try:
            data = json.loads(m.group(1))
            print('  Parsed full imageCatalog JSON with', len(data.keys()), 'categories')
        except Exception as e:
            print('  Failed to parse JSON from', f, '-', e)
            data = None
    if data is None:
        # Try to extract per-category assignments like window.imageCatalog['CAT'] = [ ... ];
        data = {}
        # regex to find window.imageCatalog['CAT']= [ ... ] or window.imageCatalog["CAT"] = [ ... ]
        for m2 in re.finditer(r"window\.imageCatalog\s*\[\s*(['\"])(.*?)\1\s*\]\s*=\s*\[([\s\S]*?)\]\s*;", txt):
            cat = m2.group(2)
            arr_text = m2.group(3)
            # find all quoted strings inside arr_text
            items = re.findall(r"(['\"])(.*?)\1", arr_text)
            items = [t[1] for t in items]
            data[cat] = items
        if data:
            print('  Parsed', len(data.keys()), 'categories from per-category assignments')
    # If still empty, try to find any occurrences of window.imageCatalog['CAT'] push patterns
    if not data:
        # find statements like window.imageCatalog.CAT = window.imageCatalog.CAT || [];
        print('  Could not parse structured manifest from', f)
        continue

    # Now scan for duplicates per category
    file_issues = False
    for cat in sorted(data.keys()):
        items = data[cat] or []
        seen = set()
        dups = []
        for it in items:
            if it in seen:
                dups.append(it)
            else:
                seen.add(it)
        if dups:
            file_issues = True
            any_issues = True
            print(f'  Category: {cat} — {len(dups)} duplicate(s)')
            for d in dups:
                print('    ', d)
    if not file_issues:
        print('  No duplicates found in this manifest.')

if any_issues:
    print('\nOne or more manifests contained duplicates')
    sys.exit(2)
else:
    print('\nAll manifests scanned — no duplicates found')
    sys.exit(0)
