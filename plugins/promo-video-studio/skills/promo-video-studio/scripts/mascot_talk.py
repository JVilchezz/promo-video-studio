#!/usr/bin/env python3
"""Promo Video Studio · mascot_talk.py — make a still mascot TALK and BLINK (frame sequence).

From one PNG of the mascot (transparent background is best) it erases the drawn mouth/eyes,
then re-draws an animated mouth (opens/closes like syllables, with tongue) and a blink.
Loop it under a voice-over or a caption, together with a gentle bob.

  python3 mascot_talk.py mascot.png --mouth 584,571:660,557 --eyes 532,547:685,512 \
          --eye-size 37,48 --loop 3.0 --out assets/talk --size 720
  → assets/talk/f_001.png … (RGBA), play with seq('m', t, T0, 'assets/talk', N, 30, true)

--mouth  left corner : right corner of the mouth (pixels in the source image)
--eyes   centers of the two eyes; --eye-size  ellipse radii to erase for the blink
--colors mouth,tongue,lid  hex colors (default dark brown / soft pink / dark brown)
Check the first frame; if the erased area shows a seam, enlarge/shrink --pad.
Other mascot moves (wave, point, enter) need their own frame sequences — ask the client for them
or animate the whole PNG (bob, tilt, squash) with CSS in the page.
"""
import argparse, math, os
import cv2, numpy as np
from PIL import Image, ImageDraw

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def polyfill(arr, mk, seed=1):
    """Fill the masked area with a smooth quadratic surface fitted on the surrounding ring + matching grain."""
    H, W = mk.shape; ring = (cv2.dilate(mk, np.ones((41, 41), np.uint8)) > 0) & (mk == 0)
    rgb = arr[..., :3].astype(float); lum = rgb @ [.3, .59, .11]
    if ring.sum() < 50: return arr
    good = ring & (lum >= np.percentile(lum[ring], 35)) & (arr[..., 3] > 200 if arr.shape[2] == 4 else True)
    ys, xs = np.nonzero(mk); cx, cy, sc = xs.mean(), ys.mean(), max(20, (np.ptp(xs) + np.ptp(ys)) / 2)
    yy, xx = np.mgrid[0:H, 0:W]; X, Y = (xx - cx) / sc, (yy - cy) / sc
    feats = lambda x, y: np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1)
    F = feats(X[good], Y[good]); out = arr.copy(); res = []; inside = mk > 0
    for c in range(3):
        coef, *_ = np.linalg.lstsq(F, rgb[..., c][good], rcond=None); res.append(rgb[..., c][good] - F @ coef)
        out[..., c][inside] = np.clip(feats(X[inside], Y[inside]) @ coef, 0, 255)
    sd = np.std(np.array(res).mean(0)); noise = cv2.GaussianBlur(np.random.default_rng(seed).normal(0, sd * .55, (H, W)), (0, 0), .8)
    soft = cv2.GaussianBlur(inside.astype(float), (0, 0), 2.5)
    for c in range(3): out[..., c] = np.clip(rgb[..., c] * (1 - soft) + (out[..., c].astype(float) + noise * inside) * soft, 0, 255)
    return out.astype(np.uint8)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('--mouth', required=True); ap.add_argument('--eyes')
    ap.add_argument('--eye-size', default='37,48'); ap.add_argument('--pad', type=int, default=14); ap.add_argument('--loop', type=float, default=3.0)
    ap.add_argument('--fps', type=int, default=30); ap.add_argument('--out', default='talk'); ap.add_argument('--size', type=int, default=720)
    ap.add_argument('--colors', default='#321814,#DE7070,#301C12'); ap.add_argument('--blink-at', type=float, default=1.25); a = ap.parse_args()
    A = np.array(Image.open(a.image).convert('RGBA')); H, W = A.shape[:2]
    (lx, ly), (rx, ry) = [tuple(map(float, p.split(','))) for p in a.mouth.split(':')]
    cM, cT, cL = [hexrgb(c) for c in a.colors.split(',')]
    # erase the drawn mouth
    mw = math.hypot(rx - lx, ry - ly); ang = math.atan2(ry - ly, rx - lx); nx, ny = -math.sin(ang), math.cos(ang)
    mk = np.zeros((H, W), np.uint8); mx, my = (lx + rx) / 2, (ly + ry) / 2
    poly = np.array([[lx - a.pad * math.cos(ang), ly - a.pad * math.sin(ang) - a.pad * .6], [rx + a.pad * math.cos(ang), ry + a.pad * math.sin(ang) - a.pad * .6],
                     [rx + nx * mw * .9, ry + ny * mw * .9], [mx + nx * mw * 1.1, my + ny * mw * 1.1], [lx + nx * mw * .9, ly + ny * mw * .9]], np.int32)
    cv2.fillPoly(mk, [poly], 255); mk = cv2.dilate(mk, np.ones((7, 7), np.uint8)); nomouth = polyfill(A, mk)
    noeyes = nomouth
    if a.eyes:
        er = tuple(map(int, a.eye_size.split(','))); eyes = [tuple(map(int, p.split(','))) for p in a.eyes.split(':')]
        mk2 = np.zeros((H, W), np.uint8)
        for c in eyes: cv2.ellipse(mk2, c, er, 0, 0, 360, 255, -1)
        noeyes = polyfill(nomouth, mk2, 2)
    S = 4
    def q(p0, c, p1, n=30): return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]) for u in np.linspace(0, 1, n)]
    def layer(color, mask): lay = Image.new('RGBA', (W, H), color + (255,)); lay.putalpha(mask); return lay
    al = A[..., 3]; ys, xs = np.where(al > 20); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max(), ys.max()
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2; sc = a.size * .83 / max(bx1 - bx0, by1 - by0)
    os.makedirs(a.out, exist_ok=True); N = int(a.loop * a.fps); LP = a.loop
    for i in range(N):
        t = i / a.fps; k = 2 * math.pi * t / LP; env = .25 + .75 * (.5 - .5 * math.cos(k))
        syl = .5 + .5 * math.sin(2 * math.pi * 15 * t / LP) * .8 + .2 * math.sin(2 * math.pi * 7 * t / LP)
        o = max(0., min(1., .12 + 1.15 * env * max(0, syl))); blink = a.eyes and abs(t - a.blink_at) < .07
        im = Image.fromarray(noeyes if blink else nomouth)
        sq = .12 * o; Lc = (lx + (rx - lx) * sq * .5, ly + (ry - ly) * sq * .5); Rc = (rx - (rx - lx) * sq * .5, ry - (ry - ly) * sq * .5)
        mid = ((Lc[0] + Rc[0]) / 2, (Lc[1] + Rc[1]) / 2); d = mw * (.13 + o * 1.45)
        top = q(Lc, (mid[0] + nx * mw * .09, mid[1] + ny * mw * .09), Rc); bot = q(Rc, (mid[0] + nx * d, mid[1] + ny * d), Lc)
        m = Image.new('L', (W * S, H * S), 0); dm = ImageDraw.Draw(m); dm.polygon([(x * S, y * S) for x, y in top + bot], fill=255)
        dm.line([(x * S, y * S) for x, y in top], fill=255, width=int(mw * .09 * S), joint='curve'); mS = m.resize((W, H), Image.LANCZOS)
        im.alpha_composite(layer(cM, mS))
        if o > .3:
            tg = Image.new('L', (W * S, H * S), 0); tc = (mid[0] + nx * d * .42, mid[1] + ny * d * .42); rw = mw * .34 * (.7 + .3 * o); rh = mw * (.08 + o * .26)
            ImageDraw.Draw(tg).ellipse([(tc[0] - rw) * S, (tc[1] - rh * .4) * S, (tc[0] + rw) * S, (tc[1] + rh * 1.2) * S], fill=255)
            tA = np.minimum(np.array(tg.resize((W, H), Image.LANCZOS)), np.array(mS)) * min(1, (o - .3) / .25)
            im.alpha_composite(layer(cT, Image.fromarray(tA.astype(np.uint8))))
        if blink:
            lid = Image.new('L', (W * S, H * S), 0); dl = ImageDraw.Draw(lid); rx_, ry_ = er
            for ex, ey in eyes:
                pts = [((ex + rx_ * .8 * math.cos(u)) * S, (ey + ry_ * .25 + ry_ * .2 * math.sin(u)) * S) for u in np.linspace(.15, math.pi - .15, 30)]
                dl.line(pts, fill=255, width=int(rx_ * .22 * S), joint='curve')
            im.alpha_composite(layer(cL, lid.resize((W, H), Image.LANCZOS)))
        bob = 5 * math.sin(2 * math.pi * 2 * t / LP); rot = 1.0 * math.sin(2 * math.pi * t / LP)
        s = im.resize((int(W * sc), int(H * sc)), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC, center=(cx * sc, cy * sc))
        out = Image.new('RGBA', (a.size, a.size), (0, 0, 0, 0)); out.alpha_composite(s, (int(a.size / 2 - cx * sc), int(a.size / 2 - cy * sc + bob)))
        out.save(f'{a.out}/f_{i + 1:03d}.png')
    print({'frames': N, 'out': a.out})

if __name__ == '__main__':
    main()
