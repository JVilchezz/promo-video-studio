# Music & sound

`scripts/score.py` writes original, royalty-free music from `cue.json` (format documented at the top
of the script). Times are seconds of the final video.

## 1 · Pick a style — and change it every video
| style | feel | bpm | progression |
|---|---|---|---|
| `uplifting` | exciting, hopeful pop: bright piano, plucks, offbeat bass, claps | 92–110 | I–V–vi–IV |
| `cinematic` | emotional build to an epic climax: strings, piano ostinato, toms | 72–90 | vi–IV–I–V |
| `nostalgic` | warm memories: felt piano, soft strings, brushes | 76–92 | IV–V–iii–vi |
| `minimal` | clean corporate/tech: piano stabs, light pulse | 104–120 | I–vi–IV–V |

Change `seed` for a new melody/arpeggio and `key` for a new color. Never ship two videos with the same score.
Thank-you / celebration videos: `uplifting` (people said slower cinematic scores "sound like a funeral").

## 2 · Build the grid first
`beat = 60/bpm`, `bar = 4·beat`. Put scene cuts on beats and big moments (logo, award, drop) on bar
downbeats. Example at 96 bpm: beat 0.625 s, bar 2.5 s → cuts at 5.0, 7.5, 10.0 …

## 3 · Sections = energy curve
- `energy` 0–0.2: piano only (intimate) · 0.2–0.45: + arpeggio/pad · 0.45–0.75: + bass and light drums
  and the melody moves to strings · ≥ 0.75: full drums, strings doubled an octave below, brighter.
- `"build": true` → accelerating snare roll + rising energy into the next section.
- `silence_before: [t]` → half-beat of silence right before a hit (huge impact for reveals).
- `hits: [t]` → boom + dark crash + accent. `end` → final tonic chord rings to the end.
Typical arc: 0.15 → 0.45 → 0.8 (logo) → 0.6 build → 1.0 (award/climax) → 0.3 (thanks) → 0.7 (CTA) → end.

## 4 · Sound design (`sfx`)
`write` pencil scribble (match handwriting duration) · `thud` polaroid landing · `ding` soft piano note
(notifications, signature circles; optional `note` MIDI) · `riser` before hits · `sweep` soft air on light
sweeps · `boom` · `whoosh` · `pop` · `click` · `file` any WAV/MP3 at a time (`"path"` relative to cue.json,
optional `gain`, `pan`) — use it for the UI sounds from `sfx_pack.py` (send/receive/typing/notification).
`cuts` adds a soft whoosh into each scene change.
Keep SFX under the music; nothing should sound like a video game.

## 5 · Warm, never shrill
The engine keeps melodies between ~D4 and G5, low-passes the master (8–11 kHz) and has no music-box or
high bells. Don't add high sine "sparkles". If someone says "chillona/shrill", lower the melody, use
`cinematic` or `nostalgic`, or drop the arpeggio energy.

## 6 · Licensed songs
Synthesized music is good, a great recorded song is better. Always also export `--sfx-only` so the
client can add a song in Instagram/TikTok/CapCut. Tell them which second the climax is at so they
align the drop.

## 7 · Speed changes
Rendering with `--speed 1.2` makes the picture 20 % faster. Never speed up the audio (it gets
higher-pitched and shrill): divide every time in `cue.json` by the speed, multiply `bpm` by the speed
(or keep the bpm and accept a looser grid) and regenerate.

## 8 · Voice-over (only if asked)
Natural voices only (e.g. ElevenLabs). Generate the voice first, time scenes to it, duck music ~8 dB
under the voice, add subtitles.
