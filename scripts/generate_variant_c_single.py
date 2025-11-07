"""
Generate Variant C for a single source file optionally rotating the source by 180° before splitting.
Saves outputs to outputs/SPLIT_POSTERS with suffix `_C_rows_rotated_columns` (or `_C_rows_rotated_columns_rot180` when rotated).

Usage:
  python scripts/generate_variant_c_single.py --file SP-001.jpeg --spacing 12 --scale 0.6 --rotate-source
"""
from PIL import Image
import os, sys, argparse, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS')
os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--file', required=True, help='filename in source folder')
parser.add_argument('--spacing', type=int, default=12)
parser.add_argument('--scale', type=float, default=0.6)
parser.add_argument('--rotate-source', action='store_true')
args = parser.parse_args()

src_path = os.path.join(SRC_DIR, args.file)
if not os.path.isfile(src_path):
    print('Source not found:', src_path); sys.exit(1)
if not os.path.isfile(TEMPLATE):
    print('Template not found:', TEMPLATE); sys.exit(1)

template = Image.open(TEMPLATE).convert('RGBA')

try:
    img = Image.open(src_path).convert('RGBA')
except Exception as e:
    print('Failed to open', src_path, e); sys.exit(1)

if args.rotate_source:
    img = img.rotate(180, expand=True)

w,h = img.size
row_h = h // 3
rows = []
for i in range(3):
    top = i*row_h
    bottom = (i+1)*row_h if i<2 else h
    rows.append(img.crop((0, top, w, bottom)))

rotated = [r.rotate(90, expand=True) for r in rows]

target_width = int(template.width * args.scale)
spacing = args.spacing
col_target_w = (target_width - spacing*2)//3

resized = []
for r in rotated:
    rw, rh = r.size
    new_w = col_target_w
    new_h = int(rh * (new_w / rw))
    resized.append(r.resize((new_w, new_h), Image.LANCZOS))

from PIL import Image

def compose_columns(slices, spacing):
    max_h = max(im.height for im in slices)
    total_w = sum(im.width for im in slices) + spacing * (len(slices)-1)
    out = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for im in slices:
        out.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing
    return out

composed = compose_columns(resized, spacing)

paste_x = (template.width - composed.width)//2
paste_y = 120

out = template.copy()
try:
    out.paste(composed, (int(paste_x), int(paste_y)), composed)
except Exception:
    out.paste(composed, (int(paste_x), int(paste_y)))

base, ext = os.path.splitext(args.file)
if args.rotate_source:
    out_name = f"{base}_C_rows_rotated_columns_rot180{ext}"
    strip_name = f"{base}_C_rows_rotated_columns_rot180_strip.png"
    meta_name = f"{base}_C_rows_rotated_columns_rot180.json"
else:
    out_name = f"{base}_C_rows_rotated_columns{ext}"
    strip_name = f"{base}_C_rows_rotated_columns_strip.png"
    meta_name = f"{base}_C_rows_rotated_columns.json"

out_path = os.path.join(OUT_DIR, out_name)
out.convert('RGB').save(out_path, quality=92)

strip_path = os.path.join(OUT_DIR, strip_name)
composed.convert('RGBA').save(strip_path)

meta = {
    'source': src_path,
    'output': out_path,
    'strip': strip_path,
    'paste_bbox': {'x': int(paste_x), 'y': int(paste_y), 'width': composed.width, 'height': composed.height},
    'params': {'spacing': spacing, 'scale': args.scale, 'rotated_source_degrees': 180 if args.rotate_source else 0}
}
meta_path = os.path.join(OUT_DIR, meta_name)
with open(meta_path, 'w', encoding='utf-8') as mf:
    json.dump(meta, mf, indent=2)

print('Saved', out_path)
print('Saved strip', strip_path)
print('Saved meta', meta_path)
