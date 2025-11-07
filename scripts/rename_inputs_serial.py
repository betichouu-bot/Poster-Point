#!/usr/bin/env python3
"""
Rename all source images under `images/PINTEREST IMAGES/<CATEGORY>/` to a consistent
per-category naming scheme: <PREFIX>-NNN[_token].ext where PREFIX is derived from
the category directory name (or detected from existing names), and NNN is a 3-digit
serial starting at 001 per category.

Also writes a CSV mapping `rename_map_inputs.csv` at the repo root with old_path,new_path
for audit/undo.

Usage: python scripts/rename_inputs_serial.py
"""
import csv
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_ROOT = ROOT / 'images' / 'PINTEREST IMAGES'
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def derive_prefix_from_dir(name):
    words = re.findall(r'[A-Za-z0-9]+', name)
    initials = ''.join(w[0] for w in words if w)
    initials = initials.upper()
    if len(initials) >= 2:
        return initials[:3]
    s = re.sub(r'[^A-Za-z0-9]', '', name).upper()
    return (s[:3] or 'X')

TOKEN_RE = re.compile(r'(_[^._-]*?(?:full|triptych|columns|rows|c|a)[^._-]*)$', re.IGNORECASE)
PREFIX_DETECT_RE = re.compile(r'^([A-Z]{1,4})[- _]')

mapping_rows = []
summary = {}

if not IN_ROOT.exists():
    print('Input root not found:', IN_ROOT)
    raise SystemExit(1)

for cat_dir in sorted([d for d in IN_ROOT.iterdir() if d.is_dir()]):
    cat = cat_dir.name
    files = sorted([p for p in cat_dir.iterdir() if p.suffix.lower() in IMG_EXTS and p.is_file()])
    if not files:
        continue
    print(f'Processing category: {cat} ({len(files)} images)')

    # detect prefix
    prefix = None
    for p in files:
        m = PREFIX_DETECT_RE.match(p.stem)
        if m:
            prefix = m.group(1)
            break
    if not prefix:
        prefix = derive_prefix_from_dir(cat)
    print('  Using prefix:', prefix)

    counter = 1
    performed = 0
    used_targets = set()

    # build mapping and avoid collisions
    planned = []
    for p in files:
        stem = p.stem
        ext = p.suffix.lower()
        tok_m = TOKEN_RE.search(stem)
        token = tok_m.group(1) if tok_m else ''
        new_base = f"{prefix}-{counter:03d}{token}"
        new_name = new_base + ext
        new_path = cat_dir / new_name
        # avoid collisions with existing names in this dir
        while str(new_path).lower() in used_targets or new_path.exists() and new_path not in planned:
            counter += 1
            new_base = f"{prefix}-{counter:03d}{token}"
            new_name = new_base + ext
            new_path = cat_dir / new_name
        used_targets.add(str(new_path).lower())
        planned.append((p, new_path))
        counter += 1

    # perform safe renames (use temporary renames if needed)
    temp_map = []
    for old, new in planned:
        if old.exists() and new.exists() and not old.samefile(new):
            tmp = new.with_suffix(new.suffix + '.baktmp')
            print('  Backing existing target', new.name, '->', tmp.name)
            new.rename(tmp)
            temp_map.append((tmp, new))

    for old, new in planned:
        try:
            if old.exists():
                print('  Rename:', old.name, '->', new.name)
                old.rename(new)
                mapping_rows.append((str(old.relative_to(ROOT)), str(new.relative_to(ROOT))))
                performed += 1
        except Exception as e:
            print('    Failed to rename', old, '->', new, e)

    for tmp, final in temp_map:
        if tmp.exists():
            print('  Restoring backed file', tmp.name, '->', final.name)
            tmp.rename(final)

    summary[cat] = performed

# write CSV map
csv_path = ROOT / 'rename_map_inputs.csv'
with csv_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['old_path','new_path'])
    for r in mapping_rows:
        writer.writerow(r)

print('\nRename summary:')
for k,v in summary.items():
    print(f'  {k}: {v} files renamed')

print('\nWrote mapping CSV to', csv_path)

# Optionally regenerate manifest and run duplicate scan (manifest uses outputs, but it's harmless)
print('\nRegenerating manifest...')
import subprocess
subp = subprocess.run(['python', str(ROOT / 'scripts' / 'generate_manifest_from_outputs.py')])
if subp.returncode != 0:
    print('Manifest regeneration failed')
else:
    print('Manifest regenerated')

print('Running duplicate scan...')
subp2 = subprocess.run(['python', str(ROOT / 'scripts' / 'scan_manifest_duplicates.py')])
print('Done. exit', subp2.returncode)
