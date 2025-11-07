"""
Generate Variant C triptych (rows->rotated columns) for given IDs after
rotating the source poster 180 degrees (upside-down), paste onto template
`011.jpg`, and write outputs to the project `outputs/` folder with names
`<ID>_C_triptych_matchSP001.jpg`.

Usage:
  python scripts/generate_C_match_flipped.py --ids SP-018,SP-024
"""
import os
import sys
import argparse
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE = os.path.join(ROOT, '011.jpg')
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
OUT_DIR = os.path.join(ROOT, 'outputs')


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def find_source_path(base):
    # accept base like 'SP-018' or 'SP-018.jpeg'
    candidate = base if base.lower().endswith(('.jpg', '.jpeg', '.png')) else base + '.jpeg'
    p = os.path.join(SRC_DIR, candidate)
    if os.path.isfile(p):
        return p
    # try other extensions
    for ext in ('.jpg', '.jpeg', '.png'):
        p2 = os.path.join(SRC_DIR, base + ext)
        if os.path.isfile(p2):
            return p2
    raise FileNotFoundError('Source image not found for ' + base)


def generate_for_id(idname, scale=0.6, spacing=12):
    base = os.path.splitext(idname)[0]
    src_path = find_source_path(base)
    tpl = Image.open(TEMPLATE).convert('RGBA')

    # Load and rotate 180 (upside-down)
    img = Image.open(src_path).convert('RGBA')
    img = img.rotate(180, expand=True)

    w, h = img.size
    # split into 3 horizontal rows
    row_h = h // 3
    rows = [img.crop((0, i*row_h, w, (i+1)*row_h if i<2 else h)) for i in range(3)]
    # rotate rows to become vertical pieces
    rotated = [r.rotate(90, expand=True) for r in rows]

    target_width = int(tpl.width * scale)
    col_target_w = (target_width - spacing*2)//3

    resized = []
    max_h = 0
    for r in rotated:
        rw, rh = r.size
        new_w = col_target_w
        new_h = int(rh * (new_w / rw)) if rw>0 else rh
        r2 = r.resize((new_w, new_h), Image.LANCZOS)
        resized.append(r2)
        if new_h > max_h:
            max_h = new_h

    # compose columns
    total_w = sum(im.width for im in resized) + spacing*2
    composed = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for i, im in enumerate(resized):
        composed.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing

    paste_x = (tpl.width - composed.width)//2
    paste_y = 120
    out = tpl.copy()
    try:
        out.paste(composed, (int(paste_x), int(paste_y)), composed)
    except Exception:
        out.paste(composed, (int(paste_x), int(paste_y)))

    ensure_dir(OUT_DIR)
    out_name = f"{base}_C_triptych_matchSP001.jpg"
    out_path = os.path.join(OUT_DIR, out_name)
    out.convert('RGB').save(out_path, quality=92)

    # Also save strip for reference
    strip_name = f"{base}_C_triptych_strip.png"
    strip_path = os.path.join(OUT_DIR, strip_name)
    composed.convert('RGBA').save(strip_path)

    print('Wrote', out_path)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', required=True, help='Comma-separated IDs, e.g. SP-018,SP-024')
    parser.add_argument('--scale', type=float, default=0.6)
    parser.add_argument('--spacing', type=int, default=12)
    args = parser.parse_args(argv)

    ids = [s.strip() for s in args.ids.split(',') if s.strip()]
    if not ids:
        print('No ids provided')
        return 1

    for idn in ids:
        try:
            generate_for_id(idn, scale=args.scale, spacing=args.spacing)
        except Exception as e:
            print('Error for', idn, e)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
