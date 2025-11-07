#!/usr/bin/env python3
"""
Create room-style mockups by placing each already-generated mockup onto a
programmatically created room scene (wall, monitor, desk, lamp silhouette).

This is a fast approximation of the photographic mockup and doesn't require
an external background image.

Usage:
  python scripts/generate_room_mockups_from_mockups.py

Outputs:
    outputs/SPLIT POSTERS_ROOM/<base>_room.jpg
"""
import os
import sys
import glob
from PIL import Image, ImageDraw, ImageFilter


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def wall_gradient(size, top=(250,245,238), bottom=(230,220,200)):
    w, h = size
    base = Image.new('RGB', size, top)
    draw = ImageDraw.Draw(base)
    for i in range(h):
        t = i / float(h)
        r = int(top[0] * (1-t) + bottom[0] * t)
        g = int(top[1] * (1-t) + bottom[1] * t)
        b = int(top[2] * (1-t) + bottom[2] * t)
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    return base


def add_monitor_and_desk(img, monitor_width_ratio=0.9):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    # monitor
    mon_w = int(w * monitor_width_ratio)
    mon_h = int(h * 0.18)
    mon_x = (w - mon_w) // 2
    mon_y = int(h * 0.42)
    draw.rectangle([mon_x, mon_y, mon_x+mon_w, mon_y+mon_h], fill=(12,12,12))
    # monitor stand
    stand_w = int(mon_w * 0.08)
    stand_h = int(mon_h * 0.22)
    sx = mon_x + (mon_w - stand_w)//2
    sy = mon_y + mon_h
    draw.rectangle([sx, sy, sx+stand_w, sy+stand_h], fill=(50,50,50))
    # desk
    desk_h = int(h * 0.14)
    desk_top = h - desk_h
    draw.rectangle([0, desk_top, w, h], fill=(70,60,50))
    return img


def add_lamp_and_shade(img):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    # lamp arm simple
    arm_x = int(w * 0.78)
    arm_y = int(h * 0.12)
    draw.line([(arm_x, arm_y), (arm_x+120, arm_y+220)], fill=(40,40,40), width=10)
    # lamp head
    head_box = (arm_x+90, arm_y+200, arm_x+210, arm_y+260)
    draw.ellipse(head_box, fill=(30,30,30))
    return img


def soft_shadow(bg, bbox, blur=22, intensity=100):
    w, h = bg.size
    shadow = Image.new('RGBA', (w, h), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = bbox
    sd.ellipse([x0, y1 - (y1-y0)//6, x1, y1 + (y1-y0)//6], fill=(0,0,0,intensity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(bg.convert('RGBA'), shadow)


def compose(mockup_path, out_path, size=(1200,1800)):
    bg = wall_gradient(size)
    bg = add_monitor_and_desk(bg)
    bg = add_lamp_and_shade(bg)

    mock = Image.open(mockup_path).convert('RGBA')
    # resize mockup to ~60% width
    mw = int(size[0] * 0.6)
    mw_h = int(mock.size[1] * (mw / mock.size[0]))
    mock_resized = mock.resize((mw, mw_h), Image.LANCZOS)

    x = (size[0] - mw)//2
    y = int(size[1] * 0.08)

    # add shadow under mock
    composed = bg.convert('RGBA')
    composed = soft_shadow(composed, (x, y, x+mw, y+mw_h), blur=24, intensity=120)

    composed.paste(mock_resized, (x, y), mock_resized)
    out = composed.convert('RGB')
    ensure_dir(os.path.dirname(out_path))
    out.save(out_path, quality=92)


def main():
    input_dir = os.path.join(os.getcwd(), 'outputs', 'SPLIT POSTERS_MOCKUPS')
    output_dir = os.path.join(os.getcwd(), 'outputs', 'SPLIT POSTERS_ROOM')
    ensure_dir(output_dir)

    patterns = ['*_mockup.jpg', '*_mockup.jpeg', '*_mockup.png']
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(input_dir, p)))
    files = sorted(files)

    if not files:
        print('No mockup files found in', input_dir)
        return 1

    count = 0
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        out_name = base.replace('_triptych_mockup', '_room') + '.jpg'
        out_path = os.path.join(output_dir, out_name)
        print('Compositing', os.path.basename(f), '->', out_name)
        try:
            compose(f, out_path)
            count += 1
        except Exception as e:
            print(' Error composing', f, e)

    print('Done. Generated', count, 'room mockups in', output_dir)


if __name__ == '__main__':
    main()
