#!/usr/bin/env python3
"""Promo Video Studio · rig.py — split a mascot into parts and animate it like a puppet.

Works from ONE still image of the mascot (PNG, ideally transparent background).

1) INSPECT / AUTO-RIG
   python3 rig.py inspect mascot.png --limb-color "#3E2216" --tol 40 --out rig.json --preview rig_check.png
   • Finds the limbs by color (cartoon stick arms/legs in a different color than the body). Dark shapes
     INSIDE the body (eyes, mouth, logo) are kept on the body.
   • Removes the limbs from the body and repairs the body where they overlapped (inpainting) → body.png
   • Measures each limb (shoulder/hip pivot, length, thickness, hand/foot size, color) so the limbs are
     REDRAWN procedurally in any pose — a raised arm looks clean even if it was hidden behind the body.
   OPEN rig_check.png: each limb colored, yellow dot = pivot, cyan = body pivot, 50 px grid.
   Edit rig.json if something is off (pivots, "kind": arm|leg, "z": -1 behind body / 1 in front).
   Mascots whose limbs can't be found by color: add parts by hand as polygons (cut-out pieces):
     {"name":"arm_r","mode":"cut","poly":[[x,y],…],"pivot":[x,y],"end":[x,y],"z":1}

1b) LAYERS — works with ANY mascot (limbs the same color as the body, furry, 3D-looking…)
   Ask the user for the mascot split in layers, all exported with the SAME canvas size (Canva, Photoshop,
   Procreate, Figma: hide all layers but one → export PNG with transparent background):
   python3 rig.py layers --body body.png --part arm_l=arm_l.png --part arm_r=arm_r.png \
                         --part leg_l=leg_l.png --part leg_r=leg_r.png [--part tail=tail.png] \
                         [--front arm_r] [--behind leg_l] [--pivot arm_r=412,380] --out rig.json --preview rig_check.png
   • pivot (shoulder/hip) and end (hand/foot) are found automatically: the two extremities of each piece
   • names starting with arm_/leg_ follow the presets; any other piece (tail, ear, wing) moves with --keys
   • default depth: arms in front of the body, legs behind (change with --front/--behind)
   Layer pieces are rigid (no elbow bend), so poses look like paper cut-out animation — clean and serious.

2) ANIMATE (presets or keyframes) → transparent PNG frames
   python3 rig.py animate rig.json --preset wave --dur 4.5 --size 1080 --out assets/m_wave [--bubble "¡Hola!"] [--shadow]
   presets: idle · wave · point_right · point_left · celebrate · walk · enter · exit · jump · peek · bow · think
   keyframes: --keys keys.json
     {"body":{"y":[[0,0],[0.5,-40],[1,0]],"rot":[[0,0],[1,4]]}, "arm_r":{"rot":[[0,0],[0.4,-120]],"bend":[[0,0],[0.4,25]]}}
     body: x, y (px), rot (deg, + = clockwise), sx, sy (squash)  ·  limbs: rot (shoulder/hip), bend (elbow/knee)
   Play the frames in a page:  seq('m', t, T0, 'assets/m_wave', N, 30)  (loop=true for idle)

3) EXPORT
   python3 rig.py export assets/m_wave --webm m_wave.webm --mp4 m_wave.mp4 --bg "#FAF4EC" --webp m_wave.webp --webp-size 512
   WebM keeps transparency (web, editors, apps), MP4 on a solid color, animated WebP for websites.

Motion style: weighty and gentle (ease in/out, small overshoot, squash on landings), never frantic.
In serious videos keep the mascot small and calm; confetti only if the client wants a playful tone.
"""
import argparse, json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from pvs_env import ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__)); FONTS = os.path.join(os.path.dirname(HERE), 'assets', 'fonts')
SS = 3  # supersampling for drawn limbs

