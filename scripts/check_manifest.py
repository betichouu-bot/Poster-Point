import json, re, sys
p='js/manifest.static.js'
s=open(p,'r',encoding='utf8').read()
m=re.search(r'window.imageCatalog\s*=\s*(\{[\s\S]*?\})\s*;',s)
if not m:
    print('FAILED: could not extract JSON')
    sys.exit(1)
js=m.group(1)
cat=json.loads(js)
problems=[]
for k,arr in cat.items():
    for i,entry in enumerate(arr):
        if not isinstance(entry,str):
            problems.append((k,i,entry))
poster_count=0
for k,arr in cat.items():
    if k in ('BOOKMARK','FULLPAGE','SINGLE STICKERS'):
        continue
    poster_count+=len(arr)
print('Poster categories counted:', ', '.join([k for k in cat.keys() if k not in ('BOOKMARK','FULLPAGE','SINGLE STICKERS')]))
print('Total posters entries (catalog):', poster_count)
print('Non-string manifest entries found:', len(problems))
if problems:
    for p in problems[:10]:
        print('  problem:',p)
