#!/usr/bin/env python3
"""Promo Video Studio · render.py — turn an animated HTML page into frames / video.

The page must define  window.R = function(t){…}  (draws the frame at time t, seconds)
and set  window.READY = true  once its images and fonts are loaded.

  # contact sheet of a few moments (look at it before every full render!)
  python3 render.py video.html prev 0.5 3 6 9 12 15          → video_prev.png
  # one full-resolution frame
  python3 render.py video.html frame 12.4                     → video_12.4.png
  # full silent video (runs headless Chromium, pipes JPEG frames to ffmpeg)
  python3 render.py video.html full --dur 45 --out silent.mp4
  # contact sheet from a finished MP4 (final QC)
  python3 render.py final.mp4 qc 1 5 10 20 30

Final renders refuse to start while the page still has {{PLACEHOLDERS}} (facts only the client can give).
Options: --w/--h (default from <meta name="pvs-size" content="1080x1920"> or 1080x1920),
         --fps 30, --speed 1.0 (play the timeline faster/slower), --scale 2 (device scale for frames)
"""
import argparse, io, os, re, subprocess, sys
from pvs_env import ffmpeg, launch_chromium

def size_from_html(path):
    try:
        m = re.search(r'name="pvs-size"\s+content="(\d+)x(\d+)"', open(path, encoding='utf-8').read())
        if m: return int(m.group(1)), int(m.group(2))
    except Exception: pass
    return 1080, 1920

def sheet(images, cols, out):
    from PIL import Image
    w, h = images[0].size; rows = (len(images) + cols - 1) // cols
    s = Image.new('RGB', (w * cols, h * rows), (0, 0, 0))
    for i, im in enumerate(images): s.paste(im, ((i % cols) * w, (i // cols) * h))
    s.save(out); print(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('mode', choices=['prev', 'frame', 'full', 'qc']); ap.add_argument('times', nargs='*', type=float)
    ap.add_argument('--w', type=int); ap.add_argument('--h', type=int); ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--dur', type=float); ap.add_argument('--speed', type=float, default=1.0); ap.add_argument('--out')
    ap.add_argument('--crf', type=int, default=16); ap.add_argument('--scale', type=float, default=1)
    ap.add_argument('--allow-placeholders', action='store_true')
    a = ap.parse_args()
    from PIL import Image
    base = os.path.splitext(os.path.basename(a.src))[0]

    if a.mode == 'qc':
        ims = []
        for t in a.times:
            r = subprocess.run([ffmpeg(), '-v', 'error', '-ss', str(t), '-i', a.src, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
            im = Image.open(io.BytesIO(r.stdout)).convert('RGB'); im.thumbnail((360, 360)); ims.append(im)
        sheet(ims, 6 if ims[0].width < ims[0].height else 4, a.out or f'{base}_qc.png'); return

    W, H = size_from_html(a.src)
    W, H = a.w or W, a.h or H
    left = sorted(set(re.findall(r'\{\{[^}]{1,80}\}\}', open(a.src, encoding='utf-8').read())))
    if left:   # facts only the client can give — never render a final video with placeholders
        msg = 'PLACEHOLDERS LEFT: ' + ' · '.join(left[:12]) + '  → fill with REAL data from the client or delete those elements.'
        if a.mode == 'full' and not a.allow_placeholders: sys.exit(msg + ' (--allow-placeholders for a draft)')
        print(msg, file=sys.stderr)
    # film-grain frames are generated on demand (they're incompressible, so not shipped)
    gdir = os.path.dirname(os.path.abspath(a.src))
    for i in range(4):
        gp = os.path.join(gdir, f'grain{i}.png')
        if not os.path.exists(gp) or Image.open(gp).size != (W, H):
            import numpy as np
            Image.fromarray(np.random.default_rng(i + 20).normal(128, 42, (H, W)).clip(0, 255).astype('uint8')).save(gp)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = launch_chromium(p)
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=a.scale)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.goto('file://' + os.path.abspath(a.src))
        pg.wait_for_function('document.fonts.ready.then(()=>true)')
        pg.wait_for_function('window.READY===true', timeout=180000)
        pg.wait_for_timeout(400)
        for e in errs: print('PAGE ERROR:', e[:300], file=sys.stderr)
        if a.mode == 'prev':
            ims = []
            for t in a.times:
                pg.evaluate(f'R({t * a.speed})'); pg.wait_for_timeout(50)
                im = Image.open(io.BytesIO(pg.screenshot())).convert('RGB'); im.thumbnail((360, 360)); ims.append(im)
            sheet(ims, 6 if H > W else 4, a.out or f'{base}_prev.png')
        elif a.mode == 'frame':
            for t in a.times:
                pg.evaluate(f'R({t * a.speed})'); pg.wait_for_timeout(80)
                out = a.out or f'{base}_{t}.png'; pg.screenshot(path=out); print(out)
        else:
            if not a.dur: sys.exit('--dur is required for full renders')
            out = a.out or f'{base}_silent.mp4'
            ff = subprocess.Popen([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(a.fps), '-i', '-',
                                   '-vf', f'scale={W}:{H}', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(a.crf), '-preset', 'medium', out], stdin=subprocess.PIPE)
            n = int(round(a.dur * a.fps))
            for i in range(n):
                pg.evaluate(f'R({i / a.fps * a.speed})')
                ff.stdin.write(pg.screenshot(type='jpeg', quality=95))
                if i % (a.fps * 5) == 0: print(f'  {i / a.fps:5.1f}s / {a.dur}s', flush=True)
            ff.stdin.close(); ff.wait(); print(out)
        b.close()

if __name__ == '__main__':
    main()