# ───────────────────────── inspect / auto-rig ─────────────────────────
def inspect(a):
    src = Image.open(a.image).convert('RGBA'); A = np.array(src); H, W = A.shape[:2]; alpha = A[..., 3] > 40
    c = a.limb_color.lstrip('#'); tgt = np.array([[[int(c[i:i + 2], 16) for i in (0, 2, 4)]]], np.uint8)
    lab = cv2.cvtColor(np.ascontiguousarray(A[..., :3]), cv2.COLOR_RGB2LAB).astype(np.float32); tl = cv2.cvtColor(tgt, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    limb = ((np.sqrt(((lab - tl) ** 2).sum(-1)) < a.tol) & alpha).astype(np.uint8) * 255
    limb = cv2.morphologyEx(limb, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    body = (alpha & (limb == 0)).astype(np.uint8) * 255
    nb, lb, sb, _ = cv2.connectedComponentsWithStats(body); body = (lb == 1 + int(np.argmax(sb[1:, 4]))).astype(np.uint8) * 255
    filled = body.copy(); cs, _ = cv2.findContours(body, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(filled, cs, -1, 255, -1)
    filled = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)) > 0
    n, L, st, _ = cv2.connectedComponentsWithStats(limb)
    comps = [i for i in range(1, n) if st[i][4] > a.min_area and filled[L == i].mean() < .6]
    bys, bxs = np.nonzero(filled); bcx, bcy = bxs.mean(), bys.mean(); by1 = bys.max()
    near = cv2.dilate(filled.astype(np.uint8) * 255, np.ones((15, 15), np.uint8)) > 0
    removed = np.zeros((H, W), bool); limbs = []
    for i in comps:
        m = L == i; removed |= cv2.dilate(m.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
        ys, xs = np.nonzero(m); touch = m & near
        if touch.sum(): ty, tx = np.nonzero(touch); k = np.argmin(np.hypot(tx - bcx, ty - bcy)); px, py = float(tx[k]), float(ty[k])
        else: k = np.argmin(np.hypot(xs - bcx, ys - bcy)); px, py = float(xs[k]), float(ys[k])
        d = np.hypot(xs - px, ys - py); k = d.argmax(); ex, ey = float(xs[k]), float(ys[k])
        dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5); de = np.hypot(np.arange(W)[None, :] - ex, np.arange(H)[:, None] - ey)
        dp = np.hypot(np.arange(W)[None, :] - px, np.arange(H)[:, None] - py); mid = m & (de > d.max() * .35) & (dp > d.max() * .08)
        thick = float(2 * np.percentile(dt[mid if mid.sum() > 20 else m], 92))
        far = m & (de < d.max() * .3); r_end = float(max(thick * .6, dt[far].max() if far.any() else thick * .6))
        col = np.median(A[..., :3][m & (dt > 1.5)], 0) if (m & (dt > 1.5)).any() else np.median(A[..., :3][m], 0)
        kind = 'leg' if ys.mean() > bys.min() + (by1 - bys.min()) * .85 else 'arm'
        if kind == 'arm':  # shoulder: on the body edge, no lower than ~60 % of the body height
            py = min(py, bys.min() + (by1 - bys.min()) * .6); row = np.nonzero(filled[int(py)])[0]
            if len(row): px = float(row.min() if px < bcx else row.max())
        # pivot slightly INSIDE the body so the limb grows from behind it
        vx, vy = px - bcx, py - bcy; nrm = math.hypot(vx, vy) or 1; px2, py2 = px - vx / nrm * thick * .8, py - vy / nrm * thick * .8
        limbs.append({'kind': kind, 'mode': 'draw', 'pivot': [round(px2, 1), round(py2, 1)], 'end': [round(ex, 1), round(ey, 1)], 'thick': round(thick, 1),
                      'r_end': round(r_end, 1), 'color': '#%02X%02X%02X' % tuple(int(v) for v in col), 'z': -1})
    legs = [p for p in limbs if p['kind'] == 'leg']
    if legs:  # arms partly hidden behind the body are measured too short → at least ~leg length
        ll = np.mean([math.hypot(p['end'][0] - p['pivot'][0], p['end'][1] - p['pivot'][1]) for p in legs])
        for p in limbs:
            if p['kind'] != 'arm': continue
            L0 = math.hypot(p['end'][0] - p['pivot'][0], p['end'][1] - p['pivot'][1])
            if L0 < ll * .9:
                k = ll * .95 / max(L0, 1); p['end'] = [round(p['pivot'][0] + (p['end'][0] - p['pivot'][0]) * k, 1), round(p['pivot'][1] + (p['end'][1] - p['pivot'][1]) * k, 1)]
        th = max(p['thick'] for p in legs)
        for p in limbs: p['thick'] = round(max(p['thick'], th * .85), 1)
    named = []
    for kind in ('leg', 'arm'):
        ps = sorted([p for p in limbs if p['kind'] == kind], key=lambda p: p['pivot'][0])
        nm = [f'{kind}_l', f'{kind}_r'] if len(ps) == 2 else [f'{kind}_{k + 1}' for k in range(len(ps))]
        for p, n_ in zip(ps, nm): p['name'] = n_; named.append(p)
    # body without limbs, repaired where the limbs covered it
    hole = (removed & filled).astype(np.uint8) * 255
    rgb = cv2.inpaint(np.ascontiguousarray(A[..., :3]), hole, 9, cv2.INPAINT_TELEA)
    B = A.copy(); B[..., :3] = np.where(hole[..., None] > 0, rgb, A[..., :3]); B[..., 3] = np.where(filled, np.where(hole > 0, 255, A[..., 3]), 0)
    bpath = os.path.splitext(a.out)[0] + '_body.png'; Image.fromarray(B).save(bpath)
    od = os.path.dirname(os.path.abspath(a.out)); rel = lambda f: os.path.relpath(os.path.abspath(f), od)
    # paths are stored relative to rig.json, so the rig folder can be moved or committed
    rig = {'image': rel(a.image), 'body_image': rel(bpath), 'body_pivot': [round(float(bcx), 1), round(float(by1), 1)], 'parts': named}
    json.dump(rig, open(a.out, 'w'), indent=1)
    draw_preview(Image.fromarray(B), rig, a.preview)
    print(json.dumps({'rig': a.out, 'body': bpath, 'preview': a.preview, 'parts': [(p['name'], p['pivot'], p['thick']) for p in named]}))

def draw_preview(base, rig, out):
    W, H = base.size; pv = Image.new('RGBA', (W, H), (245, 245, 245, 255)); pv.alpha_composite(base); d = ImageDraw.Draw(pv)
    for gx in range(0, W, 50): d.line([gx, 0, gx, H], fill=(0, 0, 0, 25))
    for gy in range(0, H, 50): d.line([0, gy, W, gy], fill=(0, 0, 0, 25))
    for gx in range(0, W, 100): d.text((gx + 2, 2), str(gx), fill=(0, 0, 0, 160))
    for gy in range(0, H, 100): d.text((2, gy + 2), str(gy), fill=(0, 0, 0, 160))
    cols = [(230, 60, 60), (60, 160, 60), (60, 90, 230), (230, 150, 30), (160, 60, 200), (30, 180, 190)]
    for k, p in enumerate(rig['parts']):
        x0, y0 = p['pivot']; x1, y1 = p.get('end', p['pivot']); c = cols[k % 6]
        d.line([x0, y0, x1, y1], fill=c + (220,), width=6); d.ellipse([x1 - 10, y1 - 10, x1 + 10, y1 + 10], outline=c + (255,), width=4)
        d.ellipse([x0 - 9, y0 - 9, x0 + 9, y0 + 9], fill=(255, 255, 0, 255), outline=(0, 0, 0, 255)); d.text((x0 + 12, y0 - 8), f"{p['name']} z{p.get('z', 1):+d}", fill=(0, 0, 0, 255))
    x, y = rig['body_pivot']; d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(0, 255, 255, 255), outline=(0, 0, 0, 255))
    pv.save(out)

