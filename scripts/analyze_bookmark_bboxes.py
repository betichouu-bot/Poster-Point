import json,glob
from collections import Counter
c=Counter()
for fn in glob.glob('outputs/BOOKMARK/*_full.json'):
    try:
        j=json.load(open(fn,encoding='utf-8'))
        bbox= j.get('paste_bbox')
        if bbox:
            # use tuple of values
            c.update([(bbox.get('x'),bbox.get('y'),bbox.get('width'),bbox.get('height'))])
    except Exception as e:
        pass
print('Unique bbox count:', len(c))
for k,v in c.most_common():
    print(v,k)
