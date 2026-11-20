# Voice-over (ElevenLabs) and captions

Only when the client wants a voice. Default is text on screen + music.

## 1 · Write the script for the ear
Short sentences (≤ 12 words), one idea each, written the way the audience talks (Costa Rican "vos",
Mexican "tú", etc.). Read it out loud at ~2.5 words/s → that's the timing budget. Write numbers as words
if the voice mispronounces them; use punctuation to shape pauses ("…", ",").

## 2 · Generate it
First: `python3 SKILL_DIR/scripts/voice.py check` (exit 2 = no key, 3 = key rejected or ElevenLabs
blocked from here). With a key, `voice.py voices --search spanish` lists the account's voices and IDs.

**No key?** Say it in one line and offer: (a) a free elevenlabs.io account → API key + voice;
(b) they send a recording of the script (their voice, a teammate's, or any text-to-speech app) →
`voice.py align recording.m4a --script script.txt --out words.json` gives word timings so captions still
sync; (c) no voice — text + captions + music. Never switch to a robotic offline voice without asking.

**Option A — the client (or you) uses elevenlabs.io:** Text to Speech → pick a natural voice from the Voice
Library (warm, conversational; test 2–3), model *Multilingual v2* for Spanish, stability ~0.5,
similarity ~0.75, style 0 → download MP3 → send it.
**Option B — API** (needs `ELEVENLABS_API_KEY` and network):
```bash
python3 SKILL_DIR/scripts/voice.py tts --text-file script.txt --voice-id <ID> --out vo.mp3 --words words.json
```
`words.json` has the exact time of every word → perfect captions.
Never use robotic voices or add room reverb ("sounds like it's in a room"). If the client says the voice
sounds weird, try another voice, lower stability a bit, or go back to text-only.

## 3 · Fit it to the picture
```bash
python3 SKILL_DIR/scripts/voice.py phrases vo.mp3 --out phrases.json        # find each spoken phrase
# write plan.json: [[src_start, src_end, video_time], …] — where each phrase should start in the video
python3 SKILL_DIR/scripts/voice.py place vo.mp3 --plan plan.json --duration 49.6 --out voice_track.wav
```
Leave the hook, the logo reveal and the end free of voice; let big visual moments breathe. Re-time
scenes to the voice, not the other way around.

## 4 · Captions
```bash
python3 SKILL_DIR/scripts/voice.py captions words.json --max-words 6 --offset 3.5 --out captions.json
```
In the page: `const C=captions('caps', CAPS); … C.update(t)` — `cap` pills (icon + short instruction) for
steps, `sub` quotes for spoken user lines (word-by-word highlight). Keep captions above the bottom safe zone.

## 5 · Mix
Add `"voice": {"file": "voice_track.wav", "duck_db": 8}` to `cue.json`. score.py ducks music under the
voice (≈ 6–9 dB), keeps the voice dry and clear on top, and lowers SFX a little while someone speaks.