def layers(a):
    body = Image.open(a.body).convert('RGBA'); W, H = body.size; full = body.copy(); parts = []
    piv_over = {k: [float(v) for v in xy.split(',')] for k, xy in (x.split('=') for x in (a.pivot or []))}
    ba = np.array(body)[..., 3] > 40; bys, bxs = np.nonzero(ba)
    if not len(bxs): sys.exit('body.png is empty (no opaque pixels)')
    bcx, bcy = bxs.mean(), bys.mean()
    od = os.path.dirname(os.path.abspath(a.out)); rel = lambda f: os.path.relpath(os.path.abspath(f), od)
    for spec in a.part:
        name, path = spec.split('=', 1); im = Image.open(path).convert('RGBA')
        if im.size != (W, H): sys.exit(f'{path} is {im.size[0]}x{im.size[1]} but body.png is {W}x{H}: export every layer with the SAME canvas size')
        m = np.array(im)[..., 3] > 40; ys, xs = np.nonzero(m)
        if not len(xs): sys.exit(f'{path} is empty')
        k = np.argmax(np.hypot(xs - bcx, ys - bcy)); ex, ey = float(xs[k]), float(ys[k])          # hand/foot: farthest from the body
        k = np.argmax(np.hypot(xs - ex, ys - ey)); px, py = float(xs[k]), float(ys[k])            # shoulder/hip: other extremity
        thick = 2 * float(cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5).max())
        L = math.hypot(ex - px, ey - py) or 1; px, py = px + (ex - px) / L * thick * .5, py + (ey - py) / L * thick * .5   # joint centre
        if name in piv_over: px, py = piv_over[name]
        kind = 'arm' if name.startswith('arm') else 'leg' if name.startswith('leg') else 'other'
        z = 1 if kind == 'arm' else -1 if kind == 'leg' else 1
        if name in (a.front or []): z = 1
        if name in (a.behind or []): z = -1
        parts.append({'name': name, 'kind': kind, 'mode': 'layer', 'file': rel(path), 'pivot': [round(px, 1), round(py, 1)], 'end': [round(ex, 1), round(ey, 1)], 'z': z})
    for zsel in (-1, 1):   # composite in depth order for the reference image
        for p in parts:
            if p['z'] == zsel: full.alpha_composite(Image.open(os.path.join(od, p['file'])).convert('RGBA'))
        if zsel == -1: full.alpha_composite(body)
    fpath = os.path.splitext(a.out)[0] + '_full.png'; full.save(fpath)
    rig = {'image': rel(fpath), 'body_image': rel(a.body), 'body_pivot': [round(float(bcx), 1), round(float(bys.max()), 1)], 'parts': parts}
    json.dump(rig, open(a.out, 'w'), indent=1); draw_preview(full, rig, a.preview)
    print(json.dumps({'rig': a.out, 'preview': a.preview, 'parts': [(p['name'], p['pivot'], p['end'], p['z']) for p in parts]}))

