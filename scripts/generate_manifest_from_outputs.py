"""
Generate `js/manifest.static.js` from the files saved in `outputs/*`.
Only include files that look like triptych outputs (contain '_triptych' in name).

This writes `js/manifest.static.js` so the web app can list the generated template images.
"""
import os, json, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_ROOT = os.path.join(ROOT, 'outputs')
IMAGES_ROOT = os.path.join(ROOT, 'images', 'PINTEREST IMAGES')
JS_PATH = os.path.join(ROOT, 'js', 'manifest.static.js')

# Helper: normalize category keys for display and merge duplicates (replace underscores with spaces)
def normalize_cat(name):
    return name.replace('_', ' ').strip()

triptych_re = re.compile(r'_triptych(?:\.(jpg|jpeg|png|webp))$', re.IGNORECASE)
full_re = re.compile(r'_full(?:\.(jpg|jpeg|png|webp))$', re.IGNORECASE)
img_exts = ('.jpg', '.jpeg', '.png', '.webp')

# Build a map of normalized image directories (from images/PINTEREST IMAGES)
images_map = {}
if os.path.isdir(IMAGES_ROOT):
    for d in os.listdir(IMAGES_ROOT):
        dpath = os.path.join(IMAGES_ROOT, d)
        if not os.path.isdir(dpath):
            continue
        images_map[normalize_cat(d)] = d

# Collect entries. Rule: only "SPLIT POSTERS" use outputs triptych files.
catalog = {}

# Build a map of outputs directories by normalized key
# If multiple directories normalize to the same key (e.g. 'SPLIT_POSTERS' and 'SPLIT POSTERS')
# prefer the human-friendly folder (with a space) when present. This avoids nondeterministic
# overwrites caused by filesystem ordering where an underscore-named folder may shadow the
# canonical one.
outputs_map = {}
for out_dir in os.listdir(OUT_ROOT):
    out_path = os.path.join(OUT_ROOT, out_dir)
    if not os.path.isdir(out_path):
        continue
    key = normalize_cat(out_dir)
    # if there's already a candidate, prefer the one that contains a space in its name
    # (e.g. 'SPLIT POSTERS') over underscored variants, otherwise keep the first seen.
    if key in outputs_map:
        existing = outputs_map[key]
        # prefer folder names containing a space (more human/canonical)
        if (' ' in out_dir) and (' ' not in existing):
            outputs_map[key] = out_dir
        # otherwise leave the existing mapping alone
    else:
        outputs_map[key] = out_dir

# 1) For split posters: gather all triptych outputs from any outputs directories that normalize to "SPLIT POSTERS"
slide_dir = outputs_map.get('SPLIT POSTERS')
if slide_dir:
    out_path = os.path.join(OUT_ROOT, slide_dir)
    files = [f for f in os.listdir(out_path)
             if triptych_re.search(f) and '_triptych_strip' not in f.lower()]
    files.sort()
    rel_paths = [os.path.join('outputs', slide_dir, f).replace('\\', '/') for f in files]
    if rel_paths:
        catalog.setdefault('SPLIT POSTERS', [])
        for p in rel_paths:
            if p not in catalog['SPLIT POSTERS']:
                catalog['SPLIT POSTERS'].append(p)

# 2) For all other categories present under images, list original filenames (so they are not split)
for norm_cat, real_dir in images_map.items():
    if norm_cat == 'SPLIT POSTERS' and norm_cat in catalog:
        # already populated from outputs
        continue

    # If we have *_full outputs for this category prefer them
    out_dir = outputs_map.get(norm_cat)
    if out_dir:
        opath = os.path.join(OUT_ROOT, out_dir)
        full_files = [f for f in os.listdir(opath) if full_re.search(f)]
        full_files.sort()
        if full_files:
            rel_paths = [os.path.join('outputs', out_dir, f).replace('\\', '/') for f in full_files]
            catalog[norm_cat] = rel_paths
            continue

    # Otherwise list original filenames so they are not split
    img_dir = os.path.join(IMAGES_ROOT, real_dir)
    files = [f for f in os.listdir(img_dir) if f.lower().endswith(img_exts)]
    files.sort()
    if files:
        # Emit explicit relative paths to the original images so the manifest contains
        # only strings that point to files. This avoids ambiguous bare filenames
        # which can vary by consumer code.
        rels = [os.path.join('images', 'PINTEREST IMAGES', real_dir, f).replace('\\', '/') for f in files]
        catalog[norm_cat] = rels

# Ensure deterministic ordering and remove duplicates while preserving order
for k in sorted(list(catalog.keys())):
    seen = set()
    unique = []
    for v in catalog[k]:
        # Normalize to string path
        if v is None:
            continue
        sv = str(v)
        if sv not in seen:
            seen.add(sv)
            unique.append(sv.replace('\\', '/'))
    catalog[k] = unique

# write manifest.static.js
with open(JS_PATH, 'w', encoding='utf-8') as jf:
    jf.write('// Static manifest generated from outputs folder (SPLIT POSTERS use outputs; others use original images)\n')
    jf.write('window.imageCatalog = ' + json.dumps(catalog, indent=2) + ';\n')
    jf.write("console.info('manifest.static (generated) loaded — categories:', Object.keys(window.imageCatalog).map(c => `${c}:${window.imageCatalog[c].length}`).join(', '));\n")

print('Wrote', JS_PATH)
print('Categories:', ', '.join(sorted(catalog.keys())))
