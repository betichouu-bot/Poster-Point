"""
Paste a triptych strip image onto the `011.jpg` template at an explicit bbox.

Usage:
  python scripts/paste_strip_at_bbox.py --strip <strip_path> --bbox X Y W H --output <out_path>

It scales the strip to fit the provided bbox width, centers it vertically inside
the bbox, pastes using alpha and writes a JPEG at the output path.
"""
from PIL import Image
import os
import sys
import argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE = os.path.join(ROOT, '011.jpg')

def ensure_dir(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)

def paste_strip(strip_path, bbox, out_path):
    if not os.path.exists(strip_path):
        print('Strip not found:', strip_path)
        return 2
    if not os.path.exists(TEMPLATE):
        print('Template not found:', TEMPLATE)
        return 3

    strip = Image.open(strip_path).convert('RGBA')
    tpl = Image.open(TEMPLATE).convert('RGBA')

    x, y, w, h = bbox
    # scale strip to fit bbox width
    sw, sh = strip.size
    if sw == 0:
        print('Strip width is zero for', strip_path)
        return 4
    new_w = int(w)
    new_h = max(1, int(sh * (new_w / sw)))
    strip_resized = strip.resize((new_w, new_h), Image.LANCZOS)

    paste_x = int(x + (w - new_w) / 2)
    paste_y = int(y + (h - new_h) / 2)

    out = tpl.copy()
    try:
        out.paste(strip_resized, (paste_x, paste_y), strip_resized)
    except Exception:
        out.paste(strip_resized, (paste_x, paste_y))

    ensure_dir(out_path)
    out.convert('RGB').save(out_path, quality=92)
    print('Wrote', out_path)
    return 0

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--strip', required=True)
    parser.add_argument('--bbox', nargs=4, type=int, required=True, help='x y width height')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    return paste_strip(args.strip, args.bbox, args.output)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