# ───────────────────────── poses ─────────────────────────
def sm(x): x = max(0., min(1., x)); return x * x * (3 - 2 * x)
def kf(keys, t, default=0.):
    if not keys: return default
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * sm((t - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]

def preset(name, t, D):
    s, pi = math.sin, math.pi; br = s(2 * pi * t / 1.6)
    P = {'body': {'y': -4 * br, 'sy': 1 + .012 * br, 'sx': 1 - .008 * br, 'rot': 1.2 * s(2 * pi * t / 3.2)},
         'arm_l': {'rot': 4 + 4 * s(2 * pi * t / 1.6 + 1), 'bend': 6}, 'arm_r': {'rot': -4 - 4 * s(2 * pi * t / 1.6 + 1), 'bend': -6},
         'leg_l': {}, 'leg_r': {}}
    if name in ('idle', 'think'):
        if name == 'think': u = sm((t - .2) / .5); P['arm_r'] = {'abs': -150, 'w': u, 'bend': -110 * u}; P['body']['rot'] = 4 * u + 1.2 * s(2 * pi * t / 3.2)
    elif name == 'wave':
        up = sm((t - .15) / .45) * (1 - sm((t - (D - .6)) / .5)); osc = s(2 * pi * (t - .6) / .55) if t > .6 else 0
        P['arm_r'] = {'abs': -58 + 16 * osc, 'w': up, 'bend': (-20 + 28 * osc) * up}; P['body']['rot'] = -4 * up + 1.2 * s(2 * pi * t / 3.2)
    elif name in ('point_right', 'point_left'):
        side, sg = ('arm_r', -1) if name == 'point_right' else ('arm_l', 1); up = sm((t - .2) / .4)
        pump = (.5 + .5 * s(2 * pi * (t - .6) / .7)) if t > .6 else 0
        P[side] = {'abs': (-6 - 5 * pump) if sg < 0 else (186 + 5 * pump), 'w': up, 'bend': 0}; P['body']['rot'] = sg * -5 * up; P['body']['x'] = sg * -8 * up
    elif name == 'celebrate':
        ph = t % 1.0; on = t < D - .4; j = max(0, s(pi * min(1, ph / .55))) if on else 0; sq = .07 * max(0, 1 - abs(ph - .6) / .1) if on else 0
        P['body'].update({'y': -120 * j, 'sy': 1 - sq + .04 * j, 'sx': 1 + sq - .02 * j})
        w = 12 * s(2 * pi * t * 2); P['arm_l'] = {'abs': 228 + w, 'bend': 30}; P['arm_r'] = {'abs': -48 - w, 'bend': -30}
        P['leg_l'] = {'rot': 18 * j}; P['leg_r'] = {'rot': -18 * j}
    elif name in ('walk', 'enter', 'exit'):
        cy = 2 * pi * t / .62; P['body'].update({'y': -10 * abs(s(cy)), 'rot': 3 * s(cy)})
        P['leg_l'] = {'rot': 26 * s(cy)}; P['leg_r'] = {'rot': -26 * s(cy)}; P['arm_l'] = {'rot': -24 * s(cy), 'bend': 12}; P['arm_r'] = {'rot': -24 * s(cy), 'bend': -12}
        if name == 'enter':
            k = sm(t / (D * .55)); P['body']['x'] = -1.0 * (1 - k)   # in canvas widths
            if t > D * .55:
                P['body'].update({'y': -4 * br, 'rot': 0}); P['leg_l'] = {}; P['leg_r'] = {}
                up = sm((t - D * .6) / .4); osc = s(2 * pi * (t - D * .7) / .55)
                P['arm_r'] = {'abs': -58 + 16 * osc, 'w': up, 'bend': (-20 + 28 * osc) * up}; P['arm_l'] = {'rot': 6, 'bend': 6}
        if name == 'exit': P['body']['x'] = 1.0 * sm((t - .4) / (D - .6))
    elif name == 'jump':
        ph = (t - .3) / .9; j = max(0, s(pi * ph)) if 0 < ph < 1 else 0
        pre = .09 * max(0, 1 - abs(t - .25) / .15); land = .09 * max(0, 1 - abs(t - 1.25) / .15)
        P['body'].update({'y': -240 * j, 'sy': 1 - pre - land + .05 * j, 'sx': 1 + pre + land - .03 * j})
        P['arm_l'] = {'abs': 215, 'w': j, 'bend': 10}; P['arm_r'] = {'abs': -35, 'w': j, 'bend': -10}; P['leg_l'] = {'rot': 12 * j}; P['leg_r'] = {'rot': -12 * j}
    elif name == 'peek':
        k = sm((t - .2) / 1.0); P['body']['y'] = 560 * (1 - k)
        if t > 1.4: up = sm((t - 1.4) / .4); osc = s(2 * pi * (t - 1.8) / .55); P['arm_r'] = {'abs': -58 + 16 * osc, 'w': up, 'bend': (-20 + 28 * osc) * up}
    elif name == 'bow':
        k = sm((t - .3) / .5) * (1 - sm((t - 1.7) / .5)); P['body']['rot'] = 16 * k; P['arm_l'] = {'rot': -15 * k, 'bend': 20 * k}; P['arm_r'] = {'rot': 15 * k, 'bend': -20 * k}
    return P

# ───────────────────────── drawing ─────────────────────────
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def draw_limb(layer, p, piv, base_ang, pose, scale):
    """2-segment limb (shoulder→elbow→hand) with round joints and a hand/foot blob."""
    L = math.hypot(p['end'][0] - p['pivot'][0], p['end'][1] - p['pivot'][1]) * scale; th = p['thick'] * scale; r = p['r_end'] * scale
    a1 = base_ang + math.radians(pose.get('rot', 0))
    if 'abs' in pose:  # absolute target direction (deg, screen: 0 = right, -90 = up), blended by w
        tgt = math.radians(pose['abs'])
        while tgt - base_ang > math.pi: tgt -= 2 * math.pi
        while tgt - base_ang < -math.pi: tgt += 2 * math.pi
        w = pose.get('w', 1); a1 = (1 - w) * a1 + w * tgt
    a2 = a1 + math.radians(pose.get('bend', 0))
    e = (piv[0] + math.cos(a1) * L * .52, piv[1] + math.sin(a1) * L * .52); h = (e[0] + math.cos(a2) * (L * .48 - r * .5), e[1] + math.sin(a2) * (L * .48 - r * .5))
    col = hexrgb(p['color']); dark = tuple(int(v * .78) for v in col); d = ImageDraw.Draw(layer)
    def seg(pa, pb, w, c):
        d.line([pa[0] * SS, pa[1] * SS, pb[0] * SS, pb[1] * SS], fill=c + (255,), width=int(w * SS))
        for q in (pa, pb): d.ellipse([(q[0] - w / 2) * SS, (q[1] - w / 2) * SS, (q[0] + w / 2) * SS, (q[1] + w / 2) * SS], fill=c + (255,))
    seg(piv, e, th + 3 * scale, dark); seg(e, h, th + 3 * scale, dark); seg(piv, e, th, col); seg(e, h, th, col)
    if p['kind'] == 'leg':
        fa = a2 - math.pi / 2; rx, ry = r * 1.25, r * .8; pts = []
        for k in range(36):
            u = 2 * math.pi * k / 36; x, y = rx * math.cos(u), ry * math.sin(u); x += r * .45
            pts.append(((h[0] + x * math.cos(fa * .35) - y * math.sin(fa * .35)) * SS, (h[1] + r * .2 + x * math.sin(fa * .35) + y * math.cos(fa * .35)) * SS))
        d.polygon(pts, fill=dark + (255,)); d.polygon([((x - h[0] * SS) * .9 + h[0] * SS, (y - h[1] * SS) * .9 + h[1] * SS) for x, y in pts], fill=col + (255,))
    else:
        d.ellipse([(h[0] - r - 1.5 * scale) * SS, (h[1] - r - 1.5 * scale) * SS, (h[0] + r + 1.5 * scale) * SS, (h[1] + r + 1.5 * scale) * SS], fill=dark + (255,))
        d.ellipse([(h[0] - r) * SS, (h[1] - r) * SS, (h[0] + r) * SS, (h[1] + r) * SS], fill=col + (255,))

def rigid_angle(p, pose, brot):
    """Rotation (rad) for a rigid piece: body rotation + 'rot', or blended toward an absolute direction 'abs'."""
    base0 = math.atan2(p['end'][1] - p['pivot'][1], p['end'][0] - p['pivot'][0]) if 'end' in p else 0.
    a1 = base0 + brot + math.radians(pose.get('rot', 0))
    if 'abs' in pose and 'end' in p:
        tgt = math.radians(pose['abs'])
        while tgt - a1 > math.pi: tgt -= 2 * math.pi
        while tgt - a1 < -math.pi: tgt += 2 * math.pi
        w = pose.get('w', 1); a1 = (1 - w) * a1 + w * tgt
    return a1 - base0

def compose(rig, body_img, cut_imgs, size, pose, scale, origin, bubble=None, font=None, t=0):
    S = size; bp = np.array(rig['body_pivot'], float); bt = pose.get('body', {})
    brot = math.radians(bt.get('rot', 0)); bsx, bsy = bt.get('sx', 1), bt.get('sy', 1); bx = bt.get('x', 0); bx = bx * S if abs(bx) <= 2 else bx
    off = np.array([bx, bt.get('y', 0)]); c, s_ = math.cos(brot), math.sin(brot)
    def bmap(p):
        v = (np.array(p, float) - bp) * [bsx, bsy]; v = np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]]); return origin + v * scale + off
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    def drawn(zsel):
        lay = Image.new('RGBA', (S * SS, S * SS), (0, 0, 0, 0)); any_ = False
        for p in rig['parts']:
            if p.get('mode', 'draw') != 'draw' or (p.get('z', -1) < 0) != (zsel < 0): continue
            base = math.atan2(p['end'][1] - p['pivot'][1], p['end'][0] - p['pivot'][0]) + brot
            draw_limb(lay, p, bmap(p['pivot']), base, pose.get(p['name'], {}), scale); any_ = True
        if any_: out.alpha_composite(lay.resize((S, S), Image.LANCZOS))
    def cuts(zsel):
        for p in rig['parts']:
            if p.get('mode') not in ('cut', 'layer') or (p.get('z', 1) < 0) != (zsel < 0): continue
            img = cut_imgs[p['name']]; tr = pose.get(p['name'], {}); rot = math.degrees(rigid_angle(p, tr, brot))
            im2 = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS); pv = np.array(p['pivot']) * scale
            big = Image.new('RGBA', (im2.width * 3, im2.height * 3), (0, 0, 0, 0)); big.paste(im2, (im2.width, im2.height))
            r = big.rotate(-rot, resample=Image.BICUBIC, center=(pv[0] + im2.width, pv[1] + im2.height)); dst = bmap(p['pivot'])
            lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); lay.paste(r, (int(round(dst[0] - pv[0] - im2.width)), int(round(dst[1] - pv[1] - im2.height))), r); out.alpha_composite(lay)
    drawn(-1); cuts(-1)
    bw, bh = body_img.size; im2 = body_img.resize((max(1, int(bw * scale * bsx)), max(1, int(bh * scale * bsy))), Image.LANCZOS); pv = bp * [scale * bsx, scale * bsy]
    big = Image.new('RGBA', (im2.width * 3, im2.height * 3), (0, 0, 0, 0)); big.paste(im2, (im2.width, im2.height))
    r = big.rotate(-math.degrees(brot), resample=Image.BICUBIC, center=(pv[0] + im2.width, pv[1] + im2.height)); dst = origin + off
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); lay.paste(r, (int(round(dst[0] - pv[0] - im2.width)), int(round(dst[1] - pv[1] - im2.height))), r); out.alpha_composite(lay)
    drawn(1); cuts(1)
    if bubble and font:
        k = sm((t - .4) / .3)
        if k > 0:
            d0 = ImageDraw.Draw(out); tw = d0.textlength(bubble, font=font); bw_, bh_ = tw + 70, font.size * 1.6
            bb = Image.new('RGBA', (int(bw_) + 40, int(bh_) + 50), (0, 0, 0, 0)); dd = ImageDraw.Draw(bb)
            dd.rounded_rectangle([0, 0, bw_, bh_], radius=bh_ / 2, fill=(18, 52, 143, 255)); dd.polygon([(30, bh_ - 4), (70, bh_ - 4), (18, bh_ + 34)], fill=(18, 52, 143, 255))
            dd.text((35, bh_ * .18), bubble, font=font, fill=(255, 255, 255, 255)); sc = .6 + .4 * k
            bb = bb.resize((max(1, int(bb.width * sc)), max(1, int(bb.height * sc))), Image.LANCZOS); al = np.array(bb.split()[3]).astype(float) * k; bb.putalpha(Image.fromarray(al.astype(np.uint8)))
            lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); lay.paste(bb, (int(S * .6), int(S * .06 + bh_ * (1 - sc))), bb); out.alpha_composite(lay)
    return out

