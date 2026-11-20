#!/usr/bin/env python3
"""Promo Video Studio · doctor.py — check (and fix) everything the studio needs, BEFORE starting a video.

  python3 doctor.py                 # check: Python packages, ffmpeg, Chromium, fonts, ElevenLabs key
  python3 doctor.py --fix           # install what is missing (pip packages, static ffmpeg, Chromium)
  python3 doctor.py --online        # also verify the ElevenLabs key against the API
  python3 doctor.py --render-test   # 1-second end-to-end test: page → frames → MP4 + music

The last line is a summary Claude must translate for the user, e.g.
  READY  video: yes · music: yes · voice-over: no (ELEVENLABS_API_KEY not set)
Anything "no" → follow "When something is missing" in SKILL.md (tell the user in one line + offer options).
"""
import argparse, importlib, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PKGS = [('playwright', 'playwright'), ('numpy', 'numpy'), ('scipy', 'scipy'), ('PIL', 'pillow'), ('cv2', 'opencv-python-headless')]
ok = lambda m: print(f'  OK    {m}'); bad = lambda m: print(f'  MISS  {m}'); info = lambda m: print(f'  --    {m}')

def pip(*names):
    base = [sys.executable, '-m', 'pip', 'install', '-q', *names]
    r = subprocess.run(base); return r.returncode == 0 or subprocess.run(base + ['--break-system-packages']).returncode == 0

def check_pkgs(fix):
    missing = []
    for mod, pkg in PKGS:
        try: importlib.import_module(mod)
        except Exception: missing.append(pkg)
    if missing and fix: pip(*missing); importlib.invalidate_caches(); return check_pkgs(False)
    (bad(f'python packages: {" ".join(missing)}  → pip install {" ".join(missing)}') if missing else ok('python packages: playwright numpy scipy pillow opencv'))
    return not missing

def check_ffmpeg(fix):
    sys.path.insert(0, HERE)
    try:
        from pvs_env import ffmpeg
        p = ffmpeg(); v = subprocess.run([p, '-version'], capture_output=True, text=True).stdout.split('\n')[0]
        ok(f'ffmpeg: {v[:60]}'); return True
    except SystemExit:
        if fix and pip('imageio-ffmpeg'): importlib.invalidate_caches(); return check_ffmpeg(False)
        bad('ffmpeg  → pip install imageio-ffmpeg  (or apt/brew/winget install ffmpeg)'); return False

def check_chromium(fix):
    try:
        from playwright.sync_api import sync_playwright
        from pvs_env import launch_chromium
    except Exception:
        bad('Chromium (playwright not installed)'); return False
    try:
        with sync_playwright() as p:
            b = launch_chromium(p); v = b.version; b.close()
        ok(f'Chromium {v}'); return True
    except SystemExit as e:
        if fix:
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'])
            if sys.platform.startswith('linux'): subprocess.run([sys.executable, '-m', 'playwright', 'install-deps', 'chromium'], capture_output=True)
            return check_chromium(False)
        bad('Chromium  → python3 -m playwright install chromium  (needs internet; or install Google Chrome)'); return False

def check_fonts():
    fd = os.path.join(ROOT, 'assets', 'fonts'); n = len([f for f in os.listdir(fd) if f.endswith('.woff2')]) if os.path.isdir(fd) else 0
    (ok(f'fonts: {n} files') if n else bad('fonts missing in assets/fonts (re-install the skill)')); return n > 0

def check_voice(online):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        info('voice-over: ELEVENLABS_API_KEY not set → ask the user for a key + voice ID, or use a recording (voice.py align), or no voice')
        return False, 'ELEVENLABS_API_KEY not set'
    if not online: ok('voice-over: ELEVENLABS_API_KEY is set (use --online to verify it)'); return True, ''
    import urllib.request
    for url in ('https://api.elevenlabs.io/v1/user', 'https://api.elevenlabs.io/v1/voices'):
        try:
            urllib.request.urlopen(urllib.request.Request(url, headers={'xi-api-key': key}), timeout=20); ok('voice-over: ElevenLabs key works'); return True, ''
        except Exception as e: err = str(e)
    if '401' in err: bad('voice-over: the ElevenLabs key was rejected (401) → ask the user to check/copy it again'); return False, 'key rejected'
    bad(f'voice-over: cannot reach api.elevenlabs.io ({err[:80]}) → network blocked here: use a recording (voice.py align)'); return False, 'ElevenLabs not reachable'

def render_test():
    tmp = tempfile.mkdtemp(prefix='pvs_test_'); html = os.path.join(tmp, 'video.html')
    open(html, 'w').write('<!doctype html><meta charset="utf-8"><meta name="pvs-size" content="360x640"><body style="margin:0;background:#1F3480">'
                          '<div id="x" style="font:700 60px sans-serif;color:#F2C352;padding:200px 40px">PVS</div>'
                          '<script>window.R=t=>{x.style.transform=`translateY(${-t*80}px)`};window.READY=true</script>')
    json.dump({'duration': 2, 'style': 'minimal', 'bpm': 90, 'key': 'D', 'seed': 1, 'sections': [{'start': 0, 'energy': .5}], 'end': 1.5}, open(os.path.join(tmp, 'cue.json'), 'w'))
    r1 = subprocess.run([sys.executable, os.path.join(HERE, 'render.py'), html, 'full', '--dur', '1', '--out', os.path.join(tmp, 's.mp4')], capture_output=True, text=True)
    r2 = subprocess.run([sys.executable, os.path.join(HERE, 'score.py'), os.path.join(tmp, 'cue.json'), '--out', os.path.join(tmp, 'm.wav')], capture_output=True, text=True)
    good = r1.returncode == 0 and os.path.getsize(os.path.join(tmp, 's.mp4')) > 1000 if os.path.exists(os.path.join(tmp, 's.mp4')) else False
    (ok('render test: 1 s MP4 rendered') if good else bad('render test failed: ' + (r1.stderr or r1.stdout)[-300:]))
    (ok('music test: score rendered') if r2.returncode == 0 else bad('music test failed: ' + r2.stderr[-300:]))
    shutil.rmtree(tmp, ignore_errors=True); return good and r2.returncode == 0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fix', action='store_true'); ap.add_argument('--online', action='store_true'); ap.add_argument('--render-test', action='store_true')
    a = ap.parse_args(); print(f'Promo Video Studio · environment check (Python {sys.version.split()[0]})')
    if sys.version_info < (3, 9): bad('Python 3.9+ required')
    pk = check_pkgs(a.fix); ff = check_ffmpeg(a.fix); ch = check_chromium(a.fix) if pk or a.fix else False; fo = check_fonts()
    vo, why = check_voice(a.online)
    video = pk and ff and ch and fo; music = pk and ff
    if a.render_test and video: video = render_test()
    yn = lambda b: 'yes' if b else 'no'
    print(f"READY  video: {yn(video)} · music: {yn(music)} · voice-over: {yn(vo)}{f' ({why})' if not vo else ''}")
    sys.exit(0 if video else 1)

if __name__ == '__main__':
    main()
