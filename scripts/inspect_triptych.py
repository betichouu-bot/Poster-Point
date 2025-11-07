import sys
from PIL import Image, ImageChops, ImageDraw
import os

if len(sys.argv) < 3:
    print('Usage: python inspect_triptych.py <template> <output> [--debug-save]')
    sys.exit(1)

template_path = sys.argv[1]
output_path = sys.argv[2]
save_debug = '--debug-save' in sys.argv

if not os.path.isfile(template_path):
    print('Template not found:', template_path)
    sys.exit(2)
if not os.path.isfile(output_path):
    print('Output not found:', output_path)
    sys.exit(3)

try:
    tpl = Image.open(template_path).convert('RGB')
    out = Image.open(output_path).convert('RGB')
except Exception as e:
    print('Failed to open images:', e)
    sys.exit(4)

print('Template size:', tpl.size)
print('Output size  :', out.size)

# Ensure same size: if not, try to align by centering smaller one on a canvas of larger
if tpl.size != out.size:
    # we'll create a canvas of the larger size and paste both centered
    W = max(tpl.width, out.width)
    H = max(tpl.height, out.height)
    ct = Image.new('RGB', (W,H), (0,0,0))
    co = Image.new('RGB', (W,H), (0,0,0))
    ct.paste(tpl, ((W - tpl.width)//2, (H - tpl.height)//2))
    co.paste(out, ((W - out.width)//2, (H - out.height)//2))
    tpl = ct
    out = co

# Difference
diff = ImageChops.difference(tpl, out)
bbox = diff.getbbox()
if not bbox:
    print('No differences detected between template and output.')
else:
    print('Difference bbox:', bbox)
    x0,y0,x1,y1 = bbox
    w = x1 - x0
    h = y1 - y0
    print('Diff region: x=%d y=%d w=%d h=%d' % (x0,y0,w,h))

    if save_debug:
        dbg = tpl.copy()
        draw = ImageDraw.Draw(dbg)
        draw.rectangle(bbox, outline='red', width=6)
        dbg_path = os.path.splitext(output_path)[0] + '.debug.jpg'
        dbg.save(dbg_path)
        print('Saved debug image with bbox drawn at', dbg_path)

sys.exit(0)
