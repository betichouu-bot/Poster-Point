#!/usr/bin/env python3
"""
Paste bookmark and single-sticker images into specified templates.

BOOKMARK category -> template 013.jpg
SINGLE STICKERS category -> template 012.jpg

This processes ALL images in those categories and writes outputs/<CATEGORY>/<base>_full.jpg
and a metadata JSON next to each output.
"""
import os, sys, json
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IMAGES_ROOT = os.path.join(ROOT, 'images', 'PINTEREST IMAGES')
OUT_ROOT = os.path.join(ROOT, 'outputs')
TEMPLATES = {
    'BOOKMARK': os.path.join(ROOT, '013.jpg'),
    'SINGLE STICKERS': os.path.join(ROOT, '012.jpg')
}

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def find_paste_bbox_from_existing(cat):
    # try to reuse paste_bbox from any existing outputs JSON in that category
    out_dir = os.path.join(OUT_ROOT, cat)
    if not os.path.isdir(out_dir):
        return None
    for fn in os.listdir(out_dir):
        if fn.lower().endswith('.json'):
            try:
                with open(os.path.join(out_dir, fn), 'r', encoding='utf-8') as f:
                    j = json.load(f)
                    if 'paste_bbox' in j:
                        return j['paste_bbox']
            except Exception:
                continue
    return None

def process_category(cat):
    tpl_path = TEMPLATES.get(cat)
    if not tpl_path or not os.path.isfile(tpl_path):
        print('Template not found for', cat, tpl_path)
        return 0

    src_dir = os.path.join(IMAGES_ROOT, cat)
    if not os.path.isdir(src_dir):
        print('Source dir not found for', cat)
        return 0

    out_dir = os.path.join(OUT_ROOT, cat)
    ensure_dir(out_dir)

    bbox = find_paste_bbox_from_existing(cat)
    if not bbox:
        # use a sensible default similar to prior scripts
        bbox = { 'x': 158, 'y': 145, 'width': 468, 'height': 361 }

    tpl = Image.open(tpl_path).convert('RGB')

    files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
    files.sort()
    count = 0
    for fn in files:
        base, ext = os.path.splitext(fn)
        out_name = f"{base}_full.jpg"
        out_path = os.path.join(out_dir, out_name)
        meta_path = os.path.join(out_dir, f"{base}_full.json")
        if os.path.exists(out_path):
            # skip existing
            count += 1
            continue

        try:
            src = Image.open(os.path.join(src_dir, fn)).convert('RGBA')
        except Exception as e:
            print('Failed to open', fn, e)
            continue

        bw, bh = bbox['width'], bbox['height']
        sw, sh = src.size
        scale = min(bw / sw, bh / sh)
        new_w = int(sw * scale)
        new_h = int(sh * scale)
        src_resized = src.resize((new_w, new_h), Image.LANCZOS)

        out_img = tpl.copy()
        paste_x = bbox['x'] + (bw - new_w)//2
        paste_y = bbox['y'] + (bh - new_h)//2
        out_img.paste(src_resized.convert('RGB'), (paste_x, paste_y))

        try:
            out_img.save(out_path, quality=92)
            meta = {
                'source': os.path.abspath(os.path.join(src_dir, fn)),
                'output': os.path.abspath(out_path),
                'paste_bbox': bbox,
                'params': {
                    'scale': scale,
                    'template': os.path.basename(tpl_path)
                }
            }
            with open(meta_path, 'w', encoding='utf-8') as mf:
                json.dump(meta, mf, indent=2)
            print('Wrote:', out_path)
            count += 1
        except Exception as e:
            print('Failed to save', out_path, e)

    return count

def main():
    total = 0
    for cat in ('BOOKMARK', 'SINGLE STICKERS'):
        print('\nProcessing', cat)
        n = process_category(cat)
        print('Processed', n, 'items for', cat)
        total += n

    print('\nTotal processed:', total)

if __name__ == '__main__':
    main()
