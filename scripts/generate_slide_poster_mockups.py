#!/usr/bin/env python3
"""
Generate simple room-style mockups for split poster triptychs.

For each `*_triptych.*` in `outputs/SPLIT POSTERS/`, this script creates
a mockup image with a neutral wall background and a soft shadow, and saves
it under `outputs/SPLIT POSTERS_MOCKUPS/` with the same basename + `_mockup.jpg`.

This is intentionally simple so it runs without extra assets. It uses Pillow.
Usage:
  python scripts/generate_slide_poster_mockups.py

Options:
    --input-dir  Path to folder containing triptychs (default: outputs/SPLIT POSTERS)
    --output-dir Path to write mockups (default: outputs/SPLIT POSTERS_MOCKUPS)
  --width      Background width in px (default: 1200)
  --height     Background height in px (default: 1800)
  --bg-color   Background RGB hex or comma list (default: 245,238,226)
  --dry-run    Do not write files; just print what would be done

"""
import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFilter
import glob


def parse_color(s):
    if "," in s:
        parts = [int(p.strip()) for p in s.split(",")]
        return tuple(parts)
    s = s.lstrip("#")
    if len(s) == 6:
        return tuple(int(s[i:i+2], 16) for i in (0,2,4))
    raise ValueError("Invalid color: %r" % s)


def make_shadow(bg_size, bbox, blur_radius=30, opacity=120):
    # Create a blurred ellipse shadow under the pasted poster
    w, h = bg_size
    shadow = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1)//2
    # Slightly wider than poster
    ex0 = x0 + (x1-x0)//10
    ex1 = x1 - (x1-x0)//10
    ey0 = y1 - (y1-y0)//6
    ey1 = y1 + (y1-y0)//6
    draw.ellipse((ex0, ey0, ex1, ey1), fill=(0,0,0,opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    return shadow


def generate_mockup(input_path, output_path, bg_size=(1200,1800), bg_color=(245,238,226)):
    poster = Image.open(input_path).convert("RGBA")

    bg_w, bg_h = bg_size
    bg = Image.new("RGB", (bg_w, bg_h), bg_color)

    # Resize poster to take ~70% of bg width
    max_w = int(bg_w * 0.70)
    w, h = poster.size
    scale = min(1.0, max_w / w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    poster_resized = poster.resize((new_w, new_h), Image.LANCZOS)

    # Position: centered horizontally, top margin
    top_margin = int(bg_h * 0.08)
    x = (bg_w - new_w) // 2
    y = top_margin

    # Add a soft shadow
    shadow = make_shadow((bg_w, bg_h), (x, y, x+new_w, y+new_h), blur_radius=28, opacity=110)
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, shadow)

    # Paste poster
    bg.paste(poster_resized, (x, y), poster_resized)

    # Optionally add a simple desk/monitor silhouette at bottom to resemble the example
    draw = ImageDraw.Draw(bg)
    desk_h = int(bg_h * 0.14)
    desk_top = bg_h - desk_h
    draw.rectangle([0, desk_top, bg_w, bg_h], fill=(55,50,45,255))

    # Convert to RGB and save
    out = bg.convert("RGB")
    out.save(output_path, format="JPEG", quality=92)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=os.path.join(os.getcwd(), "outputs", "SPLIT POSTERS"))
    parser.add_argument("--output-dir", default=os.path.join(os.getcwd(), "outputs", "SPLIT POSTERS_MOCKUPS"))
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--height", type=int, default=1800)
    parser.add_argument("--bg-color", type=str, default="245,238,226")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    input_dir = args.input_dir
    output_dir = args.output_dir
    if not os.path.isdir(input_dir):
        print("Input directory not found:", input_dir)
        return 2

    os.makedirs(output_dir, exist_ok=True)

    patterns = ["*_triptych.jpeg", "*_triptych.jpg", "*_triptych.png"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(input_dir, p)))
    files = sorted(files)

    if not files:
        print("No triptych files found in:", input_dir)
        return 0

    bg_color = parse_color(args.bg_color)
    count = 0
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        out_name = base + "_mockup.jpg"
        out_path = os.path.join(output_dir, out_name)
        print("Processing:", os.path.basename(f), "->", out_name)
        if not args.dry_run:
            try:
                generate_mockup(f, out_path, bg_size=(args.width, args.height), bg_color=bg_color)
                count += 1
            except Exception as e:
                print("  Error processing", f, "->", e)

    print(f"Done. Generated {count} mockups in: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
