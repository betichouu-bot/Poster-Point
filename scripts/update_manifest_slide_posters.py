#!/usr/bin/env python3
import json, os, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUTS = ROOT / 'outputs' / 'SPLIT POSTERS'
JS = ROOT / 'js' / 'manifest.static.js'
if not OUTS.exists():
    print('outputs/SPLIT POSTERS not found')
    raise SystemExit(1)
files = sorted([f for f in os.listdir(OUTS) if '_triptych' in f.lower() and f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
rel = [str(Path('outputs')/ 'SPLIT POSTERS' / f).replace('\\','/') for f in files]
# read manifest
s = JS.read_text(encoding='utf-8')
# find window.imageCatalog = <json>;
m = re.search(r'window\.imageCatalog\s*=\s*(\{[\s\S]*\})\s*;\n', s)
if not m:
    print('Could not parse manifest')
    raise SystemExit(1)
obj = json.loads(m.group(1))
obj['SPLIT POSTERS'] = rel
new_js = s[:m.start(1)] + json.dumps(obj, indent=2) + s[m.end(1):]
JS.write_text(new_js, encoding='utf-8')
print('Updated manifest with', len(rel), 'slide poster entries')
