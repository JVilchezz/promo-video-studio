#!/usr/bin/env python3
"""Promo Video Studio · voice.py — voice-over tools (ElevenLabs or any recording).

0) Check the key and pick a voice:
   python3 voice.py check                      # is ELEVENLABS_API_KEY set and valid? (exit 2 = no key, 3 = rejected/blocked)
   python3 voice.py voices [--search spanish]  # list the account's voices: name · voice_id · accent · gender · use

   NO KEY? Tell the user in one line and offer (in this order):
     a) create a free account at elevenlabs.io → Profile → API keys → paste the key here (+ pick a voice);
     b) record the script with their phone, or export it from any text-to-speech app, and send the audio
        → `align` below makes the word timings from the script, so captions still sync;
     c) no voice: on-screen text + captions + music (the default style — it works great).
   Never fall back to a robotic offline voice without asking.

1) Generate with ElevenLabs (needs ELEVENLABS_API_KEY and network access):
   python3 voice.py tts --text-file script.txt --voice-id <VOICE_ID> --out vo.mp3 --words words.json
       [--model eleven_multilingual_v2 --stability .5 --similarity .75 --style 0 --speed 1.0]
   → vo.mp3 + words.json  [{"w":"Hola","t0":0.12,"t1":0.41}, …]  (exact word timings for captions)
   No API access? Generate the audio in elevenlabs.io (Text to Speech → download MP3), give the file
   to Claude and continue with step 2.

2) Find the phrases in any voice file (ElevenLabs download, a recording…):
   python3 voice.py phrases vo.mp3 --out phrases.json [--thresh -38 --min-silence 0.28]
   → [[0.06,1.64],[1.99,4.10],…]  start/end of each spoken phrase (by silence detection)

3) Place each phrase exactly where the picture needs it (and leave room for music/visual beats):
   python3 voice.py place vo.mp3 --plan plan.json --duration 49.6 --out voice_track.wav
   plan.json = [[src_start, src_end, dst_time], …]   e.g. [[0.06,1.64,0.4],[1.99,4.10,3.5]]
   → a dry, cleaned (high-pass 85 Hz, de-clicked, normalized) voice track on the video timeline.
   Then add  "voice": {"file": "voice_track.wav"}  to cue.json — score.py ducks the music under it.

3b) Any recording + its script → word timings (no API needed):
   python3 voice.py align recording.m4a --script script.txt --out words.json
   → same words.json format as `tts` (spread over the detected speech by syllable weight; check the captions
     in the preview and nudge with --offset if needed)

4) Captions from word timings:
   python3 voice.py captions words.json --max-words 6 --offset 3.5 --out captions.json
   → [[t0,t1,'sub',null,'text',[[w0,w1],…]], …]  ready for captions() in motion.js

Voice rules: natural voices only (pick from the ElevenLabs Voice Library, multilingual v2 model for
Spanish), keep it DRY (no room reverb — it sounds "like in a room"), music ducks ~6–9 dB under it.
"""
import argparse, base64, json, os, subprocess, sys, wave
import numpy as np
from pvs_env import ffmpeg

SR = 44100

def load(path):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def save(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())

NO_KEY = ("NO_KEY: ELEVENLABS_API_KEY is not set. Options for the user: (a) free elevenlabs.io account → API key + voice; "
          "(b) send a recording of the script (own voice or any TTS app) → voice.py align; (c) no voice-over: text + captions + music.")

def api(path, key, timeout=30):
    import urllib.request
    return json.load(urllib.request.urlopen(urllib.request.Request('https://api.elevenlabs.io' + path, headers={'xi-api-key': key}), timeout=timeout))

def cmd_check(a):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key: print(NO_KEY); sys.exit(2)
    try: n = len(api('/v1/voices', key).get('voices', [])); print(json.dumps({'ok': True, 'voices': n}))
    except Exception as e:
        msg = str(e); print(json.dumps({'ok': False, 'error': msg[:200], 'hint': 'key rejected — ask the user to copy it again' if '401' in msg
                                        else 'api.elevenlabs.io not reachable from here — use a recording + voice.py align'})); sys.exit(3)

