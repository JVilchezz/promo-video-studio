#!/usr/bin/env python3
"""Promo Video Studio · brand.py — a brand kit for clients who start from zero (or only have a logo).

  # nothing but a name → palette from the industry/tone (show the sheet, the client approves or changes it)
  python3 brand.py init --name "Aurora Coffee" --industry coffee [--tone warm] [--tagline "…"] [--primary "#1F3480"] --out brand
  # they have a logo → colors extracted from it, logo used for the app icon
  python3 brand.py from-logo logo.png --name "Aurora Coffee" [--tagline "…"] --out brand
  # use it in a video project (tokens in :root, {{BRAND}}/{{TAGLINE}} filled, logo files copied to assets/)
  python3 brand.py apply brand/brand.json my-video

Writes brand/brand.json, wordmark.png (dark), wordmark_light.png, appicon.png (1024, rounded),
brand_sheet.png (palette + type + icon — SHOW IT to the client before building the video).

Industries → tone: coffee food bakery restaurant → warm · tech app software startup → bold ·
finance legal consulting school education → serious · beauty fashion jewelry → elegant ·
health fitness eco pharmacy → fresh · kids toys pets games → playful.   Tones: serious warm bold elegant fresh playful.
Only the NAME and TAGLINE are text — never put claims, numbers or slogans the client didn't give.
"""
import argparse, colorsys, json, os, re, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FONTS = os.path.join(os.path.dirname(HERE), 'assets', 'fonts')
TONES = {   # dark, dark2, light, accent, accent2  (tested for contrast: light text on dark, dark text on accent)
    'serious':  ['#1F3480', '#0B1A4A', '#FAF4EC', '#F2C352', '#C9573F'],
    'warm':     ['#3B2418', '#24150D', '#FBF3E8', '#E8A04A', '#B5482F'],
    'bold':     ['#111827', '#05070D', '#F5F7FB', '#5B8CFF', '#FF6B4A'],
    'elegant':  ['#2B2233', '#17121C', '#F7F2EE', '#C9A27E', '#8E4A5E'],
    'fresh':    ['#14453D', '#0A2722', '#F4F8F3', '#9BD36A', '#F2A541'],
    'playful':  ['#2E2A6B', '#1A1745', '#FFF8EC', '#FFC93C', '#FF6F59'],
}
INDUSTRY = {'warm': 'coffee cafe cafeteria food bakery restaurant soda pizza burger chocolate tea',
            'bold': 'tech app software startup saas gaming esports ai web pc computer',
            'serious': 'finance bank legal law consulting insurance school education university government',
            'elegant': 'beauty fashion jewelry wedding spa salon perfume boutique',
            'fresh': 'health fitness gym eco green pharmacy agro water clinic nutrition',
            'playful': 'kids toys pets games party candy ice'}

def hx(c): c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
def tohex(r, g, b): return '#%02X%02X%02X' % tuple(int(round(max(0, min(1, v)) * 255)) for v in (r, g, b))
def lum(c): r, g, b = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in hx(c)]; return .2126 * r + .7152 * g + .0722 * b
def contrast(a, b): la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + .05) / (lb + .05)
def hls(c): return colorsys.rgb_to_hls(*hx(c))
def fromhls(h, l, s): return tohex(*colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s))))
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), size)

def tone_for(industry):
    for tone, words in INDUSTRY.items():
        if industry and any(w in industry.lower() for w in words.split()): return tone
    return 'serious'

def palette(tone, primary=None, accent=None):
    dark, dark2, light, acc, acc2 = TONES[tone]
    if primary:
        h, l, s = hls(primary)
        if lum(primary) < .18: dark = primary.upper(); dark2 = fromhls(h, l * .55, s)
        else: acc = primary.upper(); dark = fromhls(h, .2, min(.6, s)); dark2 = fromhls(h, .11, min(.6, s))
        light = fromhls(h, .965, .35)
    if accent: acc = accent.upper()
    if contrast(acc, dark) < 3: acc = fromhls(hls(acc)[0], .68, max(.55, hls(acc)[2]))   # keep accent readable on dark
    return {'dark': dark, 'dark2': dark2, 'light': light, 'accent': acc, 'accent2': acc2, 'ink': dark, 'muted': fromhls(hls(dark)[0], .78, .2)}

