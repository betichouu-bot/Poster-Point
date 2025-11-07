"""
Force-split split posters into three horizontal slices (rows) and paste onto template 011.jpg.

This script always uses horizontal slicing (three stacked rows) regardless of
original orientation. Outputs go to `outputs/SPLIT_POSTERS_HORIZONTAL/`.

Usage:
  python scripts/process_slide_posters_force_horizontal.py [--spacing N] [--scale F] [--x-offset X]
"""
from PIL import Image
import os
import sys
import argparse
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_HORIZONTAL')

os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--x-offset', type=int, default=0, help='Horizontal offset to paste onto template')
parser.add_argument('--spacing', type=int, default=12, help='Spacing between rows (px)')
parser.add_argument('--scale', type=float, default=0.6, help='Scale of composed column relative to template height (0-1)')
parser.add_argument('--max-width', type=int, default=None, help='Max width for each row (optional)')
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
    orientation = 'forced-horizontal'
    # horizontal rows always
    row_h = h // 3
    slices = []
    for i in range(3):
        top = i * row_h
        bottom = (i + 1) * row_h if i < 2 else h
        slice_img = img.crop((0, top, w, bottom))
        slices.append(slice_img)

    print(f"{name}: orientation={orientation}, original_size={w}x{h}")

    # Determine target composed height
    target_height = int(template.height * args.scale)
    spacing_total = args.spacing * 2
    row_target_h = (target_height - spacing_total) // 3

    resized_rows = []
    max_row_w = 0
    for s in slices:
        sw, sh = s.size
        new_h = row_target_h
        new_w = int(sw * (new_h / sh)) if sh > 0 else sw
        if args.max_width and new_w > args.max_width:
            factor = args.max_width / new_w
            new_w = args.max_width
            new_h = int(new_h * factor)
        resized = s.resize((new_w, new_h), Image.LANCZOS)
        resized_rows.append(resized)
        if new_w > max_row_w:
            max_row_w = new_w

    # Compose stacked rows
    composed_w = max_row_w
    composed_h = sum(im.height for im in resized_rows) + args.spacing * 2
    composed = Image.new('RGBA', (composed_w, composed_h), (255,255,255,0))

    y = 0
    for i, im in enumerate(resized_rows):
        # center each row horizontally within composed width
        x = (composed_w - im.width)//2
        composed.paste(im, (x, y), im)
        y += im.height
        if i < 2:
            y += args.spacing

    out = template.copy()
    paste_x = args.x_offset if args.x_offset else (template.width - composed.width)//2
    paste_y = (template.height - composed.height)//2

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
            'x_offset': int(args.x_offset)
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

print('Done. Processed', len(img_names), 'images into horizontal triptychs.')
