#!/usr/bin/env python3
"""
Generate per-image JSON metadata for all images in outputs/SPLIT POSTERS.
Writes <basename>.json next to each image file.
"""
import os
import json
from datetime import datetime
from PIL import Image

ROOT = os.getcwd()
INPUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT POSTERS')

if not os.path.isdir(INPUT_DIR):
    print('Input directory not found:', INPUT_DIR)
    raise SystemExit(2)

EXTS = ('.jpg', '.jpeg', '.png')

files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(EXTS)]
files = sorted(files)

if not files:
    print('No image files found in', INPUT_DIR)
    raise SystemExit(0)

created = 0
for fname in files:
    path = os.path.join(INPUT_DIR, fname)
    try:
        with Image.open(path) as im:
            w, h = im.size
    except Exception as e:
        print('  Skipping (cannot open):', fname, 'error:', e)
        continue

    base = os.path.splitext(fname)[0]
    # Normalize id to base (likely contains spaces/parentheses)
    id_key = base
    created_at = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    meta = {
        'id': id_key,
        'filename': fname,
        'relative_path': os.path.join('outputs', 'SPLIT POSTERS', fname).replace('\\', '/'),
        'category': 'SPLIT POSTERS',
        'type': 'triptych_source',
        'width': w,
        'height': h,
        'created_at': created_at,
        'generator': {
            'script': 'scripts/process_slide_posters.py',
            'notes': 'Generated or copied into outputs; exact generator params not recorded.'
        },
        'tags': [],
        'notes': ''
    }

    outname = base + '.json'
    outpath = os.path.join(INPUT_DIR, outname)
    try:
        with open(outpath, 'w', encoding='utf-8') as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
        print('Wrote', outname)
        created += 1
    except Exception as e:
        print('Error writing', outname, ':', e)

print('\nDone. Wrote', created, 'JSON metadata files to', INPUT_DIR)
