#!/usr/bin/env python3
"""Promo Video Studio · cutout.py — cut an object out of a photo (medal, pin,
trophy, product, logo sign…) by its color, and export:
  • a transparent PNG (upscaled + sharpened for big hero shots)
  • a JS file with its alpha as a data URI, for the .sweep light effect

  python3 cutout.py assets/pin.jpg --hsv 15,38,110,120 --out assets/pin_cut.png --js pin_mask.js
      --hsv  hmin,hmax,smin,vmin  (OpenCV hue 0–180; gold ≈ 15–38, red ≈ 0–10, blue ≈ 100–130)
  python3 cutout.py assets/sign.jpg --color "#2E7D32" --tol 45 --out assets/sign_cut.png

Takes the largest blob of that color and fills its holes (text/engraving inside stays).
Check the result over a dark background with --preview.
"""
import argparse, base64, io, json
import numpy as np, cv2
from PIL import Image, ImageEnhance, ImageFilter

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('--hsv'); ap.add_argument('--color'); ap.add_argument('--tol', type=float, default=45)
    ap.add_argument('--out', default='cutout.png'); ap.add_argument('--js'); ap.add_argument('--var', default='CUTOUT')
    ap.add_argument('--upscale', type=int, default=3); ap.add_argument('--preview', default='cutout_check.jpg'); a = ap.parse_args()
    pil = Image.open(a.image); pil = __import__('PIL.ImageOps', fromlist=['x']).exif_transpose(pil).convert('RGB'); im = np.array(pil)
    if a.hsv:
        h0, h1, s0, v0 = map(int, a.hsv.split(',')); hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
        m = ((hsv[..., 0] >= h0) & (hsv[..., 0] <= h1) & (hsv[..., 1] > s0) & (hsv[..., 2] > v0)).astype(np.uint8) * 255
    elif a.color:
        c = a.color.lstrip('#'); tgt = np.array([[[int(c[i:i + 2], 16) for i in (0, 2, 4)]]], np.uint8)
        lab = cv2.cvtColor(im, cv2.COLOR_RGB2LAB).astype(np.float32); tl = cv2.cvtColor(tgt, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        m = (np.sqrt(((lab - tl) ** 2).sum(-1)) < a.tol).astype(np.uint8) * 255
    else: raise SystemExit('use --hsv or --color')
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: raise SystemExit('nothing found — adjust the color range')
    c = max(cs, key=cv2.contourArea); f = np.zeros_like(m); cv2.drawContours(f, [c], -1, 255, -1)
    f = cv2.morphologyEx(f, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    x, y, w, h = cv2.boundingRect(c); p = 20; box = (max(0, x - p), max(0, y - p), min(im.shape[1], x + w + p), min(im.shape[0], y + h + p))
    crop = ImageEnhance.Color(ImageEnhance.Contrast(pil.crop(box)).enhance(1.1)).enhance(1.06)
    mk = Image.fromarray(f).crop(box).filter(ImageFilter.GaussianBlur(1.2))
    S = a.upscale; crop = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 90, 2))
    mk = mk.resize(crop.size, Image.LANCZOS).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    crop.putalpha(mk); crop.save(a.out)
    bg = Image.new('RGB', crop.size, (10, 31, 92)); bg.paste(crop, (0, 0), crop); bg.thumbnail((700, 700)); bg.save(a.preview)
    info = {'out': a.out, 'size': list(crop.size), 'preview': a.preview}
    if a.js:
        al = mk.resize((max(1, crop.width // 2), max(1, crop.height // 2)), Image.LANCZOS)
        rgba = Image.new('RGBA', al.size, (255, 255, 255, 255)); rgba.putalpha(al); b = io.BytesIO(); rgba.save(b, 'PNG', optimize=True)
        open(a.js, 'w').write(f'window.{a.var}=' + json.dumps({'uri': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()}) + ';\n'); info['js'] = a.js
    print(json.dumps(info))

if __name__ == '__main__':
    main()
