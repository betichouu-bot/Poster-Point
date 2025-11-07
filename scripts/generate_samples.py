"""
Generate 3 visual variants for the first N images in SPLIT POSTERS so you can
pick the trimming style you prefer.

Variants:
A) Vertical columns: split into 3 vertical columns and compose left->right
B) Horizontal rows stacked: split into 3 horizontal rows and stack top->bottom
C) Rows rotated -> columns: split into 3 horizontal rows, rotate each 90deg, then place left->right

Saves outputs to outputs/SPLIT_POSTERS/samples/

Usage:
  python scripts/generate_samples.py --count 3 --spacing 12 --scale 0.6 --auto-detect

"""
from PIL import Image
import os
import sys
import json
import argparse

# try optional OpenCV
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
parser.add_argument('--count', type=int, default=3, help='How many first images to sample')
parser.add_argument('--spacing', type=int, default=12, help='Spacing between pieces')
parser.add_argument('--scale', type=float, default=0.6, help='Scale of composed strip relative to template width')
parser.add_argument('--auto-detect', action='store_true', help='Try to detect laptop bbox in template')
args = parser.parse_args()

if not os.path.isdir(SRC_DIR):
    print('Source folder not found', SRC_DIR); sys.exit(1)
if not os.path.isfile(TEMPLATE):
    print('Template not found', TEMPLATE); sys.exit(1)

names = [f for f in os.listdir(SRC_DIR) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
names.sort()
if not names:
    print('No images'); sys.exit(0)
names = names[:args.count]


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

# detection
detected = None
if args.auto_detect:
    detected = detect_laptop_bbox(TEMPLATE)
    if detected:
        print('Auto-detect: laptop bbox', detected)
    else:
        print('Auto-detect: none')

def compose_columns(slices, spacing):
    # slices: list of PIL images
    max_h = max(im.height for im in slices)
    total_w = sum(im.width for im in slices) + spacing * (len(slices)-1)
    out = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for i, im in enumerate(slices):
        out.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing
    return out


def compose_rows_stacked(slices, spacing):
    # stack rows top->bottom into a tall image
    total_h = sum(im.height for im in slices) + spacing * (len(slices)-1)
    max_w = max(im.width for im in slices)
    out = Image.new('RGBA', (max_w, total_h), (255,255,255,0))
    y = 0
    for i, im in enumerate(slices):
        out.paste(im, ((max_w - im.width)//2, y), im)
        y += im.height + spacing
    return out

for name in names:
    src = os.path.join(SRC_DIR, name)
    img = Image.open(src).convert('RGBA')
    w,h = img.size
    # prepare slices
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

    # Variant A: columns -> compose horizontally
    # resize columns to target width
    template = Image.open(TEMPLATE).convert('RGBA')
    target_w = int(template.width * args.scale)
    spacing = args.spacing
    # For columns, compute each col target width
    col_target_w = (target_w - spacing*2)//3
    cols_resized = []
    max_col_h = 0
    for s in cols:
        sw, sh = s.size
        new_w = col_target_w
        new_h = int(sh * (new_w / sw))
        resized = s.resize((new_w, new_h), Image.LANCZOS)
        cols_resized.append(resized)
        max_col_h = max(max_col_h, new_h)
    composedA = compose_columns(cols_resized, spacing)

    # Variant B: rows stacked vertically (keep widths, resize rows to target width)
    # We'll scale rows so width == target_w
    rows_resized = []
    max_row_w = 0
    for r in rows:
        rw, rh = r.size
        factor = target_w / float(rw)
        new_w = int(rw * factor)
        new_h = int(rh * factor)
        resized = r.resize((new_w, new_h), Image.LANCZOS)
        rows_resized.append(resized)
        max_row_w = max(max_row_w, new_w)
    composedB = compose_rows_stacked(rows_resized, spacing)

    # Variant C: rows -> rotate 90 deg -> compose horizontally
    rotated = [r.rotate(90, expand=True) for r in rows]
    # resize rotated pieces to column width similar to A
    rot_resized = []
    max_rot_h = 0
    for r in rotated:
        rw, rh = r.size
        new_w = col_target_w
        new_h = int(rh * (new_w / rw))
        resized = r.resize((new_w, new_h), Image.LANCZOS)
        rot_resized.append(resized)
        max_rot_h = max(max_rot_h, new_h)
    composedC = compose_columns(rot_resized, spacing)

    variants = {
        'A_columns': composedA,
        'B_rows_stacked': composedB,
        'C_rows_rotated_columns': composedC
    }

    # decide paste position (use detected if available)
    if detected:
        lx, ly, lw, lh = detected
        margin = 12
        paste_x_center = lx + (lw//2)
    else:
        paste_x_center = template.width//2

    for key, composed in variants.items():
        # center horizontally
        paste_x = int(paste_x_center - composed.width//2)
        # place above laptop if detected else use default y offset near top
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
        # save strip
        strip_name = f"{base}_{key}_strip.png"
        strip_path = os.path.join(OUT_DIR, strip_name)
        composed.convert('RGBA').save(strip_path)
        meta = {
            'source': src,
            'variant': key,
            'output': out_path,
            'strip': strip_path,
            'paste': {'x': paste_x, 'y': paste_y, 'w': composed.width, 'h': composed.height},
            'params': {'spacing': spacing, 'scale': args.scale}
        }
        meta_path = os.path.join(OUT_DIR, f"{base}_{key}.json")
        with open(meta_path, 'w', encoding='utf-8') as mf:
            json.dump(meta, mf, indent=2)
        print('Saved sample', out_path)

print('Done generating samples for', len(names), 'images')
