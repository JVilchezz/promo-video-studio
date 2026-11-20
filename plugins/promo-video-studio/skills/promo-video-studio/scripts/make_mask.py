#!/usr/bin/env python3
"""Promo Video Studio · make_mask.py — build the mask for a PORTAL transition.

Finds a colored shape inside a photo (e.g. the navy letter of a logo painted on a
wall, a neon sign, a colored door) and writes a JS file with a smooth, 2x
supersampled alpha mask as a data URI plus the best point to zoom into.
CSS masks loaded from file:// are blocked by CORS, so the data URI is required.

  python3 make_mask.py assets/stand.jpg --color "#1E2A6E" --tol 60 --box 560,170,1010,770 \
          --out portal_mask.js --preview mask_check.png
  → window.PORTAL = {uri, w, h, tx, ty}

--color : the shape's color (pick it from the photo)    --tol : color distance (30–90)
--box   : optional x0,y0,x1,y1 region to search in      --min-area : ignore specks
Always open --preview: the shape must be fully red and nothing else.
"""
import argparse, base64, io, json
import numpy as np, cv2
from PIL import Image

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('--color', required=True); ap.add_argument('--tol', type=float, default=60)
    ap.add_argument('--box'); ap.add_argument('--min-area', type=int, default=3000); ap.add_argument('--out', default='portal_mask.js')
    ap.add_argument('--preview', default='mask_check.png'); ap.add_argument('--var', default='PORTAL'); a = ap.parse_args()
    im = np.array(Image.open(a.image).convert('RGB')); H, W = im.shape[:2]
    c = a.color.lstrip('#'); tgt = np.array([[[int(c[i:i + 2], 16) for i in (0, 2, 4)]]], np.uint8)
    lab = cv2.cvtColor(im, cv2.COLOR_RGB2LAB).astype(np.float32); tl = cv2.cvtColor(tgt, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    d = np.sqrt(((lab - tl) ** 2).sum(-1)); m = (d < a.tol).astype(np.uint8) * 255
    if a.box:
        x0, y0, x1, y1 = map(int, a.box.split(',')); reg = np.zeros_like(m); reg[y0:y1, x0:x1] = 255; m &= reg
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab_, st, _ = cv2.connectedComponentsWithStats(m); keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i][4] >= a.min_area: keep[lab_ == i] = 255
    inv = 255 - keep; n2, l2, s2, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n2):
        if s2[i][4] < 400: keep[l2 == i] = 255
    if keep.sum() == 0: raise SystemExit('No shape found — adjust --color/--tol/--box')
    # zoom target: thick part of the shape, close to its centroid
    dt = cv2.distanceTransform(keep, cv2.DIST_L2, 5); ys, xs = np.nonzero(keep); cx, cy = xs.mean(), ys.mean()
    score = dt - 0.05 * np.hypot(np.arange(W)[None, :] - cx, np.arange(H)[:, None] - cy); score[keep == 0] = -1e9
    ty, tx = np.unravel_index(score.argmax(), score.shape)
    # smooth 2x supersampled alpha
    mf = cv2.resize(keep.astype(np.float32) / 255, (W * 2, H * 2), interpolation=cv2.INTER_CUBIC)
    mf = np.clip((cv2.GaussianBlur(mf, (0, 0), 3.0) - .5) * 2.2 + .5, 0, 1)
    rgba = Image.new('RGBA', (W * 2, H * 2), (255, 255, 255, 255)); rgba.putalpha(Image.fromarray((mf * 255).astype(np.uint8)))
    b = io.BytesIO(); rgba.save(b, 'PNG', optimize=True)
    data = {'uri': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': W, 'h': H, 'tx': int(tx), 'ty': int(ty)}
    open(a.out, 'w').write(f'window.{a.var}=' + json.dumps(data) + ';\n')
    dbg = im.copy(); dbg[keep > 0] = (dbg[keep > 0] * .3 + np.array([255, 0, 0]) * .7).astype(np.uint8)
    cv2.circle(dbg, (int(tx), int(ty)), max(6, W // 200), (0, 255, 0), -1); Image.fromarray(dbg).save(a.preview)
    print(json.dumps({'out': a.out, 'preview': a.preview, 'size': [W, H], 'target': [int(tx), int(ty)], 'thickness_px': float(dt[ty, tx]), 'kb': len(b.getvalue()) // 1024}))

if __name__ == '__main__':
    main()