def cmd_voices(a):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key: print(NO_KEY); sys.exit(2)
    for v in api('/v1/voices', key).get('voices', []):
        lab = v.get('labels') or {}; row = f"{v.get('name')} · {v.get('voice_id')} · {lab.get('accent', '')} · {lab.get('gender', '')} · {lab.get('age', '')} · {lab.get('use_case', lab.get('use case', ''))}"
        if not a.search or a.search.lower() in row.lower() + json.dumps(lab).lower(): print(row)

def cmd_tts(a):
    import urllib.request
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key: print(NO_KEY, file=sys.stderr); sys.exit(2)
    text = open(a.text_file, encoding='utf-8').read().strip()
    body = {'text': text, 'model_id': a.model, 'voice_settings': {'stability': a.stability, 'similarity_boost': a.similarity, 'style': a.style, 'use_speaker_boost': True, 'speed': a.speed}}
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{a.voice_id}/with-timestamps?output_format=mp3_44100_128',
                                 data=json.dumps(body).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    try: res = json.load(urllib.request.urlopen(req, timeout=180))
    except Exception as e: sys.exit(f'ElevenLabs request failed: {e}\nIf the network is blocked here, generate the MP3 on elevenlabs.io and use `phrases`.')
    open(a.out, 'wb').write(base64.b64decode(res['audio_base64']))
    al = res.get('alignment') or res.get('normalized_alignment') or {}
    words, cur, t0, t1 = [], '', None, None
    for ch, s, e in zip(al.get('characters', []), al.get('character_start_times_seconds', []), al.get('character_end_times_seconds', [])):
        if ch.isspace():
            if cur: words.append({'w': cur, 't0': round(t0, 3), 't1': round(t1, 3)}); cur = ''
            continue
        if not cur: t0 = s
        cur += ch; t1 = e
    if cur: words.append({'w': cur, 't0': round(t0, 3), 't1': round(t1, 3)})
    if a.words: json.dump(words, open(a.words, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(json.dumps({'audio': a.out, 'words': len(words), 'duration': words[-1]['t1'] if words else None}))

def detect(x, thresh=-38, min_silence=.28):
    hop = int(.01 * SR); n = len(x) // hop
    rms = np.sqrt(np.convolve(x[:n * hop].reshape(n, hop).astype(np.float64) ** 2 @ np.ones(hop) / hop, np.ones(3) / 3, 'same')) + 1e-9
    voiced = 20 * np.log10(rms) > thresh; ms = int(min_silence * 100)
    runs, i = [], 0                                   # voiced runs [start,end) in 10 ms frames
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]: j += 1
            runs.append([i, j]); i = j
        else: i += 1
    merged = []
    for r in runs:                                    # join runs separated by short pauses
        if merged and r[0] - merged[-1][1] < ms: merged[-1][1] = r[1]
        else: merged.append(r)
    return [[round(max(0, s / 100 - .03), 2), round(min(len(x) / SR, e / 100 + .05), 2)] for s, e in merged if e - s >= 8]

def cmd_phrases(a):
    out = detect(load(a.file), a.thresh, a.min_silence)
    json.dump(out, open(a.out, 'w')); print(json.dumps({'phrases': len(out), 'list': out}))

def cmd_align(a):
    import re
    ph = detect(load(a.file), a.thresh, a.min_silence)
    if not ph: sys.exit('No speech found — is the file silent? Try --thresh -45')
    words = open(a.script, encoding='utf-8').read().split()
    if not words: sys.exit('The script is empty')
    weight = lambda w: max(1, len(re.findall(r'[aeiouáéíóúüy]+', w.lower()))) + (1.5 if w[-1:] in '.!?…' else .6 if w[-1:] in ',;:' else 0)
    # one-to-one when the script's sentences match the detected phrases, else spread over all speech
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if w[-1:] in '.!?…,;:': chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    groups = list(zip(chunks, ph)) if len(chunks) == len(ph) else None
    if not groups:   # map cumulative weight onto the concatenated speech time
        tot = sum(e - s for s, e in ph); W = [weight(w) for w in words]; S = sum(W); acc = 0; out = []
        def at(f):
            d = f * tot
            for s, e in ph:
                if d <= e - s: return s + d
                d -= e - s
            return ph[-1][1]
        for w, k in zip(words, W):
            t0 = at(acc / S); acc += k; t1 = at(acc / S); out.append({'w': w, 't0': round(t0, 3), 't1': round(max(t1 - .02, t0 + .05), 3)})
    else:
        out = []
        for ws, (s, e) in groups:
            W = [weight(w) for w in ws]; S = sum(W); acc = 0
            for w, k in zip(ws, W):
                t0 = s + (e - s) * acc / S; acc += k; t1 = s + (e - s) * acc / S; out.append({'w': w, 't0': round(t0, 3), 't1': round(t1 - .02, 3)})
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(json.dumps({'words': len(out), 'phrases': len(ph), 'mode': 'sentence-per-phrase' if groups else 'proportional', 'out': a.out}))

def cmd_place(a):
    from scipy.signal import butter, sosfilt
    x = load(a.file); plan = json.load(open(a.plan)); N = int(a.duration * SR); v = np.zeros(N, np.float32)
    for s0, s1, dst in plan:
        seg = x[max(0, int((s0 - .05) * SR)):int((s1 + .15) * SR)].copy()
        f1, f2 = int(.01 * SR), int(.05 * SR); seg[:f1] *= np.linspace(0, 1, f1); seg[-f2:] *= np.linspace(1, 0, f2)
        k = int((dst - .05) * SR); m = min(len(seg), N - k)
        if m > 0: v[k:k + m] += seg[:m]
    v = sosfilt(butter(2, 85, 'high', fs=SR, output='sos'), v)
    v = v / (np.abs(v).max() + 1e-9) * .9; save(a.out, v); print(json.dumps({'out': a.out, 'phrases': len(plan), 'duration': a.duration}))

def cmd_captions(a):
    W = json.load(open(a.file, encoding='utf-8')); caps, cur = [], []
    def flush():
        if cur: caps.append([round(cur[0]['t0'] + a.offset, 2), round(cur[-1]['t1'] + a.offset + .25, 2), 'sub', None, ' '.join(w['w'] for w in cur), [[round(w['t0'] + a.offset, 2), round(w['t1'] + a.offset, 2)] for w in cur]])
    for w in W:
        cur.append(w)
        if len(cur) >= a.max_words or w['w'][-1:] in '.!?,;:…': flush(); cur = []
    flush(); json.dump(caps, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False); print(json.dumps({'captions': len(caps)}))

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('tts'); p.add_argument('--text-file', required=True); p.add_argument('--voice-id', required=True); p.add_argument('--out', default='vo.mp3')
    p.add_argument('--words', default='words.json'); p.add_argument('--model', default='eleven_multilingual_v2'); p.add_argument('--stability', type=float, default=.5)
    p.add_argument('--similarity', type=float, default=.75); p.add_argument('--style', type=float, default=0); p.add_argument('--speed', type=float, default=1.0)
    p = sp.add_parser('phrases'); p.add_argument('file'); p.add_argument('--out', default='phrases.json'); p.add_argument('--thresh', type=float, default=-38); p.add_argument('--min-silence', type=float, default=.28)
    p = sp.add_parser('place'); p.add_argument('file'); p.add_argument('--plan', required=True); p.add_argument('--duration', type=float, required=True); p.add_argument('--out', default='voice_track.wav')
    p = sp.add_parser('check'); p = sp.add_parser('voices'); p.add_argument('--search')
    p = sp.add_parser('align'); p.add_argument('file'); p.add_argument('--script', required=True); p.add_argument('--out', default='words.json')
    p.add_argument('--thresh', type=float, default=-38); p.add_argument('--min-silence', type=float, default=.28)
    p = sp.add_parser('captions'); p.add_argument('file'); p.add_argument('--max-words', type=int, default=6); p.add_argument('--offset', type=float, default=0); p.add_argument('--out', default='captions.json')
    a = ap.parse_args(); {'tts': cmd_tts, 'phrases': cmd_phrases, 'place': cmd_place, 'captions': cmd_captions,
                              'check': cmd_check, 'voices': cmd_voices, 'align': cmd_align}[a.cmd](a)

if __name__ == '__main__':
    main()
