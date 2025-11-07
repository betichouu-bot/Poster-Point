#!/usr/bin/env python3
"""
Paste BOOKMARK images into template `013.jpg` using a supplied bbox (x,y,width,height).
This script will overwrite existing outputs/BOOKMARK/*_full.jpg outputs.

Usage:
  python scripts/paste_bookmarks_with_bbox.py --bbox 158,357,468,149
  python scripts/paste_bookmarks_with_bbox.py --auto    # use detected bbox in outputs/BOOKMARK/detected_bbox.json

"""
import os, sys, json, argparse
from PIL import Image
from pathlib import Path

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
IMAGES_ROOT = ROOT / 'images' / 'PINTEREST IMAGES'
OUT_ROOT = ROOT / 'outputs'
TEMPLATE = ROOT / '013.jpg'


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def parse_bbox(s):
    try:
        parts = [int(x) for x in s.split(',')]
        if len(parts) != 4:
            raise ValueError('bbox must be x,y,width,height')
        return {'x':parts[0],'y':parts[1],'width':parts[2],'height':parts[3]}
    except Exception as e:
        raise argparse.ArgumentTypeError(str(e))


def load_detected():
    p = OUT_ROOT / 'BOOKMARK' / 'detected_bbox.json'
    if not p.exists():
        raise SystemExit('Detected bbox not found: ' + str(p))
    return json.loads(p.read_text(encoding='utf-8'))


def process_bookmarks(bbox):
    if not TEMPLATE.exists():
        print('Template not found:', TEMPLATE)
        return 0
    src_dir = IMAGES_ROOT / 'BOOKMARK'
    if not src_dir.exists():
        print('Source dir not found:', src_dir)
        return 0
    out_dir = OUT_ROOT / 'BOOKMARK'
    ensure_dir(out_dir)

    tpl = Image.open(str(TEMPLATE)).convert('RGB')
    files = [f for f in sorted(os.listdir(src_dir)) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
    count = 0
    for fn in files:
        base, ext = os.path.splitext(fn)
        out_name = f"{base}_full.jpg"
        out_path = out_dir / out_name
        meta_path = out_dir / f"{base}_full.json"

        try:
            src = Image.open(str(src_dir / fn)).convert('RGBA')
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
            out_img.save(str(out_path), quality=92)
            meta = {
                'source': str(src_dir / fn),
                'output': str(out_path),
                'paste_bbox': bbox,
                'params': {
                    'scale': scale,
                    'template': TEMPLATE.name
                }
            }
            meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
            count += 1
        except Exception as e:
            print('Failed to save', out_path, e)

    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox', type=parse_bbox, help='bbox as x,y,width,height')
    parser.add_argument('--auto', action='store_true', help='use detected bbox from outputs/BOOKMARK/detected_bbox.json')
    args = parser.parse_args()

    if args.auto:
        bbox = load_detected()
    elif args.bbox:
        bbox = args.bbox
    else:
        print('Provide --bbox or --auto')
        sys.exit(1)

    print('Using bbox:', bbox)
    n = process_bookmarks(bbox)
    print('Processed', n, 'bookmarks')

if __name__ == '__main__':
    main()
