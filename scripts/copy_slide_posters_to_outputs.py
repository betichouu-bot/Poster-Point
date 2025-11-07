#!/usr/bin/env python3
"""
Copy all slide poster images from the images folder to an outputs 'extra' folder.

Usage:
    python scripts/copy_slide_posters_to_outputs.py [--force]

By default the script will skip files that already exist in the destination.
Use --force to overwrite.
"""
import os
import sys
import shutil
import argparse


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=os.path.join(os.getcwd(), "images", "PINTEREST IMAGES", "SPLIT POSTERS"))
    parser.add_argument("--output-dir", default=os.path.join(os.getcwd(), "outputs", "SPLIT POSTERS_EXTRA"))
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in destination")
    args = parser.parse_args(argv)

    src = args.input_dir
    dst = args.output_dir
    if not os.path.isdir(src):
        print("Source folder not found:", src)
        return 2

    os.makedirs(dst, exist_ok=True)

    copied = 0
    skipped = 0
    errors = 0

    for name in sorted(os.listdir(src)):
        if not (name.lower().endswith('.jpg') or name.lower().endswith('.jpeg') or name.lower().endswith('.png')):
            continue
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        try:
            if os.path.exists(d) and not args.force:
                skipped += 1
                print(f"Skipping (exists): {name}")
                continue
            shutil.copy2(s, d)
            copied += 1
            print(f"Copied: {name}")
        except Exception as e:
            errors += 1
            print(f"Error copying {name}: {e}")

    print(f"Done. Copied={copied}, Skipped={skipped}, Errors={errors}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
