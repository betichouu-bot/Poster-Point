"""
Force-split split posters into three vertical columns and paste onto template 011.jpg.

This script is like `process_slide_posters.py` but ALWAYS uses vertical columns
even for landscape images, producing a triptych where each column is a vertical
slice of the original image.

Usage:
  python scripts/process_slide_posters_force_vertical.py [--spacing N] [--scale F] [--y-offset Y]

Outputs are written to `outputs/SPLIT_POSTERS_VERTICAL/` (images, strip PNGs, JSON metadata).
"""
from PIL import Image
import os
import sys
import argparse
import json
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_VERTICAL')

os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--y-offset', type=int, default=150, help='Vertical offset to paste onto template')
parser.add_argument('--spacing', type=int, default=12, help='Spacing between columns (px)')
parser.add_argument('--scale', type=float, default=0.6, help='Scale of composed row relative to template width (0-1)')
parser.add_argument('--max-height', type=int, default=None, help='Max height for each column (optional)')
parser.add_argument('--file', type=str, default=None, help='Optional filename in the source dir to process only that file')
args = parser.parse_args()

if not os.path.isdir(SRC_DIR):
    print('Source folder not found:', SRC_DIR)
    sys.exit(1)
if not os.path.isfile(TEMPLATE):
    print('Template not found:', TEMPLATE)
    sys.exit(1)

img_names = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
img_names.sort()

if args.file:
    candidate = os.path.basename(args.file)
    lower_map = {f.lower(): f for f in img_names}
    if args.file in img_names:
        img_names = [args.file]
    elif args.file.lower() in lower_map:
        img_names = [lower_map[args.file.lower()]]
    elif candidate in img_names:
        img_names = [candidate]
    else:
        print('Specified file not found in source directory:', args.file)
        sys.exit(1)

if not img_names:
    print('No images found in', SRC_DIR)
    sys.exit(0)

template = Image.open(TEMPLATE).convert('RGBA')

for name in img_names:
    src_path = os.path.join(SRC_DIR, name)
    try:
        img = Image.open(src_path).convert('RGBA')
    except Exception as e:
        print('Failed to open', src_path, e)
        continue

    w, h = img.size
    orientation = 'forced-vertical'
    # vertical columns always
    col_w = w // 3
    slices = []
    for i in range(3):
        left = i * col_w
        right = (i + 1) * col_w if i < 2 else w
        slice_img = img.crop((left, 0, right, h))
        slices.append(slice_img)

    print(f"{name}: orientation={orientation}, original_size={w}x{h}")

    # Determine target composed width
    target_width = int(template.width * args.scale)
    spacing_total = args.spacing * 2
    col_target_w = (target_width - spacing_total) // 3

    resized_cols = []
    max_col_h = 0
    for s in slices:
        sw, sh = s.size
        new_w = col_target_w
        new_h = int(sh * (new_w / sw))
        if args.max_height and new_h > args.max_height:
            factor = args.max_height / new_h
            new_h = args.max_height
            new_w = int(new_w * factor)
        resized = s.resize((new_w, new_h), Image.LANCZOS)
        resized_cols.append(resized)
        if new_h > max_col_h:
            max_col_h = new_h

    composed_w = sum(im.width for im in resized_cols) + args.spacing * 2
    composed_h = max_col_h
    composed = Image.new('RGBA', (composed_w, composed_h), (255,255,255,0))

    x = 0
    for i, im in enumerate(resized_cols):
        composed.paste(im, (x, (composed_h - im.height)//2), im)
        x += im.width
        if i < 2:
            x += args.spacing

    out = template.copy()
    paste_x = (template.width - composed.width)//2
    paste_y = args.y_offset

    try:
        out.paste(composed, (int(paste_x), int(paste_y)), composed)
    except Exception:
        out.paste(composed, (int(paste_x), int(paste_y)))

    base, ext = os.path.splitext(name)
    out_name = f"{base}_triptych{ext}"
    out_path = os.path.join(OUT_DIR, out_name)

    out.convert('RGB').save(out_path, quality=92)

    strip_name = f"{base}_triptych_strip.png"
    strip_path = os.path.join(OUT_DIR, strip_name)
    composed.convert('RGBA').save(strip_path)

    metadata = {
        'source': src_path,
        'output': out_path,
        'strip': strip_path,
        'paste_bbox': {
            'x': int(paste_x),
            'y': int(paste_y),
            'width': int(composed.width),
            'height': int(composed.height)
        },
        'orientation': orientation,
        'params': {
            'spacing': int(args.spacing),
            'scale': float(args.scale),
            'y_offset': int(args.y_offset)
        }
    }
    meta_name = f"{base}_triptych.json"
    meta_path = os.path.join(OUT_DIR, meta_name)
    try:
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(metadata, mf, indent=2)
    except Exception as me:
        print('Failed to write metadata for', out_path, me)

    print('Saved', out_path, 'strip->', strip_path, 'meta->', meta_path)

print('Done. Processed', len(img_names), 'images into vertical triptychs.')
