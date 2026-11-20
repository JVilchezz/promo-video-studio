#!/usr/bin/env python3
"""Promo Video Studio · new_project.py — scaffold a video project.

  python3 new_project.py my-video --format vertical     # 1080x1920 reel / TikTok / Shorts
  python3 new_project.py my-video --format horizontal   # 1920x1080 LinkedIn / YouTube
  python3 new_project.py my-video --format square       # 1080x1350 Instagram feed

Creates:
  my-video/video.html   ← starter page (edit this)
  my-video/cue.json     ← music cue sheet for score.py
  my-video/pvs/         ← motion.js, base.css, fonts
  my-video/grain0-3.png ← film grain frames
"""
import argparse, os, shutil, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
SIZES = {'vertical': (1080, 1920), 'horizontal': (1920, 1080), 'square': (1080, 1350)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--format', choices=SIZES, default='vertical')
    ap.add_argument('--force', action='store_true'); a = ap.parse_args()
    W, H = SIZES[a.format]
    if os.path.exists(a.dir) and os.listdir(a.dir) and not a.force: raise SystemExit(f'{a.dir} exists and is not empty (use --force)')
    os.makedirs(os.path.join(a.dir, 'pvs', 'fonts'), exist_ok=True); os.makedirs(os.path.join(a.dir, 'assets'), exist_ok=True)
    for f in ('motion.js', 'base.css'): shutil.copy(os.path.join(SKILL, 'lib', f), os.path.join(a.dir, 'pvs', f))
    for f in os.listdir(os.path.join(SKILL, 'assets', 'fonts')): shutil.copy(os.path.join(SKILL, 'assets', 'fonts', f), os.path.join(a.dir, 'pvs', 'fonts', f))
    tpl = 'vertical.html' if a.format != 'horizontal' else 'horizontal.html'
    html = open(os.path.join(SKILL, 'templates', tpl), encoding='utf-8').read().replace('{{W}}', str(W)).replace('{{H}}', str(H))
    open(os.path.join(a.dir, 'video.html'), 'w', encoding='utf-8').write(html)
    for i in range(4):
        n = np.random.default_rng(i + 20).normal(128, 42, (H, W)).clip(0, 255).astype('uint8')
        Image.fromarray(n).save(os.path.join(a.dir, f'grain{i}.png'))
    shutil.copy(os.path.join(SKILL, 'templates', 'cue.json'), os.path.join(a.dir, 'cue.json'))
    print(f'Created {a.dir}/ ({W}x{H}). Next: edit video.html, then\n'
          f'  python3 {HERE}/render.py {a.dir}/video.html prev 0.5 2 4 6 8 10')

if __name__ == '__main__':
    main()
