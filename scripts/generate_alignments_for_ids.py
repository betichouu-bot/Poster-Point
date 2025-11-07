"""
Generate alignment and splitting variants for selected slide-poster IDs.

For each provided ID this script will produce:
 - center/top/bottom placement variants (different y-offsets)
 - left/center/right horizontal-offset variants for horizontal composition
 - forced-vertical and forced-horizontal triptychs (copied from existing outputs)
 - variant C (split rows rotated to columns) produced per-ID

Outputs are written to: outputs/SPLIT_POSTERS_ALIGNMENTS/<ID>/ with descriptive filenames.

Usage:
  python scripts/generate_alignments_for_ids.py --ids SP-008,SP-017

Dependencies: Pillow. This script calls existing processor scripts where helpful.
"""
import os
import sys
import argparse
import shutil
import subprocess
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE = os.path.join(ROOT, '011.jpg')
SRC_DIR = os.path.join(ROOT, 'images', 'PINTEREST IMAGES', 'SPLIT POSTERS')
OUT_BASE = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_ALIGNMENTS')
PROC = os.path.join(ROOT, 'scripts', 'process_slide_posters.py')
PROC_V = os.path.join(ROOT, 'scripts', 'process_slide_posters_force_vertical.py')
PROC_H = os.path.join(ROOT, 'scripts', 'process_slide_posters_force_horizontal.py')


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def copy_if_exists(src_paths, dest):
    for p in src_paths:
        if os.path.isfile(p):
            shutil.copy2(p, dest)


