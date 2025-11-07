#!/usr/bin/env python3
"""
Generate photographic mockups from slide poster triptychs by splitting each
triptych into three vertical panels and pasting them onto a background photo.

Place a background photo in the workspace at `assets/mockup_bg.jpg` (or pass
    --background). The script writes outputs to
    `outputs/SPLIT POSTERS_PHOTO_MOCKUPS/`.

Usage:
  python scripts/generate_photo_mockups_from_triptych.py --background assets/mockup_bg.jpg

Options:
    --input-dir  Folder with `*_triptych.*` files (default: outputs/SPLIT POSTERS)
            --output-dir Destination folder (default: outputs/SPLIT POSTERS_PHOTO_MOCKUPS)
  --background Path to background image (default: assets/mockup_bg.jpg)
  --gap        Gap in px between panels on the background (default: 24)
  --scale      Fraction of background width occupied by the 3 panels combined (default: 0.48)
  --dry-run    Don't write files; only print actions

This intentionally keeps transforms simple (no perspective). It produces a
good-looking photographic mockup similar to your reference by using three
separate panels, small gaps and soft shadows.
"""
import os
import sys
import argparse
import glob
from PIL import Image, ImageDraw, ImageFilter


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def soft_shadow(image_size, bbox, blur=20, opacity=100):
    w, h = image_size
    shadow = Image.new('RGBA', (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = bbox
    # Slightly expand bbox for shadow
    pad_w = max(6, (x1-x0)//20)
    pad_h = max(6, (y1-y0)//20)
    draw.rectangle([x0-pad_w, y1-pad_h, x1+pad_w, y1+pad_h], fill=(0,0,0,opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    return shadow


def process_triptych(trip_path, bg_path, out_path, gap=24, scale=0.48, dry_run=False):
    trip = Image.open(trip_path).convert('RGBA')
    tw, th = trip.size
    panel_w = tw // 3
    panels = [trip.crop((i*panel_w, 0, (i+1)*panel_w, th)) for i in range(3)]

    bg = Image.open(bg_path).convert('RGBA')
    bw, bh = bg.size

    # Target combined width for all panels
    total_w = int(bw * scale)
    panel_target_w = (total_w - 2*gap) // 3

    # Resize panels keeping aspect ratio (height may vary slightly)
    resized = []
    max_panel_h = 0
    for p in panels:
        pw, ph = p.size
        new_h = int(ph * (panel_target_w / pw))
        p2 = p.resize((panel_target_w, new_h), Image.LANCZOS)
        resized.append(p2)
        if new_h > max_panel_h:
            max_panel_h = new_h

    # Vertical position: a bit down from top to match reference
    top_margin = int(bh * 0.08)
    y = top_margin

    # Horizontal start to center the 3 panels
    combined_w = sum(p.size[0] for p in resized) + gap*2
    x0 = (bw - combined_w) // 2

    composed = bg.copy()

    # Draw shadows then panels
    for i, p in enumerate(resized):
        px = x0 + sum(resized[j].size[0] for j in range(i)) + gap * i
        py = y
        # Shadow
        shadow = soft_shadow((bw, bh), (px, py, px + p.size[0], py + p.size[1]), blur=18, opacity=110)
        composed = Image.alpha_composite(composed, shadow)
        composed.paste(p, (px, py), p)

    # Save
    if dry_run:
        print(f"Would write: {out_path}")
        return True

    out = composed.convert('RGB')
    ensure_dir(os.path.dirname(out_path))
    out.save(out_path, quality=92)
    return True


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default=os.path.join(os.getcwd(), 'outputs', 'SPLIT POSTERS'))
    parser.add_argument('--output-dir', default=os.path.join(os.getcwd(), 'outputs', 'SPLIT POSTERS_PHOTO_MOCKUPS'))
    parser.add_argument('--background', default=os.path.join(os.getcwd(), 'assets', 'mockup_bg.jpg'))
    parser.add_argument('--gap', type=int, default=24)
    parser.add_argument('--scale', type=float, default=0.48)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)

    if not os.path.isdir(args.input_dir):
        print('Input folder not found:', args.input_dir)
        return 2
    if not os.path.exists(args.background):
        print('\nBackground image not found:', args.background)
        print('Please place your reference photo in the workspace at the path above, or pass --background <path>')
        print('Example: python scripts/generate_photo_mockups_from_triptych.py --background assets/mockup_bg.jpg')
        return 3

    ensure_dir(args.output_dir)

    patterns = ['*_triptych.jpeg', '*_triptych.jpg', '*_triptych.png']
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(args.input_dir, p)))
    files = sorted(files)

    if not files:
        print('No triptych files found in:', args.input_dir)
        return 0

    written = 0
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        out_name = base + '_photo_mockup.jpg'
        out_path = os.path.join(args.output_dir, out_name)
        print('Processing', os.path.basename(f), '->', out_name)
        try:
            ok = process_triptych(f, args.background, out_path, gap=args.gap, scale=args.scale, dry_run=args.dry_run)
            if ok and not args.dry_run:
                written += 1
        except Exception as e:
            print('  Error:', e)

    print(f'Done. Generated {written} photo mockups in: {args.output_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
