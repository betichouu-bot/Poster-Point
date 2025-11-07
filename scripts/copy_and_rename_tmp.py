import os
import shutil
import glob

root = os.getcwd()
src = os.path.join(root, 'outputs', 'SPLIT_POSTERS_MATCH_SP-001')
tmp = os.path.join(root, 'outputs', '_tmp_matchsp1')
os.makedirs(tmp, exist_ok=True)
count = 0
for p in glob.glob(os.path.join(src, '*_triptych_matchSP001.*')):
    base = os.path.basename(p)
    name, ext = os.path.splitext(base)
    newbase = name.replace('_triptych_matchSP001', '_triptych') + ext
    shutil.copy2(p, os.path.join(tmp, newbase))
    count += 1
print(f'Copied {count} files to {tmp}')
