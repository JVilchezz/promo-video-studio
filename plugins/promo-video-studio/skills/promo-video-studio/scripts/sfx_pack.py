#!/usr/bin/env python3
"""Promo Video Studio · sfx_pack.py — warm, premium sound design: app notification sounds, UI sounds and
a sonic logo, all synthesized (royalty-free) and tunable to the brand's key.

  python3 sfx_pack.py --out sounds/ --key D [--mp3] [--only notif_bell,notif_marimba]

Generates (WAV 44.1 kHz stereo, normalized to −1 dBFS, short tails):
  notif_bell      soft two-note bell (FM, low index — never piercing)
  notif_marimba   warm marimba arpeggio (wooden, rounded)
  notif_dingding  classic two-tone "ding-ding", softened
  notif_popchord  bubble pop + soft major chord
  success         rising major triad, felt piano     error   gentle low two-note "uh-oh" (not harsh)
  tap  click  toggle  send  receive  typing  swipe  whoosh  riser  boom  sparkle_soft  paper  shutter
  sonic_logo      2-second brand signature (pluck arpeggio + pad + soft hit) in the given key

Rules that made clients happy: short, rounded attacks, no frequencies screaming above ~4 kHz, a tiny
room, and every sound in the same key so they feel like one family. Use them in cue.json ("sfx")
or deliver them as the app's notification/UI sounds (iOS/Android accept .wav/.caf/.mp3/.ogg).
"""
import argparse, os, subprocess, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from pvs_env import ffmpeg

SR = 44100; rng = np.random.default_rng(3)
KEYS = {'C': 0, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'Gb': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def T(d): return np.arange(int(d * SR)) / SR
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b): return sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x)
def env(t, a=.003, d=.5): return np.clip(t / a, 0, 1) * np.exp(-t / d)
def mix(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, at, g in parts:
        i = int(at * SR); n = min(len(x), len(out) - i)
        if n > 0: out[i:i + n] += x[:n] * g
    return out

def bell(f, d=1.4, idx=1.1): t = T(d); return np.sin(2 * np.pi * f * t + idx * np.exp(-t / .18) * np.sin(2 * np.pi * f * 2.0 * t)) * env(t, .002, .45)
def marimba(f, d=.9):
    t = T(d); y = np.sin(2 * np.pi * f * t) * np.exp(-t / .32) + .35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / .05) + .12 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / .015)
    return y * np.clip(t / .0015, 0, 1)
def felt(f, d=1.6, vel=.6):
    t = T(d); y = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (.9 + h * .7)) / h ** 1.6 for h in range(1, 7)); return lp(y * np.clip(t / .006, 0, 1), 1500 + 3000 * vel)
def pluck(f, d=.6):
    t = T(d); ph = f * t; x = 2 * (ph % 1) - 1; k = np.exp(-t * 16); return (lp(x, 1200) * (1 - k) + lp(x, 3200) * k) * env(t, .002, .2)
def pad(fs, d, att=.3):
    t = T(d); y = sum(lp(2 * ((f * (1 + dv) * t + rng.uniform()) % 1) - 1, 1600) for f in fs for dv in (-.004, .004))
    return y * np.clip(t / att, 0, 1) * np.clip((d - t) / .6, 0, 1) / (2 * len(fs))
def noise(d): return rng.normal(0, 1, int(d * SR))
def sweep(d, lo, hi, up=True):
    n = noise(d); y = np.zeros_like(n); C = int(.02 * SR)
    for s in range(0, len(n), C):
        k = s / len(n); k = k if up else 1 - k; c = lo + (hi - lo) * k ** 2; seg = bp(n[max(0, s - 1500):s + C], c * .6, c * 1.3); y[s:s + C] = seg[-len(y[s:s + C]):]
    return y

