#!/usr/bin/env python3
"""Promo Video Studio · score.py — original, royalty-free music + sound design,
generated from a cue sheet so every hit lands exactly on the picture.

  python3 score.py cue.json --out music.wav            # music + SFX
  python3 score.py cue.json --out sfx.wav --sfx-only   # SFX only (to add a licensed song later)

cue.json (all times in seconds of the FINAL video):
{
  "duration": 30.0,
  "style": "uplifting",          // uplifting | cinematic | nostalgic | minimal
  "bpm": 96, "key": "D",         // key = major key name (C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B)
  "seed": 7,                     // change it → new melody/arpeggio (never reuse the same score)
  "sections": [                  // energy 0..1 drives the arrangement; "build": true = drum roll + riser
    {"start": 0,    "energy": 0.15},
    {"start": 5.0,  "energy": 0.45},
    {"start": 10.0, "energy": 0.8},
    {"start": 17.5, "energy": 0.6, "build": true},
    {"start": 20.0, "energy": 1.0},
    {"start": 26.0, "energy": 0.3}
  ],
  "hits":   [10.0, 20.0],         // boom + dark crash + accent (logo reveal, award, drop)
  "silence_before": [20.0],       // short breath of silence right before these times
  "cuts":   [5.0, 10.0, 17.5, 26.0],   // soft whoosh into every scene change
  "end": 27.0,                    // final chord rings from here to the end
  "voice": {"file": "voice_track.wav", "duck_db": 8, "gain": 1.0},   // optional voice-over (voice.py place) — music ducks under it
  "sfx": [ {"type": "write", "t": 1.0, "dur": 1.6}, {"type": "thud", "t": 6.4},
           {"type": "ding", "t": 12.0}, {"type": "riser", "t": 18.0, "dur": 2.0},
           {"type": "sweep", "t": 21.5}, {"type": "pop", "t": 14.0}, {"type": "click", "t": 15.0},
           {"type": "whoosh", "t": 3.0}, {"type": "boom", "t": 9.0},
           {"type": "file", "t": 11.2, "path": "sounds/notif_bell.wav", "gain": 1.0} ]   // any WAV/MP3 (sfx_pack.py UI sounds)
}
Paths ("voice.file", sfx "path") are relative to the cue.json folder.
Tip: put "cuts" and "hits" on the beat grid: beat = 60/bpm, bar = 4 beats.
The palette is deliberately warm — no music-box, no bells above ~1 kHz, master low-passed —
so it never sounds shrill ("chillón").
"""
import argparse, json, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve, lfilter
from pvs_env import ffmpeg

SR = 44100
KEYS = {'C': 0, 'Db': 1, 'C#': 1, 'D': 2, 'Eb': 3, 'D#': 3, 'E': 4, 'F': 5, 'Gb': 6, 'F#': 6, 'G': 7, 'Ab': 8, 'G#': 8, 'A': 9, 'Bb': 10, 'A#': 10, 'B': 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
ROMAN = {'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5}
STYLES = {
    # progression, chord extension, melody rhythm bank, master low-pass, groove
    'uplifting': dict(prog=['I', 'V', 'vi', 'IV'], ext='add9', lpf=11000, groove='pop', arp='pluck', rev=1.6),
    'cinematic': dict(prog=['vi', 'IV', 'I', 'V'], ext='triad', lpf=8500, groove='epic', arp='piano', rev=2.8),
    'nostalgic': dict(prog=['IV', 'V', 'iii', 'vi'], ext='maj7', lpf=8000, groove='soft', arp='piano', rev=2.4),
    'minimal':   dict(prog=['I', 'vi', 'IV', 'V'], ext='add9', lpf=11000, groove='light', arp='pluck', rev=1.4),
}
RHYTHMS = [[(0, 1), (1, .5), (1.5, 1.5), (3, 1)], [(0, 1.5), (1.5, .5), (2, 1), (3, 1)], [(0, 2), (2, 1), (3, 1)],
           [(0, 1), (1, 1), (2, 2)], [(0, .5), (.5, .5), (1, 1), (2, 2)], [(0, 3), (3, 1)]]

def T(d): return np.arange(int(max(d, 0) * SR)) / SR
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, a, b): return sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x, axis=0)
def taper(s, ms=60):
    s = s.copy(); n = min(len(s), int(ms / 1000 * SR))
    if n: s[-n:] *= np.linspace(1, 0, n)
    return s

