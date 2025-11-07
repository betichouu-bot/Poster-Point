#!/usr/bin/env python3
"""
Paste full (unsplit) poster images into template `011.jpg` and save to outputs.

Usage:
  python paste_full_template.py [--all] [--limit N]

By default this runs in sample mode and writes up to 5 images per category.
Use --all to process every image.
"""
import os, sys, json
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE = os.path.join(ROOT, '011.jpg')
IMAGES_ROOT = os.path.join(ROOT, 'images', 'PINTEREST IMAGES')
OUT_ROOT = os.path.join(ROOT, 'outputs')

def find_sample_paste_bbox():
    # Search existing outputs jsons for a paste_bbox to reuse; else fallback
    for dirpath, dirnames, filenames in os.walk(OUT_ROOT):
        for fn in filenames:
            if fn.lower().endswith('.json'):
                try:
                    with open(os.path.join(dirpath, fn), 'r', encoding='utf-8') as f:
                        j = json.load(f)
                        if 'paste_bbox' in j:
                            return j['paste_bbox']
                except Exception:
                    continue
    # fallback default (reasonable guess)
    return { 'x': 158, 'y': 151, 'width': 468, 'height': 355 }

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def process_category(cat_dir, real_dir, bbox, limit_per_cat=5, do_all=False, force=False):
    src_dir = os.path.join(IMAGES_ROOT, real_dir)
    if not os.path.isdir(src_dir):
        return 0
    out_dir = os.path.join(OUT_ROOT, real_dir)
    ensure_dir(out_dir)

    files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
    files.sort()
    count = 0
    for i, fn in enumerate(files):
        if not do_all and i >= limit_per_cat:
            break
        base, ext = os.path.splitext(fn)
        out_name = f"{base}_full.jpg"
        out_path = os.path.join(out_dir, out_name)
        meta_path = os.path.join(out_dir, f"{base}_full.json")
        if os.path.exists(out_path) and not force:
            print('Skipping (exists):', out_path)
            count += 1
            continue

        try:
            tpl = Image.open(TEMPLATE).convert('RGB')
            src = Image.open(os.path.join(src_dir, fn)).convert('RGBA')
        except Exception as e:
            print('Failed to open images for', fn, '—', e)
            continue

        # Resize source to fit inside bbox while preserving aspect ratio
        bw, bh = bbox['width'], bbox['height']
        sw, sh = src.size
        scale = min(bw / sw, bh / sh)
        new_w = int(sw * scale)
        new_h = int(sh * scale)
        src_resized = src.resize((new_w, new_h), Image.LANCZOS)

        # Paste onto template centered in bbox
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
                    'mode': 'full_paste'
                }
            }
            with open(meta_path, 'w', encoding='utf-8') as mf:
                json.dump(meta, mf, indent=2)
            print('Wrote:', out_path)
            count += 1
        except Exception as e:
            print('Failed to write output for', fn, '-', e)

    return count

def main():
    do_all = '--all' in sys.argv
    limit = 5
    if '--limit' in sys.argv:
        try:
            limit = int(sys.argv[sys.argv.index('--limit')+1])
        except Exception:
            pass

    bbox = find_sample_paste_bbox()
    print('Using paste bbox:', bbox)

    total = 0
    # iterate categories under images root
    for d in sorted(os.listdir(IMAGES_ROOT)):
        dpath = os.path.join(IMAGES_ROOT, d)
        if not os.path.isdir(dpath):
            continue
        # skip split posters — those are intentionally split into panels
        if d.strip().upper() == 'SPLIT POSTERS':
            continue
        # skip bookmarks and sticker/fullpage categories
        if d.strip().upper() in ('BOOKMARK','SINGLE STICKERS','FULLPAGE'):
            continue

        print('\nProcessing category:', d)
        n = process_category(d, d, bbox, limit_per_cat=limit, do_all=do_all, force='--force' in sys.argv)
        total += n

    print('\nTotal outputs written (or skipped if existed):', total)

if __name__ == '__main__':
    main()
