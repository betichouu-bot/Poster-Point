from PIL import Image
import sys
import os

# Paths (project-root absolute paths)
assets_dir = r"C:\Users\Prati\Downloads\poster point - Copy\assets"
src_png = os.path.join(assets_dir, '014.png')
src_jpg = os.path.join(assets_dir, '014.jpg')
dst_png = src_png
dst_favicon = os.path.join(assets_dir, 'favicon.ico')

try:
    # Prefer PNG if present, otherwise fall back to JPG
    if os.path.exists(src_png):
        src = src_png
    elif os.path.exists(src_jpg):
        src = src_jpg
    else:
        raise FileNotFoundError('Neither 014.png nor 014.jpg found in assets/')

    im = Image.open(src)
    im_rgba = im.convert('RGBA')

    # Ensure a PNG copy exists at dst_png (if source was JPG we'll write PNG)
    if src != dst_png:
        im_rgba.save(dst_png, format='PNG')
        print('OK: wrote PNG at', dst_png)
    else:
        print('OK: source PNG already present at', dst_png)

    # Create a multi-size ICO for favicon
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128)]
    im_rgba.save(dst_favicon, format='ICO', sizes=sizes)
    print('OK: favicon.ico written at', dst_favicon)
except Exception as e:
    print('ERROR:', e)
    sys.exit(1)