def run_cmd(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print('Command failed:', ' '.join(cmd))
        print(proc.stdout)
        print(proc.stderr)
    return proc.returncode == 0


def variant_center_top_bottom(idname, y_offsets, scale=0.6, spacing=12):
    # For each y-offset run the standard processor and copy outputs into a folder
    for y in y_offsets:
        print('  y-offset', y)
        cmd = [sys.executable, PROC, '--file', idname, '--scale', str(scale), '--spacing', str(spacing), '--y-offset', str(y)]
        run_cmd(cmd)
        # copy produced files from outputs/SPLIT_POSTERS
        base = os.path.splitext(idname)[0]
        src_folder = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS')
        dest_folder = os.path.join(OUT_BASE, base)
        ensure_dir(dest_folder)
        # possible extensions
        for ext in ('.jpeg', '.jpg', '.png'):
            src = os.path.join(src_folder, f"{base}_triptych{ext}")
            if os.path.isfile(src):
                dst = os.path.join(dest_folder, f"{base}_triptych_y{y}{ext}")
                shutil.copy2(src, dst)
        strip = os.path.join(src_folder, f"{base}_triptych_strip.png")
        if os.path.isfile(strip):
            shutil.copy2(strip, os.path.join(dest_folder, f"{base}_triptych_strip_y{y}.png"))
        meta = os.path.join(src_folder, f"{base}_triptych.json")
        if os.path.isfile(meta):
            shutil.copy2(meta, os.path.join(dest_folder, f"{base}_triptych_y{y}.json"))


def variant_horizontal_xoffsets(idname, x_offsets, scale=0.6, spacing=12):
    for x in x_offsets:
        print('  x-offset', x)
        cmd = [sys.executable, PROC_H, '--file', idname, '--scale', str(scale), '--spacing', str(spacing), '--x-offset', str(x)]
        run_cmd(cmd)
        base = os.path.splitext(idname)[0]
        src_folder = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_HORIZONTAL')
        dest_folder = os.path.join(OUT_BASE, base)
        ensure_dir(dest_folder)
        for ext in ('.jpeg', '.jpg', '.png'):
            src = os.path.join(src_folder, f"{base}_triptych{ext}")
            if os.path.isfile(src):
                dst = os.path.join(dest_folder, f"{base}_htrip_x{x}{ext}")
                shutil.copy2(src, dst)
        strip = os.path.join(src_folder, f"{base}_triptych_strip.png")
        if os.path.isfile(strip):
            shutil.copy2(strip, os.path.join(dest_folder, f"{base}_htrip_strip_x{x}.png"))
        meta = os.path.join(src_folder, f"{base}_triptych.json")
        if os.path.isfile(meta):
            shutil.copy2(meta, os.path.join(dest_folder, f"{base}_htrip_x{x}.json"))


def copy_vertical(idname):
    base = os.path.splitext(idname)[0]
    src_folder = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_VERTICAL')
    dest_folder = os.path.join(OUT_BASE, base)
    ensure_dir(dest_folder)
    for ext in ('.jpeg', '.jpg', '.png'):
        src = os.path.join(src_folder, f"{base}_triptych{ext}")
        if os.path.isfile(src):
            dst = os.path.join(dest_folder, f"{base}_vtrip{ext}")
            shutil.copy2(src, dst)
    strip = os.path.join(src_folder, f"{base}_triptych_strip.png")
    if os.path.isfile(strip):
        shutil.copy2(strip, os.path.join(dest_folder, f"{base}_vtrip_strip.png"))
    meta = os.path.join(src_folder, f"{base}_triptych.json")
    if os.path.isfile(meta):
        shutil.copy2(meta, os.path.join(dest_folder, f"{base}_vtrip.json"))


def variant_C_for_id(idname, scale=0.6, spacing=12):
    # Implement variant C behavior for a single file (split into rows, rotate, compose)
    base = os.path.splitext(idname)[0]
    src_path = os.path.join(SRC_DIR, idname)
    if not os.path.isfile(src_path):
        print(' source missing for', idname); return
    tpl = Image.open(TEMPLATE).convert('RGBA')
    img = Image.open(src_path).convert('RGBA')
    w,h = img.size
    row_h = h // 3
    rows = [img.crop((0, i*row_h, w, (i+1)*row_h if i<2 else h)) for i in range(3)]
    rotated = [r.rotate(90, expand=True) for r in rows]
    target_width = int(tpl.width * scale)
    col_target_w = (target_width - spacing*2)//3
    resized = []
    max_h = 0
    for r in rotated:
        rw, rh = r.size
        new_w = col_target_w
        new_h = int(rh * (new_w / rw))
        r2 = r.resize((new_w, new_h), Image.LANCZOS)
        resized.append(r2)
        if new_h > max_h: max_h = new_h
    # compose columns
    total_w = sum(im.width for im in resized) + spacing*2
    composed = Image.new('RGBA', (total_w, max_h), (255,255,255,0))
    x = 0
    for i,im in enumerate(resized):
        composed.paste(im, (x, (max_h - im.height)//2), im)
        x += im.width + spacing
    paste_x = (tpl.width - composed.width)//2
    paste_y = 120
    out = tpl.copy()
    try:
        out.paste(composed, (int(paste_x), int(paste_y)), composed)
    except Exception:
        out.paste(composed, (int(paste_x), int(paste_y)))
    dest_folder = os.path.join(OUT_BASE, base)
    ensure_dir(dest_folder)
    out_name = f"{base}_C_triptych_matchSP001.jpg"
    out_path = os.path.join(dest_folder, out_name)
    out.convert('RGB').save(out_path, quality=92)
    strip_name = f"{base}_C_triptych_strip.png"
    composed.convert('RGBA').save(os.path.join(dest_folder, strip_name))
    print(' Saved C-variant for', base)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', required=True, help='Comma-separated IDs or filenames')
    args = parser.parse_args(argv)
    ids = [s.strip() for s in args.ids.split(',') if s.strip()]
    if not ids:
        print('No ids'); return 1
    ensure_dir(OUT_BASE)
    y_offsets = [80, 150, 260]
    x_offsets = [-120, 0, 120]
    for idn in ids:
        print('Processing', idn)
        # center/top/bottom variants
        variant_center_top_bottom(idn, y_offsets)
        # horizontal x-offset variants
        variant_horizontal_xoffsets(idn, x_offsets)
        # copy vertical precomputed
        copy_vertical(idn)
        # variant C per-id
        variant_C_for_id(idn)

    print('Done. Variants under', OUT_BASE)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
