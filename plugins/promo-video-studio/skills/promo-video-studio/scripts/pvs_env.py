"""Promo Video Studio · shared helpers to find the tools the scripts need on any machine
(Linux, macOS, Windows, cloud sandboxes). Imported by the other scripts — not run directly."""
import os, shutil

def ffmpeg():
    """Path to an ffmpeg binary: $PVS_FFMPEG → ffmpeg on PATH → the static build from `pip install imageio-ffmpeg`."""
    p = os.environ.get('PVS_FFMPEG') or shutil.which('ffmpeg')
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    raise SystemExit('ffmpeg not found. Fix: pip install imageio-ffmpeg  (or install ffmpeg: apt install ffmpeg · '
                     'brew install ffmpeg · winget install ffmpeg). Run scripts/doctor.py --fix to do it automatically.')

def launch_chromium(p):
    """Start headless Chromium with Playwright: bundled build → installed Chrome / Edge → chromium on PATH."""
    errs = []
    for kw in ({}, {'channel': 'chrome'}, {'channel': 'msedge'}):
        try: return p.chromium.launch(**kw)
        except Exception as e: errs.append(str(e).splitlines()[0])
    for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable', 'chrome'):
        exe = shutil.which(name)
        if exe:
            try: return p.chromium.launch(executable_path=exe)
            except Exception as e: errs.append(str(e).splitlines()[0])
    raise SystemExit('Chromium could not start. Fix: python3 -m playwright install chromium  (or install Google Chrome). '
                     'Run scripts/doctor.py --fix to try automatically.\nFirst error: ' + (errs[0] if errs else '?'))
