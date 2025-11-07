"""
Process all SPLIT POSTERS images using variant C (split into 3 horizontal rows,
rotate each 90 degrees, then compose them left->right) and paste onto template
011.jpg. Saves outputs to outputs/SPLIT_POSTERS/ with suffix `_C_triptych`.

Usage:
  python scripts/process_variant_c.py [--auto-detect] [--spacing N] [--scale F]

"""
from PIL import Image
import os, sys, json, argparse

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS')
os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--auto-detect', action='store_true')
parser.add_argument('--spacing', type=int, default=12)
parser.add_argument('--scale', type=float, default=0.6)
args = parser.parse_args()

if not os.path.isdir(SRC_DIR):
    print('Source folder not found:', SRC_DIR); sys.exit(1)
if not os.path.isfile(TEMPLATE):
    print('Template not found:', TEMPLATE); sys.exit(1)

names = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
names.sort()
if not names:
    print('No images'); sys.exit(0)


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
            aspect = w/float(h) if h>0 else 0
            if aspect < 1.2: continue
            if aspect > 6.0: continue
            if area > best_area:
                best_area = area; best = (x,y,w,h)
        return best
    except Exception as e:
        print('Auto-detect failed:', e)
        return None

# detect once
detected = None
if args.auto_detect:
    detected = detect_laptop_bbox(TEMPLATE)
    if detected:
        print('Auto-detect: laptop bbox detected at', detected)
    else:
        print('Auto-detect: no bbox found; will center horizontally and use y offset 120')

template = Image.open(TEMPLATE).convert('RGBA')

def compose_columns(slices, spacing):
    max_h = max(im.height for im in slices)
    total_w = sum(im.width for im in slices) + spacing * (len(slices)-1)
    out = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for i, im in enumerate(slices):
        out.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing
    return out

for name in names:
    src_path = os.path.join(SRC_DIR, name)
    try:
        img = Image.open(src_path).convert('RGBA')
    except Exception as e:
        print('Failed to open', src_path, e); continue

    w,h = img.size
    # split into 3 horizontal rows
    row_h = h // 3
    rows = []
    for i in range(3):
        top = i*row_h
        bottom = (i+1)*row_h if i<2 else h
        rows.append(img.crop((0, top, w, bottom)))

    # rotate rows to become vertical pieces
    rotated = [r.rotate(90, expand=True) for r in rows]

    # compute target composed width based on template
    target_width = int(template.width * args.scale)
    spacing = args.spacing
    col_target_w = (target_width - spacing*2)//3

    resized = []
    for r in rotated:
        rw, rh = r.size
        new_w = col_target_w
        new_h = int(rh * (new_w / rw))
        resized.append(r.resize((new_w, new_h), Image.LANCZOS))

    composed = compose_columns(resized, spacing)

    # paste position
    paste_x = (template.width - composed.width)//2
    paste_y = 120
    if detected:
        lx, ly, lw, lh = detected
        paste_x = lx + (lw - composed.width)//2
        paste_y = ly - composed.height - 12
        if paste_y < 8:
            paste_y = 8
        paste_x = max(8, min(paste_x, template.width - composed.width - 8))

    out = template.copy()
    try:
        out.paste(composed, (int(paste_x), int(paste_y)), composed)
    except Exception:
        out.paste(composed, (int(paste_x), int(paste_y)))

    base, ext = os.path.splitext(name)
    out_name = f"{base}_C_triptych{ext}"
    out_path = os.path.join(OUT_DIR, out_name)
    out.convert('RGB').save(out_path, quality=92)

    strip_name = f"{base}_C_triptych_strip.png"
    strip_path = os.path.join(OUT_DIR, strip_name)
    composed.convert('RGBA').save(strip_path)

    meta = {
        'source': src_path,
        'output': out_path,
        'strip': strip_path,
        'paste_bbox': {'x': int(paste_x), 'y': int(paste_y), 'width': composed.width, 'height': composed.height},
        'params': {'spacing': spacing, 'scale': args.scale, 'auto_detect': bool(args.auto_detect), 'variant': 'C_rows_rotated_columns'}
    }
    meta_path = os.path.join(OUT_DIR, f"{base}_C_triptych.json")
    try:
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(meta, mf, indent=2)
    except Exception as e:
        print('Failed to write meta for', base, e)

    print('Saved', out_path)

print('Done. Processed', len(names), 'images with variant C')
