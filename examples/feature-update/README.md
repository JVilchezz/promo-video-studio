# Example · new version / feature update (vertical)

26 s: "NEW VERSION 2.0" (letter-spacing collapsing + back-eased pop) → mascot glory moment with rotating
`rays`, glow and `sparkles` → phone demo of the new feature with `captions()` (icon pills + quoted
subtitle) → mascot waving + "UPDATE AURORA" + store `.badge`s. Fictional brand.

**Add a voice-over** (see `reference/voiceover.md`):
```bash
SK=../../plugins/promo-video-studio/skills/promo-video-studio/scripts
python3 $SK/voice.py tts --text-file script.txt --voice-id <VOICE_ID> --out vo.mp3 --words words.json
python3 $SK/voice.py phrases vo.mp3 --out phrases.json            # where each phrase starts/ends
python3 $SK/voice.py place vo.mp3 --plan plan.json --duration 26 --out voice_track.wav
python3 $SK/voice.py captions words.json --offset 0 --out caps.json  # → CAPS in video.html
```
then set `"voice": {"file": "voice_track.wav", "duck_db": 9}` in `cue.json` and rebuild. With a real
screen recording, replace the HTML phone UI with frames from `recording.py`.

```bash
bash ../build.sh feature-update
```
