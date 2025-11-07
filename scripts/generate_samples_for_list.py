"""
Regenerate sample variants (A/B/C) for a specific list of poster numbers.
Usage:
  python scripts/generate_samples_for_list.py --numbers 46,41,39

This will look for files starting with `1 (NUMBER)` in the source folder and
create A_columns, B_rows_stacked and C_rows_rotated_columns variants in
outputs/SPLIT_POSTERS/samples/.
"""
from PIL import Image
import os, sys, argparse, json

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS', 'samples')
os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--numbers', type=str, required=True, help='Comma-separated numbers, e.g. 46,41,39')
parser.add_argument('--spacing', type=int, default=12)
parser.add_argument('--scale', type=float, default=0.6)
parser.add_argument('--auto-detect', action='store_true')
args = parser.parse_args()

nums = [n.strip() for n in args.numbers.split(',') if n.strip()]
if not nums:
    print('No numbers provided'); sys.exit(1)

if not os.path.isdir(SRC_DIR):
    print('Source folder not found', SRC_DIR); sys.exit(1)
if not os.path.isfile(TEMPLATE):
    print('Template not found', TEMPLATE); sys.exit(1)

all_names = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
all_names.sort()

# find matching filenames for given numbers
target_names = []
for n in nums:
    candidates = [f for f in all_names if f.startswith(f'1 ({n})')]
    if not candidates:
        print('Warning: no file found for number', n)
    else:
        target_names.extend(candidates)

if not target_names:
    print('No matching source files found. Exiting.')
    sys.exit(0)

# reuse composition helper functions from generate_samples.py

def detect_laptop_bbox(template_path):
    if cv2 is None:
        return None
    try:
        img = cv2.imdecode(np.fromfile(template_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            img = cv2.imread(template_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        edges = cv2.dilate(edges, kernel, iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h_img, w_img = gray.shape[:2]
        best = None; best_area = 0
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            area = w*h
            if area < (w_img*h_img)*0.005:
                continue
            aspect = w / float(h) if h>0 else 0
            if aspect < 1.2: continue
            if aspect > 6.0: continue
            if area > best_area:
                best_area = area; best = (x,y,w,h)
        return best
    except Exception as e:
        print('Auto-detect failed:', e)
        return None


def compose_columns(slices, spacing):
    max_h = max(im.height for im in slices)
    total_w = sum(im.width for im in slices) + spacing * (len(slices)-1)
    out = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for im in slices:
        out.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing
    return out


def compose_rows_stacked(slices, spacing):
    total_h = sum(im.height for im in slices) + spacing * (len(slices)-1)
    max_w = max(im.width for im in slices)
    out = Image.new('RGBA', (max_w, total_h), (255,255,255,0))
    y = 0
    for im in slices:
        out.paste(im, ((max_w - im.width)//2, y), im)
        y += im.height + spacing
    return out

# detection

detected = None
if args.auto_detect:
    detected = detect_laptop_bbox(TEMPLATE)
    if detected:
        print('Auto-detect: laptop bbox', detected)
    else:
        print('Auto-detect: none')

template = Image.open(TEMPLATE).convert('RGBA')

for name in target_names:
    src = os.path.join(SRC_DIR, name)
    img = Image.open(src).convert('RGBA')
    w,h = img.size
    # vertical columns
    cols = []
    col_w = w // 3
    for i in range(3):
        left = i*col_w
        right = (i+1)*col_w if i<2 else w
        cols.append(img.crop((left,0,right,h)))
    # horizontal rows
    rows = []
    row_h = h // 3
    for i in range(3):
        top = i*row_h
        bottom = (i+1)*row_h if i<2 else h
        rows.append(img.crop((0,top,w,bottom)))

    # prepare target sizes
    target_w = int(template.width * args.scale)
    spacing = args.spacing
    col_target_w = (target_w - spacing*2)//3

    # Variant A
    cols_resized = []
    for s in cols:
        sw, sh = s.size
        new_w = col_target_w
        new_h = int(sh * (new_w / sw))
        cols_resized.append(s.resize((new_w, new_h), Image.LANCZOS))
    composedA = compose_columns(cols_resized, spacing)

    # Variant B
    rows_resized = []
    for r in rows:
        rw, rh = r.size
        factor = target_w / float(rw)
        new_w = int(rw * factor)
        new_h = int(rh * factor)
        rows_resized.append(r.resize((new_w, new_h), Image.LANCZOS))
    composedB = compose_rows_stacked(rows_resized, spacing)

    # Variant C
    rotated = [r.rotate(90, expand=True) for r in rows]
    rot_resized = []
    for r in rotated:
        rw, rh = r.size
        new_w = col_target_w
        new_h = int(rh * (new_w / rw))
        rot_resized.append(r.resize((new_w, new_h), Image.LANCZOS))
    composedC = compose_columns(rot_resized, spacing)

    variants = {'A_columns': composedA, 'B_rows_stacked': composedB, 'C_rows_rotated_columns': composedC}

    if detected:
        lx, ly, lw, lh = detected
        paste_x_center = lx + (lw//2)
    else:
        paste_x_center = template.width//2

    for key, composed in variants.items():
        paste_x = int(paste_x_center - composed.width//2)
        if detected:
            paste_y = detected[1] - composed.height - 12
            if paste_y < 8:
                paste_y = 8
        else:
            paste_y = 120
        out = template.copy()
        try:
            out.paste(composed, (paste_x, paste_y), composed)
        except Exception:
            out.paste(composed, (paste_x, paste_y))
        base, ext = os.path.splitext(name)
        out_name = f"{base}_{key}{ext}"
        out_path = os.path.join(OUT_DIR, out_name)
        out.convert('RGB').save(out_path, quality=92)
        strip_name = f"{base}_{key}_strip.png"
        strip_path = os.path.join(OUT_DIR, strip_name)
        composed.convert('RGBA').save(strip_path)
        meta = {'source': src, 'variant': key, 'output': out_path, 'strip': strip_path, 'paste': {'x': paste_x, 'y': paste_y, 'w': composed.width, 'h': composed.height}, 'params': {'spacing': spacing, 'scale': args.scale}}
        meta_path = os.path.join(OUT_DIR, f"{base}_{key}.json")
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(meta, mf, indent=2)
        print('Saved sample', out_path)

print('Done')