def logo_palette(path):
    import cv2
    A = np.array(Image.open(path).convert('RGBA')); px = A[..., :3][A[..., 3] > 128].reshape(-1, 3)
    if len(px) < 50: sys.exit('The logo has almost no opaque pixels')
    px = px[np.random.default_rng(0).choice(len(px), min(len(px), 40000), replace=False)].astype(np.float32)
    keep = px.mean(1) < 240; px = px[keep] if keep.sum() > 50 else px          # ignore white background
    k = min(5, len(np.unique(px.astype(int), axis=0)))
    _, lab, cen = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, .5), 4, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.ravel(), minlength=k); cols = [tohex(*(c / 255)) for c in cen]; order = list(np.argsort(-cnt))
    cols = [cols[i] for i in order if cnt[i] > .03 * cnt.sum()]
    darks = [c for c in cols if lum(c) < .2]; sat = sorted([c for c in cols if c not in darks], key=lambda c: -hls(c)[2])
    primary = darks[0] if darks else cols[0]; accent = sat[0] if sat and contrast(sat[0], primary) > 1.8 else None
    return primary, accent, cols

def wordmark(name, color, tagline=None, tcolor=None, h=360):
    f = font('anton-latin-400-normal.woff2', h); txt = name.upper(); sp = int(h * .04)
    widths = [f.getlength(ch) for ch in txt]; W = int(sum(widths) + sp * (len(txt) - 1)) + 40
    ft = font('poppins-latin-600-normal.woff2', int(h * .2)) if tagline else None; th = int(h * .42) if tagline else 0
    if ft: W = max(W, int(ft.getlength(tagline)) + 40)
    im = Image.new('RGBA', (W, int(h * 1.3) + th), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = (W - (sum(widths) + sp * (len(txt) - 1))) / 2
    for ch, w in zip(txt, widths): d.text((x, 0), ch, font=f, fill=color); x += w + sp
    if ft: d.text(((W - ft.getlength(tagline)) / 2, int(h * 1.22)), tagline, font=ft, fill=tcolor or color)
    return im.crop(im.getbbox())

def appicon(name, bg, fg, logo=None, size=1024):
    S = size * 2; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * .225), fill=bg)
    if logo is not None:
        lg = logo.crop(logo.getbbox() or (0, 0, logo.width, logo.height)); lg.thumbnail((int(S * .66), int(S * .66)), Image.LANCZOS); im.alpha_composite(lg, ((S - lg.width) // 2, (S - lg.height) // 2))
    else:
        f = font('anton-latin-400-normal.woff2', int(S * .62)); ch = name.strip()[0].upper(); bb = d.textbbox((0, 0), ch, font=f)
        d.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=fg)
    return im.resize((size, size), Image.LANCZOS)

def sheet(B, wm, icon, out):
    P = B['colors']; W, H = 1600, 900; im = Image.new('RGBA', (W, H), P['light']); d = ImageDraw.Draw(im)
    w = wm.copy(); w.thumbnail((820, 260), Image.LANCZOS); im.alpha_composite(w, (80, 90 + (260 - w.height) // 2))
    ic = icon.resize((260, 260), Image.LANCZOS); im.alpha_composite(ic, (W - 340, 90))
    fl, fs = font('poppins-latin-600-normal.woff2', 22), font('poppins-latin-500-normal.woff2', 20)
    for i, k in enumerate(['dark', 'dark2', 'light', 'accent', 'accent2']):
        x = 80 + i * 292; d.rounded_rectangle([x, 420, x + 262, 600], 24, fill=P[k], outline=(0, 0, 0, 30) if k == 'light' else None, width=2)
        d.text((x, 615), k, font=fl, fill=P['dark']); d.text((x, 645), P[k], font=fs, fill=P['muted'] if contrast(P['muted'], P['light']) > 2.5 else P['dark'])
    d.rectangle([0, 720, W, H], fill=P['dark'])
    d.text((80, 745), 'DISPLAY · ANTON', font=font('anton-latin-400-normal.woff2', 64), fill=P['light'])
    d.text((80, 830), 'Sans · Poppins 500/600/700', font=font('poppins-latin-600-normal.woff2', 30), fill=P['light'])
    d.text((900, 800), 'Hand · Caveat', font=font('caveat-latin-700-normal.woff2', 60), fill=P['accent'])
    im.convert('RGB').save(out)

def build(name, tagline, colors, tone, logo_path, out):
    os.makedirs(out, exist_ok=True)
    B = {'name': name, 'tagline': tagline or '', 'tone': tone, 'colors': colors,
         'fonts': {'display': 'Anton', 'sans': 'Poppins', 'hand': 'Caveat'}, 'logo': os.path.basename(logo_path) if logo_path else None}
    wm = wordmark(name, colors['dark'], tagline, colors['accent2'] if contrast(colors['accent2'], colors['light']) > 3 else colors['dark'])
    wm.save(os.path.join(out, 'wordmark.png')); wordmark(name, colors['light'], tagline, colors['accent']).save(os.path.join(out, 'wordmark_light.png'))
    logo = None
    if logo_path:
        shutil.copy(logo_path, os.path.join(out, os.path.basename(logo_path))); logo = Image.open(logo_path).convert('RGBA')
        A = np.array(logo); bg = colors['dark'] if A[..., :3][A[..., 3] > 128].mean() > 150 else colors['light']   # light logo → dark tile
        ic = appicon(name, bg, colors['accent'], logo)
    else: ic = appicon(name, colors['dark'], colors['accent'])
    ic.save(os.path.join(out, 'appicon.png')); sheet(B, wm, ic, os.path.join(out, 'brand_sheet.png'))
    json.dump(B, open(os.path.join(out, 'brand.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'brand': os.path.join(out, 'brand.json'), 'sheet': os.path.join(out, 'brand_sheet.png'), 'colors': colors, 'tone': tone}, ensure_ascii=False))

def cmd_init(a):
    tone = a.tone or tone_for(a.industry); build(a.name, a.tagline, palette(tone, a.primary, a.accent), tone, None, a.out)

def cmd_from_logo(a):
    primary, accent, found = logo_palette(a.logo); tone = a.tone or tone_for(a.industry)
    print(json.dumps({'logo_colors': found}), file=sys.stderr); build(a.name, a.tagline, palette(tone, primary, accent), tone, a.logo, a.out)

def cmd_apply(a):
    B = json.load(open(a.brand, encoding='utf-8')); c = B['colors']; bdir = os.path.dirname(os.path.abspath(a.brand))
    page = os.path.join(a.project, 'video.html'); s = open(page, encoding='utf-8').read()
    tokens = ':root{' + ';'.join(f'--{k}:{c[k]}' for k in ('dark', 'dark2', 'light', 'accent', 'accent2', 'ink', 'muted')) + '}'
    s = re.sub(r':root\{[^}]*\}', tokens, s, count=1).replace('{{BRAND}}', B['name'])
    if B.get('tagline'): s = s.replace('{{TAGLINE}}', B['tagline'])
    open(page, 'w', encoding='utf-8').write(s); os.makedirs(os.path.join(a.project, 'assets'), exist_ok=True)
    for f in ('wordmark.png', 'wordmark_light.png', 'appicon.png', B.get('logo')):
        if f and os.path.exists(os.path.join(bdir, f)): shutil.copy(os.path.join(bdir, f), os.path.join(a.project, 'assets', f))
    print(f'Applied {B["name"]} to {page} (tokens, name, assets/wordmark*.png, assets/appicon.png)')

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    for n in ('init', 'from-logo'):
        p = sp.add_parser(n)
        if n == 'from-logo': p.add_argument('logo')
        p.add_argument('--name', required=True); p.add_argument('--tagline'); p.add_argument('--industry'); p.add_argument('--tone', choices=TONES)
        p.add_argument('--primary'); p.add_argument('--accent'); p.add_argument('--out', default='brand')
    p = sp.add_parser('apply'); p.add_argument('brand'); p.add_argument('project')
    a = ap.parse_args(); {'init': cmd_init, 'from-logo': cmd_from_logo, 'apply': cmd_apply}[a.cmd](a)

if __name__ == '__main__':
    main()
