"""
Generate combinations of spacing and scale variants for a list of slide-poster IDs.

This script calls the existing `scripts/process_slide_posters.py` for each
    combination of scale and spacing, then copies the produced triptych, strip and
    metadata into a labeled folder `outputs/SPLIT_POSTERS_VARIANTS/<id>/` with
filenames containing the variant parameters.

Usage:
  python scripts/generate_variants_for_ids.py --ids SP-008.jpeg,SP-017.jpeg \ 
       --scales 0.5,0.6,0.7 --spacings 6,12,24
"""
import os
import sys
import argparse
import subprocess
import shutil
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROCESS_SCRIPT = os.path.join(ROOT, 'scripts', 'process_slide_posters.py')
SRC_OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS')
VAR_OUT_DIR = os.path.join(ROOT, 'outputs', 'SPLIT_POSTERS_VARIANTS')


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def run_variant_for_id(idname, scale, spacing, y_offset=150):
    # Call process_slide_posters.py for this id
    cmd = [sys.executable, PROCESS_SCRIPT, '--file', idname, '--scale', str(scale), '--spacing', str(spacing), '--y-offset', str(y_offset)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print('  Error running processor for', idname, 'scale', scale, 'spacing', spacing)
        print(proc.stdout)
        print(proc.stderr)
        return False
    # Now copy produced files from SRC_OUT_DIR to variant folder
    base = os.path.splitext(os.path.basename(idname))[0]
    variant_folder = os.path.join(VAR_OUT_DIR, base)
    ensure_dir(variant_folder)
    # possible extensions
    for ext in ('.jpeg', '.jpg', '.png'):
        src_trip = os.path.join(SRC_OUT_DIR, f"{base}_triptych{ext}")
        if os.path.isfile(src_trip):
            dst_trip = os.path.join(variant_folder, f"{base}_triptych_scale{scale}_spacing{spacing}{ext}")
            shutil.copy2(src_trip, dst_trip)
    # copy strip
    src_strip = os.path.join(SRC_OUT_DIR, f"{base}_triptych_strip.png")
    if os.path.isfile(src_strip):
        dst_strip = os.path.join(variant_folder, f"{base}_triptych_strip_scale{scale}_spacing{spacing}.png")
        shutil.copy2(src_strip, dst_strip)
    # copy json metadata if present
    src_json = os.path.join(SRC_OUT_DIR, f"{base}_triptych.json")
    if os.path.isfile(src_json):
        dst_json = os.path.join(variant_folder, f"{base}_triptych_scale{scale}_spacing{spacing}.json")
        shutil.copy2(src_json, dst_json)
    return True


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', type=str, required=True, help='Comma-separated IDs or filenames')
    parser.add_argument('--scales', type=str, default='0.6', help='Comma-separated scale values, e.g. 0.5,0.6,0.7')
    parser.add_argument('--spacings', type=str, default='12', help='Comma-separated spacing values, e.g. 6,12,24')
    parser.add_argument('--y-offset', type=int, default=150, help='y-offset to pass to processor')
    args = parser.parse_args(argv)

    ids = [s.strip() for s in args.ids.split(',') if s.strip()]
    scales = [float(s.strip()) for s in args.scales.split(',') if s.strip()]
    spacings = [int(s.strip()) for s in args.spacings.split(',') if s.strip()]

    ensure_dir(VAR_OUT_DIR)

    total = 0
    start = time.time()
    for idn in ids:
        for sc in scales:
            for sp in spacings:
                print('Processing', idn, 'scale', sc, 'spacing', sp)
                ok = run_variant_for_id(idn, sc, sp, y_offset=args.y_offset)
                if ok:
                    total += 1

    elapsed = time.time() - start
    print(f'Done. Generated {total} variant sets in {elapsed:.1f}s; variants are under: {VAR_OUT_DIR}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
