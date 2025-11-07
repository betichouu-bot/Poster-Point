from PIL import Image
import os

assets = os.path.join(os.path.dirname(__file__), '..', 'assets')
assets = os.path.abspath(assets)

src = os.path.join(assets, '014.png')
if not os.path.exists(src):
    src = os.path.join(assets, '014.svg')

sizes = {
    'logo-48.png': (48,48),
    'logo-96.png': (96,96),
    'favicon-32.png': (32,32),
    'favicon-64.png': (64,64),
    'apple-touch-180.png': (180,180),
}

print('Using source:', src)

try:
    im = Image.open(src)
    im = im.convert('RGBA')
    for name, size in sizes.items():
        out = os.path.join(assets, name)
        # preserve aspect ratio and pad with transparent background if needed
        thumb = im.copy()
        thumb.thumbnail(size, Image.LANCZOS)
        # Create a transparent background and paste centered
        bg = Image.new('RGBA', size, (0,0,0,0))
        x = (size[0] - thumb.width)//2
        y = (size[1] - thumb.height)//2
        bg.paste(thumb, (x,y), thumb)
        bg.save(out, format='PNG')
        print('Wrote', out)
    print('All icons generated')
except Exception as e:
    print('ERROR', e)
    raise
