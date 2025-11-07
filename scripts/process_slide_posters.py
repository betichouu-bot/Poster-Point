"""
Process split posters: for every image in images/PINTEREST IMAGES/SPLIT POSTERS,
split into 3 equal vertical columns, place them horizontally with spacing,
then paste the composed row onto the template image 011.jpg at a configurable
    y offset (default near the top). Outputs go into outputs/SPLIT_POSTERS/.

Usage (from project root):
  python scripts/process_slide_posters.py [--y-offset Y] [--spacing S] [--scale S]

Options:
  --y-offset Y    vertical coordinate (px) where the composed image will be pasted
  --spacing S     spacing between the three columns in px (default 12)
  --scale S       scale factor for the composed width relative to template width (0-1, default 0.6)

"""
from PIL import Image
import os
import sys
import argparse
import json

# Try to import OpenCV for automatic laptop/screen detection. If not available,
# the script will fall back to manual --y-offset behavior.
try:
        import cv2
        import numpy as np
except Exception:
        cv2 = None
        np = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
TEMPLATE = os.path.join(ROOT, '011.jpg')
OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT POSTERS')

os.makedirs(OUT_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--y-offset', type=int, default=150, help='Vertical offset to paste onto template')
parser.add_argument('--spacing', type=int, default=12, help='Spacing between columns (px)')
parser.add_argument('--scale', type=float, default=0.6, help='Scale of composed row relative to template width (0-1)')
parser.add_argument('--max-height', type=int, default=None, help='Max height for each column (optional)')
parser.add_argument('--auto-detect', action='store_true', help='Auto-detect laptop area on template and paste above it (requires opencv)')
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

# If a single file was requested, filter to that file (allow full filename or basename)
if args.file:
    if args.file in img_names:
        img_names = [args.file]
    else:
        # try to match case-insensitively
        lower_map = {f.lower(): f for f in img_names}
        if args.file.lower() in lower_map:
            img_names = [lower_map[args.file.lower()]]
        else:
            # also allow passing a full path
            candidate = os.path.basename(args.file)
            if candidate in img_names:
                img_names = [candidate]
            else:
                print('Specified file not found in source directory:', args.file)
                sys.exit(1)

if not img_names:
    print('No images found in', SRC_DIR)
    sys.exit(0)

template = Image.open(TEMPLATE).convert('RGBA')


def detect_laptop_bbox(template_path):
    """Attempt to detect a laptop/screen rectangle in the template image.
    Returns (x,y,w,h) in template pixel coordinates or None on failure.
    Requires OpenCV (cv2).
    """
    if cv2 is None:
        return None
    try:
        img = cv2.imdecode(np.fromfile(template_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            # fallback to cv2.imread if imdecode fails
            img = cv2.imread(template_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Blur and edge detect
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        # Dilate to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        edges = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h_img, w_img = gray.shape[:2]
        best = None
        best_area = 0
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            area = w*h
            # ignore tiny contours
            if area < (w_img*h_img)*0.005:
                continue
            aspect = w / float(h) if h>0 else 0
            # laptop screens are usually wider than tall; prefer aspect ratio > 1.2
            if aspect < 1.2:
                continue
            # ignore extremely wide objects (likely background)
            if aspect > 6.0:
                continue
            # prefer larger areas
            if area > best_area:
                best_area = area
                best = (x,y,w,h)

        return best
    except Exception as ex:
        print('Auto-detect failed:', ex)
        return None


# If requested, attempt to auto-detect laptop area on template
detected_laptop = None
if args.auto_detect:
    detected_laptop = detect_laptop_bbox(TEMPLATE)
    if detected_laptop is None:
        print('Auto-detect: no laptop area found or OpenCV not installed; falling back to y-offset')
    else:
        print('Auto-detect: laptop bbox detected at', detected_laptop)

for name in img_names:
    src_path = os.path.join(SRC_DIR, name)
    try:
        img = Image.open(src_path).convert('RGBA')
    except Exception as e:
        print('Failed to open', src_path, e)
        continue

    w, h = img.size
    # Decide splitting strategy based on orientation:
    # - Tall/portrait images: split vertically into 3 columns
    # - Wide/landscape images: split horizontally into 3 rows
    slices = []
    if h > w:
        orientation = 'portrait'
        # vertical columns
        col_w = w // 3
        for i in range(3):
            left = i * col_w
            right = (i + 1) * col_w if i < 2 else w
            slice_img = img.crop((left, 0, right, h))
            slices.append(slice_img)
    else:
        orientation = 'landscape'
        # horizontal rows
        row_h = h // 3
        for i in range(3):
            top = i * row_h
            bottom = (i + 1) * row_h if i < 2 else h
            slice_img = img.crop((0, top, w, bottom))
            slices.append(slice_img)
    print(f"{name}: orientation={orientation}, original_size={w}x{h}")

    # Determine target composed width
    target_width = int(template.width * args.scale)
    spacing_total = args.spacing * 2
    # compute each column target width
    col_target_w = (target_width - spacing_total) // 3

    # Resize slices to same height while fitting width
    # We'll scale by width; maintain aspect ratio
    resized_cols = []
    max_col_h = 0
    for s in slices:
        sw, sh = s.size
        new_w = col_target_w
        new_h = int(sh * (new_w / sw))
        if args.max_height and new_h > args.max_height:
            # scale down to max_height
            factor = args.max_height / new_h
            new_h = args.max_height
            new_w = int(new_w * factor)
        resized = s.resize((new_w, new_h), Image.LANCZOS)
        resized_cols.append(resized)
        if new_h > max_col_h:
            max_col_h = new_h

    # Create composed row image
    composed_w = sum(im.width for im in resized_cols) + args.spacing * 2
    composed_h = max_col_h
    composed = Image.new('RGBA', (composed_w, composed_h), (255,255,255,0))

    # Paste columns centered vertically within composed
    x = 0
    for i, im in enumerate(resized_cols):
        # For the first column, x = 0; after paste, add spacing
        composed.paste(im, (x, (composed_h - im.height)//2), im)
        x += im.width
        if i < 2:
            x += args.spacing

    # Compute paste position: if auto-detect found a laptop bbox, place composed
    # just above the laptop (on the wall). Otherwise use manual y-offset.
    out = template.copy()
    paste_x = (template.width - composed.width)//2
    paste_y = args.y_offset
    if detected_laptop:
        lx, ly, lw, lh = detected_laptop
        margin = 12
        # Target to place composed centered horizontally over laptop, above it.
        paste_x = lx + (lw - composed.width)//2
        paste_y = ly - composed.height - margin
        # If there's not enough room above, place on top edge with small margin
        if paste_y < 8:
            paste_y = max(8, ly + 8)
        # Ensure composed is within template horizontally
        paste_x = max(8, min(paste_x, template.width - composed.width - 8))

    # Paste composed strip onto the template and save output
    base, ext = os.path.splitext(name)
    out_name = f"{base}_triptych{ext}"
    out_path = os.path.join(OUT_DIR, out_name)

    # Paste using alpha channel so transparency is respected
    try:
        out.paste(composed, (int(paste_x), int(paste_y)), composed)
    except Exception:
        # fallback: paste without mask
        out.paste(composed, (int(paste_x), int(paste_y)))

    out.convert('RGB').save(out_path, quality=92)

    # Also save the composed strip image separately for preview/debug
    strip_name = f"{base}_triptych_strip.png"
    strip_path = os.path.join(OUT_DIR, strip_name)
    composed.convert('RGBA').save(strip_path)

    # Write metadata (bounding box where composed was pasted)
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
            'y_offset': int(args.y_offset),
            'auto_detect': bool(args.auto_detect)
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

print('Done. Processed', len(img_names), 'images.')