def animate(a):
    rig = json.load(open(a.rig)); rd = os.path.dirname(os.path.abspath(a.rig)); P = lambda f: f if os.path.isabs(f) else os.path.join(rd, f)
    body = Image.open(P(rig.get('body_image') or rig['image'])).convert('RGBA'); src = np.array(Image.open(P(rig['image'])).convert('RGBA'))
    cut_imgs = {}
    for p in rig['parts']:
        if p.get('mode') == 'layer': cut_imgs[p['name']] = Image.open(P(p['file'])).convert('RGBA'); continue
        if p.get('mode') == 'cut' and 'end' not in p:
            q = np.array(p['poly'], float); p['end'] = q[np.argmax(np.hypot(q[:, 0] - p['pivot'][0], q[:, 1] - p['pivot'][1]))].tolist()
        if p.get('mode') == 'cut':
            m = np.zeros(src.shape[:2], np.uint8); cv2.fillPoly(m, [np.array(p['poly'], np.int32)], 255); img = src.copy(); img[..., 3] = np.where(m > 0, src[..., 3], 0)
            cut_imgs[p['name']] = Image.fromarray(img); b = np.array(body); b[..., 3] = np.where(m > 0, 0, b[..., 3]); body = Image.fromarray(b)
    keys = json.load(open(a.keys)) if a.keys else None
    ys, xs = np.nonzero(src[..., 3] > 20); ext = max(xs.max() - xs.min(), ys.max() - ys.min()); scale = a.size * a.fill / ext
    bp = np.array(rig['body_pivot'], float); origin = np.array([a.size / 2 + (bp[0] - (xs.min() + xs.max()) / 2) * scale, a.size * .5 + (bp[1] - (ys.min() + ys.max()) / 2) * scale + a.size * .05])
    font = ImageFont.truetype(os.path.join(FONTS, 'poppins-latin-700-normal.woff2'), int(a.size * .045)) if a.bubble else None
    os.makedirs(a.out, exist_ok=True); N = int(round(a.dur * a.fps))
    for i in range(N):
        t = i / a.fps
        if keys: pose = {p: {k: kf(v, t, 1 if k in ('sx', 'sy') else 0) for k, v in ch.items()} for p, ch in keys.items()}
        else: pose = preset(a.preset, t, a.dur)
        fr = compose(rig, body, cut_imgs, a.size, pose, scale, origin, a.bubble, font, t)
        if a.shadow:
            bt = pose.get('body', {}); lift = min(1, abs(bt.get('y', 0)) / 300); sh = Image.new('RGBA', fr.size, (0, 0, 0, 0)); w = a.size * (.2 - .06 * lift)
            fy = origin[1] + (ys.max() - bp[1]) * scale; cxs = origin[0] + (bt.get('x', 0) * a.size if abs(bt.get('x', 0)) <= 2 else bt.get('x', 0))
            ImageDraw.Draw(sh).ellipse([cxs - w, fy - a.size * .012, cxs + w, fy + a.size * .02], fill=(60, 40, 20, int(55 * (1 - .5 * lift)))); sh.alpha_composite(fr); fr = sh
        fr.save(f'{a.out}/f_{i + 1:03d}.png')
    print(json.dumps({'frames': N, 'out': a.out, 'preset': 'keys' if keys else a.preset}))

