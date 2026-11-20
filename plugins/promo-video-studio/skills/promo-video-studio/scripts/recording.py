#!/usr/bin/env python3
"""Promo Video Studio · recording.py — turn a phone screen recording into clean frames for a mockup.

  python3 recording.py rec.mp4 --plan plan.json --out assets/rec --width 540 \
          [--crop 600:1325:60:57] [--statusbar 9:41] [--blur "x,y,w,h@t0-t1;…"] [--xfade 6]

plan.json — which parts to keep and how fast (speed > 1 = faster, use 2–3× for typing, 0.45× for a
screen that flies by):
  [{"from":0.3,"to":3.8,"speed":1.0}, {"from":9.6,"to":15.6,"speed":3.0}, …]
Outputs <out>/0000.jpg… plus <out>.json  {"n": frames, "fps": 30, "segments": [[out_t0,out_t1,src_from,speed],…]}
so the page can show segment k at a known time:  seq('scr', t, T0, 'assets/rec', N, 30, false, 4, 'jpg', '').

--statusbar paints a clean iOS status bar (time, island, signal, battery) over the real one, hiding the
real clock/notifications. --blur hides private data (names, emails, phone numbers, receipts) in the
source-time range given (coordinates in source pixels after --crop). Smooth crossfades join segments.
"""
import argparse, json, os, shutil, subprocess, tempfile
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
from pvs_env import ffmpeg

def statusbar(w, time_txt):
    h = int(round(w * .148)); sb = Image.new('RGB', (w, h), 'white'); d = ImageDraw.Draw(sb); s = w / 1180
    try: f = ImageFont.truetype('DejaVuSans-Bold.ttf', int(48 * s))
    except Exception: f = ImageFont.load_default()
    d.text((105 * s, 58 * s), time_txt, font=f, fill='black')
    d.rounded_rectangle([322 * s, 34 * s, 838 * s, 144 * s], radius=55 * s, fill='black')
    for i in range(4): d.rounded_rectangle([(890 + i * 16) * s, (100 - i * 12) * s, (900 + i * 16) * s, 112 * s], radius=3 * s, fill='black')
    d.rounded_rectangle([970 * s, 70 * s, 1050 * s, 110 * s], radius=12 * s, outline='black', width=max(1, int(4 * s)))
    d.rounded_rectangle([977 * s, 77 * s, 1043 * s, 103 * s], radius=7 * s, fill='black'); d.rounded_rectangle([1054 * s, 82 * s, 1060 * s, 98 * s], radius=2 * s, fill='black')
    return cv2.cvtColor(np.array(sb), cv2.COLOR_RGB2BGR)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--plan', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--width', type=int, default=540); ap.add_argument('--crop'); ap.add_argument('--statusbar'); ap.add_argument('--blur', default='')
    ap.add_argument('--xfade', type=int, default=6); ap.add_argument('--fps', type=int, default=30); a = ap.parse_args()
    plan = json.load(open(a.plan)); shutil.rmtree(a.out, ignore_errors=True); os.makedirs(a.out)
    blurs = []
    for b in filter(None, a.blur.split(';')):
        r, tr = b.split('@'); x, y, w, h = map(int, r.split(',')); t0, t1 = map(float, tr.split('-')); blurs.append((x, y, w, h, t0, t1))
    frames, segs, SB = [], [], None
    def ss(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
    for k, p in enumerate(plan):
        tmp = tempfile.mkdtemp(); sp = p.get('speed', 1.0)
        vf = (f'crop={a.crop},' if a.crop else '') + f'setpts=PTS/{sp},fps={a.fps}'
        subprocess.run([ffmpeg(), '-loglevel', 'error', '-y', '-ss', str(p['from']), '-t', str(p['to'] - p['from']), '-i', a.video, '-vf', vf, '-q:v', '2', f'{tmp}/%05d.jpg'], check=True)
        seg = []
        for i, fn in enumerate(sorted(os.listdir(tmp))):
            im = cv2.imread(f'{tmp}/{fn}'); src_t = p['from'] + i / a.fps * sp
            for x, y, w, h, t0, t1 in blurs:
                if t0 <= src_t <= t1: im[y:y + h, x:x + w] = cv2.GaussianBlur(im[y:y + h, x:x + w], (0, 0), 18)
            if a.statusbar:
                if SB is None: SB = statusbar(im.shape[1], a.statusbar)
                im[:SB.shape[0]] = SB
            H = int(round(im.shape[0] * a.width / im.shape[1])); seg.append(cv2.resize(im, (a.width, H), interpolation=cv2.INTER_AREA))
        shutil.rmtree(tmp)
        if frames and a.xfade:
            for i in range(min(a.xfade, len(seg))):
                al = ss((i + 1) / (a.xfade + 1)); seg[i] = cv2.addWeighted(seg[i], al, frames[-1], 1 - al, 0)
        segs.append([round(len(frames) / a.fps, 3), round((len(frames) + len(seg)) / a.fps, 3), p['from'], sp]); frames += seg
    for i, im in enumerate(frames): cv2.imwrite(f'{a.out}/{i:04d}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    info = {'n': len(frames), 'fps': a.fps, 'size': [frames[0].shape[1], frames[0].shape[0]] if frames else None, 'segments': segs}
    json.dump(info, open(a.out.rstrip('/') + '.json', 'w')); print(json.dumps(info))

if __name__ == '__main__':
    main()