def make(key):
    K = KEYS[key]; m = lambda n: hz(n + K)     # MIDI note in C → transposed
    S = {}
    S['notif_bell'] = mix([(bell(m(76)), 0, .6), (bell(m(83)), .12, .5)], 1.6)
    S['notif_marimba'] = mix([(marimba(m(72)), 0, .5), (marimba(m(76)), .09, .5), (marimba(m(79)), .18, .5), (marimba(m(84)), .27, .55)], 1.3)
    S['notif_dingding'] = mix([(bell(m(79), 1.2, .7), 0, .55), (bell(m(76), 1.2, .7), .16, .5)], 1.5)
    t = T(.12); popx = np.sin(2 * np.pi * (260 + 600 * np.exp(-t * 45)) * t) * np.exp(-t / .03)
    S['notif_popchord'] = mix([(popx, 0, .7)] + [(felt(m(n), 1.4, .7), .05 + .015 * i, .35) for i, n in enumerate([60, 64, 67, 72])], 1.5)
    S['success'] = mix([(felt(m(n), 1.2, .8), .09 * i, .5) for i, n in enumerate([60, 64, 67, 72])], 1.6)
    S['error'] = mix([(felt(m(n) , 1.0, .4), .14 * i, .6) for i, n in enumerate([62, 58])], 1.3)
    t = T(.06); S['tap'] = lp(noise(.06), 2500) * np.exp(-t / .006) * .8 + np.sin(2 * np.pi * 180 * t) * np.exp(-t / .015) * .5
    t = T(.03); S['click'] = lp(noise(.03), 4000) * np.exp(-t / .003)
    S['toggle'] = mix([(S['click'], 0, .8), (marimba(m(84), .3), .0, .25)], .4)
    S['send'] = mix([(sweep(.35, 400, 2600), 0, .25), (pluck(m(79), .4), .18, .4)], .7)
    S['receive'] = mix([(marimba(m(79), .6), 0, .45), (marimba(m(84), .6), .07, .4)], .8)
    tp = np.zeros(int(1.4 * SR))
    for k in range(9):
        i = int((k * .14 + rng.uniform(0, .05)) * SR); c = lp(noise(.025), 3500) * np.exp(-T(.025) / .004) * rng.uniform(.5, 1); tp[i:i + len(c)] += c
    S['typing'] = tp
    S['swipe'] = sweep(.35, 600, 3000) * np.sin(np.pi * T(.35) / .35) ** 2
    S['whoosh'] = sweep(.8, 300, 2200) * np.sin(np.pi * T(.8) / .8) ** 2
    t = T(2.0); S['riser'] = sweep(2.0, 300, 6000) * (t / 2.0) ** 2.3
    t = T(2.6); S['boom'] = np.sin(2 * np.pi * (36 + 26 * np.exp(-t * 4)) * t) * np.exp(-t / .9) * np.clip(t / .008, 0, 1) + lp(noise(2.6), 300) * np.exp(-t / .25) * .3
    S['sparkle_soft'] = mix([(bell(m(n), .9, .5), .06 * i, .25) for i, n in enumerate([76, 79, 84])], 1.2)
    t = T(.3); S['paper'] = lp(noise(.3), 800) * np.exp(-t / .035) * .6 + np.sin(2 * np.pi * 100 * t) * np.exp(-t / .06) * .45 + bp(noise(.3), 1500, 5000) * np.exp(-t / .02) * .2
    t = T(.18); sh = bp(noise(.18), 1200, 6000); S['shutter'] = mix([(sh * np.exp(-T(.18) / .01), 0, .7), (sh * np.exp(-T(.18) / .012), .07, .5)], .3)
    S['sonic_logo'] = mix([(pluck(m(n), .7), .12 * i, .5) for i, n in enumerate([62, 66, 69, 74])] + [(pad([m(50), m(57), m(62), m(66)], 2.2, .15), .36, .9),
                           (felt(m(38), 2.0, .5), .36, .6), (bell(m(86), 1.2, .5), .5, .12)], 2.4)
    return S

def finish(x):
    x = hp(lp(x, 9000), 40); ir = lp(noise(1.2) * np.exp(-T(1.2) / .25), 6000); ir /= np.sqrt((ir ** 2).sum())
    wet = fftconvolve(x, ir)[:len(x) + int(.4 * SR)]; y = np.zeros(len(wet)); y[:len(x)] = x; y += .12 * wet
    n = int(.03 * SR); y[-n:] *= np.linspace(1, 0, n); y = y / (np.abs(y).max() + 1e-9) * .89
    return np.stack([y, np.roll(y, 9) * .98], 1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='sounds'); ap.add_argument('--key', default='D', choices=KEYS)
    ap.add_argument('--mp3', action='store_true'); ap.add_argument('--only'); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); S = make(a.key); sel = a.only.split(',') if a.only else S.keys()
    for k in sel:
        y = finish(S[k]); p = os.path.join(a.out, k + '.wav')
        with wave.open(p, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())
        if a.mp3: subprocess.run([ffmpeg(), '-y', '-v', 'error', '-i', p, '-b:a', '192k', p[:-4] + '.mp3'], check=True)
    print(f'{len(list(sel))} sounds → {a.out}/ (key {a.key})')

if __name__ == '__main__':
    main()