class Score:
    def __init__(s, cue):
        s.c = cue; s.D = float(cue['duration']); s.N = int(s.D * SR); s.rng = np.random.default_rng(cue.get('seed', 1))
        s.st = STYLES[cue.get('style', 'uplifting')]; s.bpm = float(cue.get('bpm', 96)); s.beat = 60 / s.bpm; s.bar = 4 * s.beat
        s.key = KEYS[cue.get('key', 'D')]; s.bus = {k: np.zeros((s.N, 2)) for k in ['keys', 'arp', 'str', 'bass', 'drm', 'sfx']}
        s.secs = sorted(cue.get('sections', [{'start': 0, 'energy': .5}]), key=lambda x: x['start'])
        s.end = cue.get('end', s.D - 3); s.silence = cue.get('silence_before', []); s.kicks = []

    # ── helpers ──
    def add(s, b, x, at, g=1, pan=0):
        i = int(round(at * SR)); x = np.asarray(x) * g
        if x.ndim == 1: a = (pan + 1) * np.pi / 4; x = np.stack([x * np.cos(a), x * np.sin(a)], 1) * 1.41
        n = min(len(x), s.N - i)
        if n > 0 and i >= 0: s.bus[b][i:i + n] += x[:n]
    def sec(s, t):
        cur = s.secs[0]
        for x in s.secs:
            if t >= x['start'] - 1e-6: cur = x
        return cur
    def muted(s, t): return any(h - s.beat * .75 <= t < h for h in s.silence) or t >= s.end - 1e-6
    def deg(s, d, octave=5):  # scale degree (0-based, can exceed 6) → midi
        return 12 * octave + s.key + MAJOR[d % 7] + 12 * (d // 7)
    def chord(s, rn):
        d = ROMAN[rn]; root = 12 * 2 + s.key + MAJOR[d]
        while root < 36: root += 12
        while root > 47: root -= 12
        tones = [s.deg(d, 4), s.deg(d + 2, 4), s.deg(d + 4, 4)]
        ext = s.st['ext']
        if ext == 'maj7' and rn in ('I', 'IV'): tones.append(s.deg(d + 6, 4))
        elif ext == 'add9': tones.append(s.deg(d + 1, 5))
        tones = sorted([m + 12 if m < 55 else (m - 12 if m > 74 else m) for m in tones])
        return root, tones

    # ── instruments (warm by design) ──
    def piano(s, m, d=2.6, vel=.6, felt=False):
        f = hz(m); t = T(d); y = np.zeros_like(t)
        for det in (-.7, .7):
            ff = f * 2 ** (det / 1200)
            y += sum(np.sin(2 * np.pi * ff * h * np.sqrt(1 + .0004 * h * h) * t + .3 * h) * np.exp(-t * (.55 + h * .5)) / h ** (1.6 - .5 * vel) for h in range(1, 8))
        y *= np.clip(t / (.012 if felt else .005), 0, 1)
        return taper(lp(y, (1200 if felt else 1800) + 3500 * vel) * .4)
    def pluck(s, m, d=.45):
        t = T(d); ph = np.cumsum(np.full(len(t), hz(m))) / SR; x = (2 * (ph % 1) - 1) * .6 + np.sign(np.sin(2 * np.pi * ph)) * .4
        k = np.exp(-t * 18); y = lp(x, 1100) * (1 - k) + lp(x, 3000) * k
        return taper(y * np.clip(t / .002, 0, 1) * np.exp(-t / .16))
    def bassnote(s, m, d):
        t = T(d); ph = np.cumsum(np.full(len(t), hz(m))) / SR
        return taper((np.sin(2 * np.pi * ph) * .9 + lp(2 * (ph % 1) - 1, 450) * .45) * np.clip(t / .005, 0, 1) * np.clip((d - t) / .04, 0, 1), 20)
    def pad(s, notes, t0, d, g, cut=2200, att=.4):
        t = T(d); e = np.clip(t / att, 0, 1) * np.clip((d - t) / .5, 0, 1); out = np.zeros((len(t), 2))
        for m in notes:
            for v in range(3):
                ph = np.cumsum(np.full(len(t), hz(m) * (1 + (v - 1) * .004))) / SR; x = 2 * ((ph + s.rng.uniform()) % 1) - 1; an = v * .25 * np.pi
                out[:, 0] += x * np.cos(an); out[:, 1] += x * np.sin(an)
        s.add('str', lp(out, cut) * e[:, None] / (3 * len(notes)) * 2, t0, g)
    def legato(s, notes, g, cut=3600, voices=6, att=.07, rel=.3):
        if not notes: return
        t0 = notes[0][0]; t = T(max(a + d for a, d, _ in notes) + rel + .2 - t0); lf = np.zeros_like(t); env = np.zeros_like(t)
        for a, d, m in notes:
            i0 = int((a - t0) * SR); lf[i0:] = np.log(hz(m)); tt = t[i0:] - t[i0]; e = np.zeros_like(t)
            e[i0:] = np.clip(tt / att, 0, 1) * np.clip(1 - (tt - d) / rel, 0, 1); env = np.maximum(env, e)
        k = np.exp(-1 / (.04 * SR)); lf = lfilter([1 - k], [1, -k], lf, zi=[lf[0] * k])[0]; f = np.exp(lf); out = np.zeros((len(t), 2))
        for v in range(voices):
            vib = 1 + .0035 * np.sin(2 * np.pi * (5.3 + .3 * v) * t + s.rng.uniform(0, 6)); ph = np.cumsum(f * (1 + (v - (voices - 1) / 2) * .003) * vib) / SR
            x = 2 * ((ph + s.rng.uniform()) % 1) - 1; an = (.75 * (2 * v / (voices - 1) - 1) + 1) * np.pi / 4
            out[:, 0] += x * np.cos(an); out[:, 1] += x * np.sin(an)
        s.add('str', lp(lp(out, cut), cut * 1.3) * env[:, None] / voices * 1.5, t0, g)
    def kick(s):
        t = T(.5); f = 46 + 100 * np.exp(-t * 28)
        return taper(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .24) + lp(s.rng.normal(0, 1, len(t)), 2800) * np.exp(-t / .003) * .3)
    def clap(s):
        t = T(.35); n = bp(s.rng.normal(0, 1, len(t)), 900, 4000); env = sum(np.exp(-np.clip(t - o, 0, None) / .008) * (t >= o) for o in (0, .011, .022)) + np.exp(-t / .12) * .6
        return taper(n * env * .6)
    def snare(s):
        t = T(.3); return taper(lp(bp(s.rng.normal(0, 1, len(t)), 300, 4800) * np.exp(-t / .1) + np.sin(2 * np.pi * 195 * t) * np.exp(-t / .05) * .6, 6500))
    def brush(s):
        t = T(.32); return taper(bp(s.rng.normal(0, 1, len(t)), 900, 5000) * np.clip(t / .02, 0, 1) * np.exp(-t / .1))
    def hat(s, open_=False):
        t = T(.22 if open_ else .05); return taper(lp(hp(s.rng.normal(0, 1, len(t)), 6500), 10000) * np.exp(-t / (.08 if open_ else .014)))
    def tom(s, f0=120):
        t = T(.7); f = f0 * .7 + f0 * .5 * np.exp(-t * 9)
        return taper(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .3) + lp(s.rng.normal(0, 1, len(t)), 900) * np.exp(-t / .03) * .25)
    def boom(s):
        t = T(3.0); return taper(np.sin(2 * np.pi * (36 + 26 * np.exp(-t * 4)) * t) * np.exp(-t / 1.0) * np.clip(t / .008, 0, 1) + lp(s.rng.normal(0, 1, len(t)), 300) * np.exp(-t / .25) * .3)
    def crash(s, d=3.0):
        t = T(d); return taper(lp(hp(s.rng.normal(0, 1, len(t)), 2500), 7000) * np.clip(t / .005, 0, 1) * np.exp(-t / .9))
    def noise_sweep(s, d, top=5000, up=True):
        t = T(d); n = s.rng.normal(0, 1, len(t)); y = np.zeros_like(n); C = int(.02 * SR)
        for i in range(0, len(n), C):
            c = 300 + top * (i / len(n)) ** 2; seg = bp(n[max(0, i - 1500):i + C], c * .6, c * 1.3); y[i:i + C] = seg[-len(y[i:i + C]):]
        y = lp(y * (t / d) ** 2.2, 8000); return y if up else y[::-1]
    def whoosh(s, d=.8):
        t = T(d); n = s.rng.normal(0, 1, len(t)); y = np.zeros_like(n); C = int(.02 * SR)
        for i in range(0, len(n), C):
            c = 300 + 1800 * i / len(n); seg = bp(n[max(0, i - 1500):i + C], c * .6, c * 1.4); y[i:i + C] = seg[-len(y[i:i + C]):]
        return taper(y * np.sin(np.pi * t / d) ** 2)
    def thud(s):
        t = T(.3); return taper(lp(s.rng.normal(0, 1, len(t)), 800) * np.exp(-t / .035) * .6 + np.sin(2 * np.pi * 100 * t) * np.exp(-t / .06) * .45)
    def scribble(s, d):
        t = T(d); n = bp(s.rng.normal(0, 1, len(t)), 900, 3500); env = np.zeros_like(t); k = 0
        while k < d:
            L = s.rng.uniform(.08, .22); i0, i1 = int(k * SR), int(min(d, k + L) * SR)
            if i1 > i0: env[i0:i1] = np.sin(np.linspace(0, np.pi, i1 - i0)) * s.rng.uniform(.5, 1)
            k += L + s.rng.uniform(.02, .08)
        return taper(n * env)
    def popfx(s):
        t = T(.12); f = 300 + 500 * np.exp(-t * 40); return taper(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .03))
    def click(s):
        t = T(.03); return taper(lp(s.rng.normal(0, 1, len(t)), 3000) * np.exp(-t / .004), 5)

    # ── melody: a 4-bar phrase built from chord tones, repeated (catchy), seeded ──
    def phrase(s):
        prog = s.st['prog']; mel = []; prev = s.deg(2, 5)
        for bi, rn in enumerate(prog):
            _, tones = s.chord(rn); r = RHYTHMS[int(s.rng.integers(0, len(RHYTHMS)))]
            ct = sorted({m + 12 * k for m in tones for k in (0, 1) if 62 <= m + 12 * k <= 78})
            scale = [s.deg(d, 4) for d in range(0, 14) if 62 <= s.deg(d, 4) <= 79]
            for i, (b, d) in enumerate(r):
                if i == 0: p = min(ct, key=lambda m: abs(m - prev) + (0 if m != prev else 1.5))
                else:
                    near = [m for m in scale if 0 < abs(m - prev) <= 4]; p = near[int(s.rng.integers(0, len(near)))] if near else prev
                    if i == len(r) - 1: p = min(ct, key=lambda m: abs(m - p))
                mel.append((bi, b, d, p)); prev = p
        return mel

    def build(s):
        st = s.st; prog = st['prog']; P = s.phrase(); nb = int(np.ceil(s.end / s.bar)); lines = []
        for j in range(nb):
            t0 = j * s.bar; rn = prog[j % 4]; root, tones = s.chord(rn); S = s.sec(t0 + .01); e = S['energy']; build = S.get('build')
            if t0 >= s.end - 1e-6: break
            def ok(t): return t < s.end - .01 and not s.muted(t)
            vel = .45 + .45 * e; felt = st['groove'] == 'soft'
            # keys: chord + bass note
            if ok(t0):
                s.add('keys', s.piano(root + 12, 3.0, vel, felt), t0, .16)
                for i, m in enumerate(tones): s.add('keys', s.piano(m, 2.4, vel, felt), t0 + .01 * i, .07, .2 * (i - 1.5))
            # arpeggio / ostinato
            if e >= .2:
                arp = [tones[0], tones[1], tones[2], tones[-1], tones[2], tones[1], tones[2], tones[-1]] if st['arp'] == 'piano' else [tones[0] + 12, tones[1], tones[2], tones[1] + 12, tones[0] + 12, tones[2], tones[1], tones[2]]
                sub = 8 if (st['arp'] == 'pluck' and e >= .45) else 4 if e < .45 else 8
                for k in range(sub):
                    tt = t0 + k * s.bar / sub
                    if not ok(tt): continue
                    m = arp[k % len(arp)]
                    if st['arp'] == 'pluck': s.add('arp', s.pluck(m - 12), tt, (.05 + .04 * e) * (1 if k % 2 == 0 else .8), .45 * (-1) ** k)
                    else: s.add('arp', s.piano(m, 2.0, vel * .85, felt), tt, (.04 + .03 * e) * (1 if k % 2 == 0 else .8), .3 * (-1) ** k)
            # pad / strings bed
            if e >= .2: s.pad([m - 12 if m > 64 else m for m in tones], t0, s.bar + .3, .08 + .14 * e, 1600 + 2200 * e, .5 if e < .6 else .1)
            # bass
            if e >= .45:
                for k in range(8 if st['groove'] in ('pop', 'light') else 4):
                    step = s.bar / (8 if st['groove'] in ('pop', 'light') else 4); tt = t0 + k * step
                    if ok(tt): s.add('bass', s.bassnote(root, step * .9), tt, (.22 if k % 2 else .12) if st['groove'] in ('pop', 'light') else .18)
            elif e >= .2 and ok(t0): s.add('bass', s.bassnote(root, s.bar * .95), t0, .12)
            # drums
            if e >= .45 or build:
                for k in range(4):
                    tt = t0 + k * s.beat
                    if not ok(tt): continue
                    g = st['groove']; full = e >= .75
                    if build:
                        s.add('drm', s.kick(), tt, .5); s.kicks.append(tt)
                        nxt = [x['start'] for x in s.secs if x['start'] > t0]; tend = min(nxt) if nxt else s.end
                        prog_ = (tt - S['start']) / max(.1, tend - S['start']); div = 2 if prog_ < .5 else 4 if prog_ < .8 else 8
                        for q in range(div):
                            ts = tt + q * s.beat / div
                            if ok(ts) and ts < tend: s.add('drm', s.snare(), ts, .06 + .22 * prog_ ** 1.5, .1 * (-1) ** q)
                        continue
                    if k in (0, 2) and (g != 'soft' or k == 0 or full): s.add('drm', s.kick(), tt, .6 if full else .45); s.kicks.append(tt)
                    if k in (1, 3):
                        if g in ('pop', 'light'): s.add('drm', s.clap(), tt, .36 if full else .26)
                        elif g == 'epic': s.add('drm', s.snare(), tt, .4 if full else .25); full and s.add('drm', s.tom(90), tt, .2)
                        else: s.add('drm', s.brush(), tt, .12)
                    if g in ('pop', 'light'): s.add('drm', s.hat(k % 2 == 1 and full), tt + s.beat / 2, .05, .4)
                    if g == 'epic' and full: s.add('drm', s.tom(140), tt + s.beat / 2, .16, -.4)
            # melody: keys when quiet, strings (doubled an octave below) when energetic
            for (bi, b, d, p) in [x for x in P if x[0] == j % 4]:
                tt = t0 + b * s.beat
                if not ok(tt): continue
                if e < .45: s.add('keys', s.piano(p, 2.6, vel + .1, felt), tt, .14, .05)
                else: lines.append((tt, d * s.beat * .97, p, e))
        # string lines (contiguous runs)
        if lines:
            run = [lines[0]]
            for x in lines[1:] + [None]:
                if x is not None and x[0] - (run[-1][0] + run[-1][1]) < s.beat * 1.1: run.append(x); continue
                e = max(r[3] for r in run); s.legato([(a, d, m) for a, d, m, _ in run], .14 + .14 * e, 3000 + 1800 * e)
                if e >= .75: s.legato([(a, d, m - 12) for a, d, m, _ in run], .12 + .08 * e, 2400)
                if x is not None: run = [x]
        # hits & ending
        for h in s.c.get('hits', []):
            s.add('sfx', s.boom(), h, .45); s.add('sfx', s.crash(), h, .05)
        root, tones = s.chord('I'); fin = s.D - s.end
        for i, m in enumerate([root, root + 12] + tones): s.add('keys', s.piano(m, fin, .6, st['groove'] == 'soft'), s.end + .012 * i, .2 if m < 48 else .12)
        s.pad(tones, s.end, fin, .2, 2400, .05); s.legato([(s.end, fin * .8, max(tones))], .16, 3600)
        # SFX
        for c in s.c.get('cuts', []): s.add('sfx', s.whoosh(), c - .4, .05)
        for x in s.c.get('sfx', []):
            ty, t = x['type'], x['t']; d = x.get('dur', 1.0); g = x.get('gain', 1.0)
            if ty == 'write': s.add('sfx', s.scribble(d), t, .02 * g, .15)
            elif ty == 'thud': s.add('sfx', s.thud(), t, .16 * g, s.rng.uniform(-.3, .3))
            elif ty == 'ding': s.add('keys', s.piano(x.get('note', s.deg(4, 5)), 2.0, .75), t, .11 * g, .25)
            elif ty == 'riser': s.add('sfx', s.noise_sweep(d, 5500), t, .07 * g)
            elif ty == 'sweep': s.add('sfx', s.noise_sweep(d, 3500, up=False), t, .03 * g)
            elif ty == 'boom': s.add('sfx', s.boom(), t, .35 * g)
            elif ty == 'whoosh': s.add('sfx', s.whoosh(d), t, .06 * g)
            elif ty == 'pop': s.add('sfx', s.popfx(), t, .06 * g)
            elif ty == 'click': s.add('sfx', s.click(), t, .08 * g)
            elif ty == 'file': s.add('sfx', load_audio(cue_path(s.c, x['path'])), t, .5 * g, x.get('pan', 0))

    def mix(s, sfx_only=False):
        rng = s.rng
        def reverb(x, decay, mixv, cut=8000):
            t = T(decay * 2.5); o = x.copy()
            for ch in range(2):
                ir = lp(bp(rng.normal(0, 1, len(t)) * np.exp(-t / decay * 2.3), 150, 10000), cut); ir /= np.sqrt((ir ** 2).sum())
                o[:, ch] += mixv * fftconvolve(x[:, ch], ir)[:len(x)]
            return o
        tt = np.arange(s.N) / SR; duck = np.ones(s.N); vo = None
        if s.c.get('voice'):
            import subprocess
            V = s.c['voice']; raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', cue_path(s.c, V['file']), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
            v = np.frombuffer(raw, np.int16).astype(np.float64) / 32768; vo = np.zeros(s.N); vo[:min(s.N, len(v))] = v[:s.N]
            e = lp(np.abs(vo), 5); e /= e.max() + 1e-9; depth = 1 - 10 ** (-V.get('duck_db', 8) / 20)
            duck = lp(1 - depth * np.clip(e * 3.5, 0, 1), 3)
        for h in s.silence:
            m = (tt >= h - s.beat * .75) & (tt < h); duck[m] = np.clip(1 - (tt[m] - (h - s.beat * .75)) / .1, .06, 1)
        sc = np.ones(s.N)
        if s.st['groove'] in ('pop', 'light'):
            for kt in s.kicks:
                i = int(kt * SR); L = int(.3 * SR)
                if i + L < s.N: sc[i:i + L] = np.minimum(sc[i:i + L], 1 - .3 * np.exp(-np.arange(L) / SR / .09))
        R = s.st['rev']; b = s.bus
        sfx = reverb(b['sfx'], 1.6, .2) * (.6 + .4 * duck)[:, None]
        if sfx_only: out = sfx
        else:
            music = (reverb(b['keys'], R, .28) + reverb(b['arp'], R * .8, .24) * sc[:, None] * .9 + reverb(b['str'], R * 1.2, .32) * sc[:, None]
                     + b['bass'] * sc[:, None] * .9 + reverb(b['drm'], 1.2, .12, 6000) * .75) * duck[:, None]
            out = music + sfx * .85
        out = hp(lp(out, s.st['lpf'], 2), 30)
        out /= np.abs(out).max() + 1e-9; out = np.tanh(out * 1.35) / np.tanh(1.35)
        if vo is not None and not sfx_only:   # voice stays dry and clear on top
            vo = hp(vo, 85); vo = vo / (np.abs(vo).max() + 1e-9) * s.c['voice'].get('gain', 1.0)
            out = out * .5 + np.stack([vo, vo], 1) * .85; out /= np.abs(out).max() + 1e-9; out = np.tanh(out * 1.2) / np.tanh(1.2)
        fi = int(.4 * SR); out[:fi] *= np.linspace(0, 1, fi)[:, None]
        fo = int(min(2.0, s.D - s.end) * SR)
        if fo > 0: out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
        return out * (.93 / (np.abs(out).max() + 1e-9))

def cue_path(c, p):
    import os
    return p if os.path.isabs(p) else os.path.join(c.get('_dir', '.'), p)

def load_audio(path):
    import subprocess
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cue'); ap.add_argument('--out', default='music.wav'); ap.add_argument('--sfx-only', action='store_true')
    a = ap.parse_args(); cue = json.load(open(a.cue)); cue['_dir'] = __import__('os').path.dirname(__import__('os').path.abspath(a.cue)); sc = Score(cue); sc.build(); out = sc.mix(a.sfx_only)
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    print(a.out, f'{sc.D:.1f}s', cue.get('style', 'uplifting'), f"{sc.bpm:.0f}bpm key {cue.get('key', 'D')}")

if __name__ == '__main__':
    main()
