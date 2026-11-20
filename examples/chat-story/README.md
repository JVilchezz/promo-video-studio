# Example · chat opener ("the dynamic" for a presentation)

16 s vertical. A relatable chat (typing dots, read ticks, send/receive sounds) about the long line at
the cafeteria, the app's notification drops in, then the logo with "NO MORE LINES." — ideal to open a
pitch or a class presentation before the speaker talks. Fictional brand.

- Chat: `chatUI()` in `pvs/motion.js` — messages `[t, 'me'|'them', text, time]`, typing ranges, one notification.
- Sounds: `sfx_pack.py --out sounds --key F` → placed in `cue.json` as `{"type": "file", …}` SFX.
- Music: `minimal` at 90 bpm that only opens up on the logo hit (12.4 s), with a half-beat of silence before it.

```bash
bash ../build.sh chat-story          # sounds → music → video → chat-story.mp4
```
Change the names, messages and times to your story; keep every message short enough to read in ~1.5 s.
