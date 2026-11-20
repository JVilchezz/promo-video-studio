# Sound design & brand sounds

## In videos
`score.py` handles music + cue-sheet SFX. Placement rules that make a video feel expensive:
- **whoosh** starts 0.35–0.45 s before a cut so it peaks on the cut · **boom** exactly on reveals (logo, award)
  · **half-beat silence** before the biggest reveal · **riser** 1.5–2.5 s into it.
- **paper thud** when a polaroid lands · **pencil scribble** for the whole duration of handwriting ·
  **ding** per notification/name circled (notes of the key, rising) · **pop** when an icon/badge pops ·
  **typing** under typed headlines · **soft air sweep** with light sweeps.
- **Chat / app scenes**: put the `sfx_pack.py` sounds on the timeline with `{"type":"file","t":2.9,"path":"sounds/receive.wav"}`
  — send on every "me" bubble, receive on "them", typing under the typing dots, the notification sound when the
  banner drops (see `examples/chat-story/cue.json`).
- SFX sit under the music, never like a video game. Nothing piercing: no sine "sparkles" above ~2 kHz.

## Brand / app sounds (`sfx_pack.py`)
```bash
python3 SKILL_DIR/scripts/sfx_pack.py --out sounds --key D --mp3
```
Makes a family of sounds in one key: 4 notification options (soft bell, marimba, ding-ding, pop + chord),
success, error (gentle), tap, click, toggle, send, receive, typing, swipe, whoosh, riser, boom, sparkle,
paper, shutter and a 2-second **sonic logo**. Deliver 3–4 notification options for the client to choose;
render a short preview video for each (app icon + waveform, or the notification mockup) so they can
listen on their phone. For iOS push sounds: ≤ 30 s, .caf/.wav/.aiff; Android: .ogg/.mp3/.wav.

## Levels
Final mix peak ≈ −0.6 dBFS, integrated loudness ≈ −14 LUFS for social (check with
`ffmpeg -i final.mp4 -af ebur128 -f null -`). Booth loops: much quieter (−20 dB) or silent.
