#!/usr/bin/env python3
"""
Renumber and rename image outputs per category folder under `outputs/`.
New naming: <FOLDERNAME_NO_SPACES>-NNN<SUFFIX><ext>
  - Folder name uppercased, spaces replaced with underscore
  - NNN is a 3-digit serial starting at 001 per folder
  - SUFFIX is _full, _triptych, or preserved suffix found in filename
Also renames any accompanying .json sidecar and updates paths inside JSON files where possible.

Usage: python scripts/renumber_outputs_by_category.py
"""
import os, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
if not OUT.exists():
    print('No outputs folder found at', OUT)
    raise SystemExit(1)

img_exts = ('.jpg', '.jpeg', '.png', '.webp')
# regex to capture suffix like _full, _triptych, _C_triptych etc.
suffix_re = re.compile(r'(_[a-zA-Z0-9]+(?:_triptych|_full|_rows|_columns|_C_triptych|_triptych_strip)?)', re.IGNORECASE)

mapping = {}

for folder in sorted([p for p in OUT.iterdir() if p.is_dir()]):
    cat = folder.name
    cat_clean = re.sub(r"\s+", '_', cat.strip().upper())
    # collect image-like files (ignore samples subfolder)
    files = [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in img_exts]
    if not files:
        continue
    seq = 1
    for f in files:
        name = f.name
        # determine suffix and extension
        m = suffix_re.search(name)
        if m:
            suffix = m.group(1)
            # normalize suffix to lowercase
            suffix = suffix.lower()
        else:
            # if no recognizable suffix, leave empty
            suffix = ''
        ext = f.suffix.lower()
        new_base = f"{cat_clean}-{seq:03d}{suffix}{ext}"
        new_path = folder / new_base
        # Avoid collision: if new_path exists, increment seq until free
        while new_path.exists():
            seq += 1
            new_base = f"{cat_clean}-{seq:03d}{suffix}{ext}"
            new_path = folder / new_base
        # perform rename
        print(f'Renaming: {f} -> {new_path}')
        f.rename(new_path)
        mapping[str(f.resolve())] = str(new_path.resolve())
        # also handle .json sidecar (same base name but .json)
        side_json_old = folder / (f.stem + '.json')
        if side_json_old.exists():
            side_json_new = folder / (Path(new_base).stem + '.json')
            print(f' Renaming JSON: {side_json_old} -> {side_json_new}')
            side_json_old.rename(side_json_new)
            mapping[str(side_json_old.resolve())] = str(side_json_new.resolve())
            # try updating internal paths in the JSON file
            try:
                txt = side_json_new.read_text(encoding='utf-8')
                for old_abs, new_abs in list(mapping.items()):
                    # replace Windows backslashes with forward slashes in JSON content
                    txt = txt.replace(old_abs.replace('\\','/'), new_abs.replace('\\','/'))
                    txt = txt.replace(old_abs, new_abs)
                side_json_new.write_text(txt, encoding='utf-8')
            except Exception as e:
                print('  Warning: failed to update JSON contents:', e)
        seq += 1

# After all renames, also update any .json files that refer to old absolute paths across outputs
print('\nPost-process: scanning all JSON files to update referenced paths from mapping...')
all_json = list(OUT.rglob('*.json'))
for j in all_json:
    try:
        txt = j.read_text(encoding='utf-8')
        changed = False
        for old_abs, new_abs in mapping.items():
            old_rel = old_abs.replace('\\', '/').replace(str(ROOT.resolve()).replace('\\','/') + '/', '')
            new_rel = new_abs.replace('\\', '/').replace(str(ROOT.resolve()).replace('\\','/') + '/', '')
            if old_rel in txt:
                txt = txt.replace(old_rel, new_rel)
                changed = True
            if old_abs in txt:
                txt = txt.replace(old_abs, new_abs)
                changed = True
        if changed:
            j.write_text(txt, encoding='utf-8')
            print(' Updated json:', j)
    except Exception as e:
        print(' Failed to process json', j, e)

print('\nRenaming complete. Regenerate manifest to apply changes.')
