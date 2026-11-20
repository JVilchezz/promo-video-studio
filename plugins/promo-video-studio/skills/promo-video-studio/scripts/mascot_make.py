#!/usr/bin/env python3
"""Promo Video Studio · mascot_make.py — an ORIGINAL mascot in the brand's colors, already rigged.

For clients who have no mascot (or want a new one). Pick the shape from what the business IS — never
from a famous character:  cup (coffee, drinks) · box (shop, delivery, app, gift) · phone (apps) ·
blob (friendly, generic) · drop (water, cleaning, health) · bag (store, fashion) · bun (bakery, food)

  python3 mascot_make.py --shape cup --brand brand/brand.json --letter A --out mascot
  python3 mascot_make.py --shape blob --body "#F2C352" --accent "#1F3480" --limb "#3E2618" --out mascot
      [--mouth smile|open|calm] [--no-band] [--no-cheeks] [--size 1024]

→ mascot/mascot.png (full character), mascot/rig_body.png, mascot/rig.json (ready for rig.py animate),
  mascot/sheet.png (4 poses — SHOW IT to the client: it's a proposal, they approve or ask for changes).
Body color: the default (brand light) reads best on dark scenes; for light/paper scenes use --body with a
brand color (e.g. the accent) — the band switches to the dark color automatically.
Then:  python3 rig.py animate mascot/rig.json --preset wave --out assets/m_wave   (and mascot_talk.py to talk)
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FONTS = os.path.join(os.path.dirname(HERE), 'assets', 'fonts')
sys.path.insert(0, HERE)
import rig as R

def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def shade(c, k): return tuple(int(max(0, min(255, v * k))) for v in c)
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def body_shape(shape, W, SS):
    """Return (mask L image at SS scale, body box (x0,y0,x1,y1) in 1x px, extras dict)."""
    S = W * SS; m = Image.new('L', (S, S), 0); d = ImageDraw.Draw(m); cx = W / 2; ex = {}
    def P(pts): return [(x * SS, y * SS) for x, y in pts]
    if shape == 'cup':
        x0, x1, y0, y1 = cx - 175, cx + 175, 300, 700; b0, b1 = cx - 140, cx + 140
        d.polygon(P([(x0, y0), (x1, y0), (b1, y1 - 30), (b0, y1 - 30)]), fill=255)
        d.rounded_rectangle([b0 * SS, (y1 - 90) * SS, b1 * SS, y1 * SS], radius=30 * SS, fill=255)
        ex['lid'] = (x0 - 22, y0 - 70, x1 + 22, y0 + 10); box = (x0, y0, x1, y1)
    elif shape == 'box':
        box = (cx - 190, 290, cx + 190, 700); d.rounded_rectangle([v * SS for v in box], radius=60 * SS, fill=255)
    elif shape == 'phone':
        box = (cx - 160, 230, cx + 160, 710); d.rounded_rectangle([v * SS for v in box], radius=64 * SS, fill=255)
        ex['screen'] = (box[0] + 26, box[1] + 60, box[2] - 26, box[3] - 60)
    elif shape == 'drop':
        pts = []
        for k in range(200):
            u = 2 * math.pi * k / 200; r = 190; x = cx + r * math.sin(u) * (1 - .55 * max(0, math.cos(u)) ** 3)
            y = 520 - r * math.cos(u) * (1.25 if math.cos(u) > 0 else .95); pts.append((x, y))
        d.polygon(P(pts), fill=255); box = (cx - 190, 282, cx + 190, 700)
    elif shape == 'bag':
        box = (cx - 185, 320, cx + 185, 700); d.rounded_rectangle([v * SS for v in box], radius=40 * SS, fill=255)
        ex['handle'] = (cx - 95, 230, cx + 95, 380)
    elif shape == 'bun':
        d.ellipse([(cx - 210) * SS, 300 * SS, (cx + 210) * SS, 700 * SS], fill=255); box = (cx - 210, 300, cx + 210, 700)
        d.rectangle([(cx - 210) * SS, 560 * SS, (cx + 210) * SS, 700 * SS], fill=0)
        d.rounded_rectangle([(cx - 205) * SS, 520 * SS, (cx + 205) * SS, 700 * SS], radius=50 * SS, fill=255)
    else:   # blob
        d.ellipse([(cx - 185) * SS, 265 * SS, (cx + 185) * SS, 705 * SS], fill=255); box = (cx - 185, 265, cx + 185, 705)
    return m, box, ex

def make(a):
    W = a.size; SS = 3; S = W * SS; k = W / 1024
    B = json.load(open(a.brand, encoding='utf-8'))['colors'] if a.brand else {}
    body_c = rgb(a.body or B.get('light') or '#FAF4EC'); acc = rgb(a.accent or B.get('accent') or '#F2C352')
    dark = rgb(a.dark or B.get('dark') or '#1F3480'); limb = rgb(a.limb or '#3E2618')
    if sum(body_c) > 690: body_c = mix(body_c, (255, 255, 255), 0) if a.body else shade(body_c, .97)
    outline = shade(mix(body_c, limb, .55), .8)
    letter_c = dark
    if sum(abs(x - y) for x, y in zip(body_c, acc)) < 90:   # band would vanish on a body of the same color
        acc, letter_c = dark, rgb(B.get('light') or '#FAF4EC')
    mask, box, ex = body_shape(a.shape, 1024, SS)
    if k != 1: mask = mask.resize((S, S), Image.LANCZOS); box = tuple(v * k for v in box); ex = {n: tuple(v * k for v in b) for n, b in ex.items()}
    x0, y0, x1, y1 = box; bw, bh = x1 - x0, y1 - y0; cx = (x0 + x1) / 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def L(v): return v * SS
    if 'handle' in ex:
        h = ex['handle']; d.arc([L(h[0]), L(h[1]), L(h[2]), L(h[3])], 180, 360, fill=dark + (255,), width=int(L(26 * k)))
    # outline + fill
    ol = mask.filter(ImageFilter.MaxFilter(int(7 * k * SS) | 1)); im.paste(outline + (255,), (0, 0), ol); im.paste(body_c + (255,), (0, 0), mask)
    fill = Image.new('RGBA', (S, S), (0, 0, 0, 0)); fd = ImageDraw.Draw(fill)
    if 'screen' in ex:
        s_ = ex['screen']; fd.rounded_rectangle([L(v) for v in s_], radius=L(30 * k), fill=mix(body_c, (255, 255, 255), .55) + (255,))
    if not a.no_band and a.shape not in ('phone',):
        by = y0 + bh * (.62 if a.shape != 'bun' else .7); fd.rectangle([0, L(by), S, L(by + bh * .17)], fill=acc + (255,))
    # soft shading: darker right side + a highlight top-left (depth without gradients that look "AI")
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).ellipse([L(cx + bw * .18), L(y0 - bh * .2), L(cx + bw * 1.1), L(y1 + bh * .2)], fill=70)
    fd.bitmap((0, 0), sh.filter(ImageFilter.GaussianBlur(L(18 * k))), fill=shade(body_c, .55) + (255,))
    hl = Image.new('L', (S, S), 0); ImageDraw.Draw(hl).ellipse([L(x0 + bw * .12), L(y0 + bh * .08), L(x0 + bw * .32), L(y0 + bh * .2)], fill=90)
    fd.bitmap((0, 0), hl.filter(ImageFilter.GaussianBlur(L(10 * k))), fill=(255, 255, 255, 255))
    clip = Image.new('RGBA', (S, S), (0, 0, 0, 0)); clip.paste(fill, (0, 0), Image.fromarray(np.minimum(np.array(fill.split()[3]), np.array(mask)))); im.alpha_composite(clip)
    if 'lid' in ex:
        l_ = ex['lid']; d.rounded_rectangle([L(l_[0]) - L(5 * k), L(l_[1]) - L(5 * k), L(l_[2]) + L(5 * k), L(l_[3]) + L(5 * k)], radius=L(30 * k), fill=shade(dark, .7) + (255,))
        d.rounded_rectangle([L(v) for v in l_], radius=L(26 * k), fill=dark + (255,)); d.rounded_rectangle([L(l_[0] + 60 * k), L(l_[1] - 22 * k), L(l_[2] - 60 * k), L(l_[1] + 20 * k)], radius=L(18 * k), fill=dark + (255,))
    # letter on the band (the brand initial — optional)
    if a.letter and not a.no_band and a.shape != 'phone':
        f = ImageFont.truetype(os.path.join(FONTS, 'anton-latin-400-normal.woff2'), int(L(bh * .15))); by = y0 + bh * (.62 if a.shape != 'bun' else .7)
        bb = d.textbbox((0, 0), a.letter[:2].upper(), font=f); d.text((L(cx) - (bb[2] + bb[0]) / 2, L(by + bh * .085) - (bb[3] + bb[1]) / 2), a.letter[:2].upper(), font=f, fill=letter_c + (255,))
    # face
    fy = y0 + bh * (.36 if a.shape not in ('drop', 'bun') else .48); sp = bw * .2; er = 24 * k; ink = (35, 24, 18)
    if 'screen' in ex: fy = ex['screen'][1] + (ex['screen'][3] - ex['screen'][1]) * .32
    for sx in (-1, 1):
        ex_ = cx + sx * sp; d.ellipse([L(ex_ - er), L(fy - er * 1.25), L(ex_ + er), L(fy + er * 1.25)], fill=ink + (255,))
        d.ellipse([L(ex_ - er * .15), L(fy - er * .9), L(ex_ + er * .5), L(fy - er * .25)], fill=(255, 255, 255, 255))
        if not a.no_cheeks: d.ellipse([L(ex_ + sx * er * .6 - er * 1.05), L(fy + er * 1.55), L(ex_ + sx * er * .6 + er * 1.05), L(fy + er * 2.25)], fill=(232, 120, 110, 120))
    my = fy + er * 1.9
    if a.mouth == 'calm': d.arc([L(cx - 34 * k), L(my - 26 * k), L(cx + 34 * k), L(my + 14 * k)], 20, 160, fill=ink + (255,), width=int(L(8 * k)))
    else:
        mw, mh = (40 * k, 36 * k) if a.mouth == 'open' else (34 * k, 26 * k)
        d.chord([L(cx - mw), L(my - mh), L(cx + mw), L(my + mh)], 0, 180, fill=ink + (255,))
        d.chord([L(cx - mw * .55), L(my + mh * .25), L(cx + mw * .55), L(my + mh * 1.05)], 180, 360, fill=(226, 92, 92, 255))
    body = im.resize((W, W), Image.LANCZOS); os.makedirs(a.out, exist_ok=True); body.save(os.path.join(a.out, 'rig_body.png'))
    # limbs (drawn by rig.py so every pose stays clean)
    th = 22 * k; hand = 21 * k; armL = bh * .42; legL = bh * .27; sh_y = y0 + bh * (.5 if a.shape != 'drop' else .62)
    def edge_x(y, side):   # body edge at height y (from the mask)
        row = np.nonzero(np.array(mask.resize((W, W)))[int(min(W - 1, max(0, y)))] > 128)[0]; return (row.max() if side > 0 else row.min()) if len(row) else cx + side * bw / 2
    parts = []
    for side, n in ((-1, 'arm_l'), (1, 'arm_r')):
        px = edge_x(sh_y, side) - side * th * .9; ang = math.radians(90 - side * 62) if side < 0 else math.radians(90 - 62)
        ang = math.radians(118) if side < 0 else math.radians(62)
        parts.append({'name': n, 'kind': 'arm', 'mode': 'draw', 'pivot': [round(px, 1), round(sh_y, 1)], 'end': [round(px + math.cos(ang) * armL, 1), round(sh_y + math.sin(ang) * armL, 1)],
                      'thick': round(th, 1), 'r_end': round(hand, 1), 'color': '#%02X%02X%02X' % limb, 'z': -1})
    for side, n in ((-1, 'leg_l'), (1, 'leg_r')):
        hx_ = cx + side * bw * .2; hy = y1 - 18 * k
        parts.append({'name': n, 'kind': 'leg', 'mode': 'draw', 'pivot': [round(hx_, 1), round(hy, 1)], 'end': [round(hx_ + side * 14 * k, 1), round(hy + legL, 1)],
                      'thick': round(th * 1.05, 1), 'r_end': round(hand * 1.05, 1), 'color': '#%02X%02X%02X' % limb, 'z': -1})
    rigd = {'image': 'mascot.png', 'body_image': 'rig_body.png', 'body_pivot': [round(cx, 1), round(y1, 1)], 'parts': parts}
    full = R.compose(rigd, body, {}, W, {'arm_l': {'bend': 8}, 'arm_r': {'bend': -8}}, 1.0, np.array(rigd['body_pivot'], float))
    full.save(os.path.join(a.out, 'mascot.png')); json.dump(rigd, open(os.path.join(a.out, 'rig.json'), 'w'), indent=1)
    # proposal sheet: rest + 3 poses
    tiles = [full.resize((360, 360), Image.LANCZOS)]
    for pr, t in (('wave', 1.2), ('point_right', 1.2), ('celebrate', .5)):
        P = R.preset(pr, t, 3.0); tiles.append(R.compose(rigd, body, {}, W, P, 1.0, np.array(rigd['body_pivot'], float)).resize((360, 360), Image.LANCZOS))
    sh_ = Image.new('RGBA', (360 * 4, 360), (250, 246, 240, 255))
    for i, t_ in enumerate(tiles): sh_.alpha_composite(t_, (i * 360, 0))
    sh_.convert('RGB').save(os.path.join(a.out, 'sheet.png'))
    print(json.dumps({'mascot': os.path.join(a.out, 'mascot.png'), 'rig': os.path.join(a.out, 'rig.json'), 'sheet': os.path.join(a.out, 'sheet.png')}))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shape', default='blob', choices=['blob', 'cup', 'box', 'phone', 'drop', 'bag', 'bun']); ap.add_argument('--brand')
    ap.add_argument('--body'); ap.add_argument('--accent'); ap.add_argument('--dark'); ap.add_argument('--limb'); ap.add_argument('--letter')
    ap.add_argument('--mouth', default='smile', choices=['smile', 'open', 'calm']); ap.add_argument('--no-band', action='store_true'); ap.add_argument('--no-cheeks', action='store_true')
    ap.add_argument('--size', type=int, default=1024); ap.add_argument('--out', default='mascot')
    make(ap.parse_args())

if __name__ == '__main__':
    main()
