"""
Paste a triptych strip (or generate from a triptych) onto the template `011.jpg`
at the exact bbox taken from a reference triptych metadata (default: SP-001 vertical).

Usage:
  python scripts/paste_strip_to_template.py --ids SP-008.jpeg,SP-017.jpeg ...

Options:
  --ids       Comma-separated basenames or filenames to process (required)
  --ref-id    Reference ID to read paste_bbox from (default: SP-001)
    --ref-dir   Directory containing the reference metadata (default: outputs/SPLIT_POSTERS_VERTICAL)
    --src-dir   Source folder that contains *_triptych_strip.png (default: outputs/SPLIT_POSTERS)
    --out-dir   Destination folder for matched outputs (default: outputs/SPLIT_POSTERS_MATCH_SP-001)

This script will resize each strip to the reference bbox width/height, paste it
onto `011.jpg` at the reference x/y and save the resulting image and metadata.
"""
from PIL import Image
import os
import sys
import argparse
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE = os.path.join(ROOT, '011.jpg')
DEFAULT_REF_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_VERTICAL')
# Many outputs folders use a space in the name; prefer the space variant by default
DEFAULT_SRC_DIR = os.path.join(ROOT, 'outputs', 'SPLIT POSTERS')
DEFAULT_OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_MATCH_SP-001')


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def load_ref_bbox(ref_dir, ref_id):
    # Look for JSON file under ref_dir named <ref_id>_triptych.json
    candidate = os.path.join(ref_dir, f"{ref_id}_triptych.json")
    if not os.path.isfile(candidate):
        raise FileNotFoundError(f"Reference metadata not found: {candidate}")
    with open(candidate, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    bbox = meta.get('paste_bbox')
    if not bbox:
        raise ValueError('paste_bbox missing in reference metadata')
    return bbox


def process_one(basename, src_dir, out_dir, template_path, ref_bbox):
    # Accept either 'SP-008' or 'SP-008.jpeg' as basename
    base = os.path.splitext(os.path.basename(basename))[0]

    strip_path = os.path.join(src_dir, f"{base}_triptych_strip.png")
    if not os.path.isfile(strip_path):
        # try jpg/png triptych image and derive strip by cropping central row
        alt = os.path.join(src_dir, f"{base}_triptych.jpeg")
        if not os.path.isfile(alt):
            alt = os.path.join(src_dir, f"{base}_triptych.jpg")
        if os.path.isfile(alt):
            # use the triptych itself as the strip
            strip_img = Image.open(alt).convert('RGBA')
        else:
            print('  Skipping, no strip or triptych found for', base)
            return False
    else:
        strip_img = Image.open(strip_path).convert('RGBA')

    template = Image.open(template_path).convert('RGBA')

    x = int(ref_bbox['x'])
    y = int(ref_bbox['y'])
    w = int(ref_bbox['width'])
    h = int(ref_bbox['height'])

    # Resize strip to exactly (w,h)
    resized = strip_img.resize((w, h), Image.LANCZOS)

    out = template.copy()
    try:
        out.paste(resized, (x, y), resized)
    except Exception:
        out.paste(resized, (x, y))

    ensure_dir(out_dir)
    out_name = f"{base}_triptych_matchSP001.jpg"
    out_path = os.path.join(out_dir, out_name)
    out.convert('RGB').save(out_path, quality=92)

    # Write metadata
    meta = {
        'source_strip': strip_path,
        'output': out_path,
        'paste_bbox': {'x': x, 'y': y, 'width': w, 'height': h}
    }
    meta_path = os.path.join(out_dir, f"{base}_triptych_matchSP001.json")
    with open(meta_path, 'w', encoding='utf-8') as mf:
        json.dump(meta, mf, indent=2)

    print('Saved match output for', base, '->', out_path)
    return True


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', type=str, required=True, help='Comma-separated IDs or filenames to process')
    parser.add_argument('--ref-id', type=str, default='SP-001', help='Reference ID to copy bbox from')
    parser.add_argument('--ref-dir', default=DEFAULT_REF_DIR)
    parser.add_argument('--bbox', type=str, default=None, help='Optional bbox override as x,y,width,height')
    parser.add_argument('--src-dir', default=DEFAULT_SRC_DIR)
    parser.add_argument('--out-dir', default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    ids = [s.strip() for s in args.ids.split(',') if s.strip()]
    if not ids:
        print('No ids supplied')
        return 1

    ref_bbox = None
    # If a manual bbox was provided, use it (format: x,y,width,height)
    if args.bbox:
        parts = [p.strip() for p in args.bbox.split(',')]
        if len(parts) != 4:
            print('Invalid --bbox format; expected x,y,width,height')
            return 3
        try:
            ref_bbox = {'x': int(parts[0]), 'y': int(parts[1]), 'width': int(parts[2]), 'height': int(parts[3])}
        except Exception as e:
            print('Invalid --bbox numbers:', e)
            return 4
    else:
        try:
            ref_bbox = load_ref_bbox(args.ref_dir, args.ref_id)
        except Exception as e:
            print('Failed to load reference bbox:', e)
            return 2

    for i in ids:
        try:
            process_one(i, args.src_dir, args.out_dir, TEMPLATE, ref_bbox)
        except Exception as e:
            print('Error processing', i, e)

    print('Done.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
