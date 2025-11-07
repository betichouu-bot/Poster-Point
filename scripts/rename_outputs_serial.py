#!/usr/bin/env python3
"""
Rename all image outputs under `outputs/<CATEGORY>/` to a consistent per-category
naming scheme: <PREFIX>-NNN[_token].ext where PREFIX is detected (from existing
filenames) or derived from the category directory name, and NNN is a 3-digit
serial starting at 001 per category.

The script also renames associated metadata JSON files that share the same stem
(e.g. foo_full.jpg -> foo_full.json).

Usage: python scripts/rename_outputs_serial.py
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / 'outputs'
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}

def derive_prefix_from_dir(name):
    # Take initials of words (letters/digits) up to 3 chars; fall back to first 3 letters
    words = re.findall(r'[A-Za-z0-9]+', name)
    initials = ''.join(w[0] for w in words if w)
    initials = initials.upper()
    if len(initials) >= 2:
        return initials[:3]
    # fallback
    s = re.sub(r'[^A-Za-z0-9]', '', name).upper()
    return (s[:3] or 'X')

# token detection: try to preserve suffix like _full, _triptych, _C_triptych, _rows_rotated_columns, etc
TOKEN_RE = re.compile(r'(_[^._-]*?(?:full|triptych|columns|rows)[^._-]*)$', re.IGNORECASE)
PREFIX_DETECT_RE = re.compile(r'^([A-Z]{1,4})[- _]')

summary = {}

for cat_dir in sorted([d for d in OUT_ROOT.iterdir() if d.is_dir()]):
    cat = cat_dir.name
    files = sorted([p for p in cat_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    if not files:
        continue
    print(f'Processing category: {cat} ({len(files)} images)')

    # Try to detect prefix from filenames
    prefix = None
    for p in files:
        m = PREFIX_DETECT_RE.match(p.stem)
        if m:
            prefix = m.group(1)
            break
    if not prefix:
        prefix = derive_prefix_from_dir(cat)
    print('  Using prefix:', prefix)

    # build mapping old->new
    mapping = []
    used_targets = set()
    counter = 1
    for p in files:
        stem = p.stem
        ext = p.suffix.lower()
        # detect token
        tok_m = TOKEN_RE.search(stem)
        token = tok_m.group(1) if tok_m else ''
        # new name
        new_base = f"{prefix}-{counter:03d}{token}"
        new_name = new_base + ext
        new_path = cat_dir / new_name
        # if target already used (unlikely) increment until free
        while str(new_path).lower() in used_targets or new_path.exists() and new_path not in mapping:
            counter += 1
            new_base = f"{prefix}-{counter:03d}{token}"
            new_name = new_base + ext
            new_path = cat_dir / new_name
        used_targets.add(str(new_path).lower())
        mapping.append((p, new_path))
        counter += 1

    # perform renames safely: if any target collides with a source that will be renamed,
    # first rename sources to temporary names, then to final.
    temp_map = []
    for old, new in mapping:
        if old.samefile(new) if old.exists() and new.exists() else False:
            # same file, skip
            continue
        if new.exists():
            # if target exists (and is different file), move it to a temp to avoid collision
            tmp = new.with_suffix(new.suffix + '.baktmp')
            print('  Backing existing target', new, '->', tmp)
            new.rename(tmp)
            temp_map.append((tmp, new))

    # perform renames old->new
    performed = 0
    for old, new in mapping:
        try:
            if old.exists():
                print('  Rename:', old.name, '->', new.name)
                old.rename(new)
                # also rename associated json metadata if present
                meta_old = cat_dir / (old.stem + '.json')
                if meta_old.exists():
                    meta_new = cat_dir / (new.stem + '.json')
                    print('    Rename meta:', meta_old.name, '->', meta_new.name)
                    meta_old.rename(meta_new)
                performed += 1
        except Exception as e:
            print('    Failed to rename', old, '->', new, e)

    # restore any backed up targets
    for tmp, final in temp_map:
        if tmp.exists():
            print('  Restoring backed file', tmp.name, '->', final.name)
            tmp.rename(final)

    summary[cat] = performed

# Summary
print('\nRename summary:')
for k,v in summary.items():
    print(f'  {k}: {v} files renamed')

# regenerate manifest and scan duplicates
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
