#!/usr/bin/env python3
"""Promo Video Studio · mux.py — final MP4 = silent video + music/voice, web-ready (+ optional cover).

  python3 mux.py silent.mp4 music.wav --out final.mp4 [--cover 12.4]   # cover = frame at 12.4 s → final_cover.jpg

H.264 CRF 19, yuv420p, AAC 256k, +faststart (plays everywhere: Instagram, TikTok, LinkedIn, WhatsApp, PowerPoint).
"""
import argparse, os, subprocess
from pvs_env import ffmpeg

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('audio', nargs='?'); ap.add_argument('--out', default='final.mp4')
    ap.add_argument('--crf', type=int, default=19); ap.add_argument('--cover', type=float); a = ap.parse_args()
    cmd = [ffmpeg(), '-y', '-v', 'error', '-i', a.video]
    if a.audio: cmd += ['-i', a.audio]
    cmd += ['-c:v', 'libx264', '-crf', str(a.crf), '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    cmd += (['-c:a', 'aac', '-b:a', '256k', '-shortest'] if a.audio else ['-an']) + [a.out]
    subprocess.run(cmd, check=True); print(a.out)
    if a.cover is not None:
        cv = os.path.splitext(a.out)[0] + '_cover.jpg'
        subprocess.run([ffmpeg(), '-y', '-v', 'error', '-ss', str(a.cover), '-i', a.out, '-frames:v', '1', '-q:v', '2', cv], check=True); print(cv)

if __name__ == '__main__':
    main()