def export(a):
    pat = os.path.join(a.frames, 'f_%03d.png')
    if a.webm: subprocess.run([ffmpeg(), '-y', '-v', 'error', '-framerate', str(a.fps), '-i', pat, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '2M', a.webm], check=True)
    if a.mp4: subprocess.run([ffmpeg(), '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color={a.bg}:s=64x64:r={a.fps}', '-framerate', str(a.fps), '-i', pat,
                              '-filter_complex', '[0:v][1:v]scale2ref[bg][fg];[bg][fg]overlay=shortest=1,format=yuv420p', '-c:v', 'libx264', '-crf', '18', a.mp4], check=True)
    if a.webp:
        fs = sorted(f for f in os.listdir(a.frames) if f.endswith('.png')); ims = [Image.open(os.path.join(a.frames, f)) for f in fs]
        if a.webp_size: ims = [im.resize((a.webp_size, a.webp_size), Image.LANCZOS) for im in ims]
        ims[0].save(a.webp, save_all=True, append_images=ims[1:], duration=int(1000 / a.fps), loop=0, quality=80, method=6)
    print('exported')

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('inspect'); p.add_argument('image'); p.add_argument('--limb-color', required=True); p.add_argument('--tol', type=float, default=40)
    p.add_argument('--min-area', type=int, default=400); p.add_argument('--out', default='rig.json'); p.add_argument('--preview', default='rig_check.png')
    p = sp.add_parser('layers'); p.add_argument('--body', required=True); p.add_argument('--part', action='append', required=True, help='name=file.png')
    p.add_argument('--front', nargs='*'); p.add_argument('--behind', nargs='*'); p.add_argument('--pivot', action='append', help='name=x,y')
    p.add_argument('--out', default='rig.json'); p.add_argument('--preview', default='rig_check.png')
    p = sp.add_parser('animate'); p.add_argument('rig'); p.add_argument('--preset', default='idle'); p.add_argument('--keys'); p.add_argument('--dur', type=float, default=4.0)
    p.add_argument('--fps', type=int, default=30); p.add_argument('--out', required=True); p.add_argument('--size', type=int, default=1080); p.add_argument('--fill', type=float, default=.55)
    p.add_argument('--bubble'); p.add_argument('--shadow', action='store_true')
    p = sp.add_parser('export'); p.add_argument('frames'); p.add_argument('--webm'); p.add_argument('--mp4'); p.add_argument('--bg', default='#FAF4EC'); p.add_argument('--webp')
    p.add_argument('--webp-size', type=int); p.add_argument('--fps', type=int, default=30)
    a = ap.parse_args(); {'inspect': inspect, 'layers': layers, 'animate': animate, 'export': export}[a.cmd](a)

if __name__ == '__main__':
    main()
