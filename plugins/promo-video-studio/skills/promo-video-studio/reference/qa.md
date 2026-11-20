# QA checklist (on the FINAL mp4)

`python3 SKILL_DIR/scripts/render.py final.mp4 qc <start/middle/end of every scene…>` and look at it.

- [ ] First frame is not empty — or a separate cover image is delivered.
- [ ] No text overlaps another element (logo vs tagline at the end, text vs phone/photo, stat numbers inside tiles).
- [ ] Nothing cut by the frame; margins ≥ 80 px; vertical safe zones respected.
- [ ] No orphan word on the last line; manual line breaks in headlines.
- [ ] Spelling and accents in every language; translations sound native (no double verbs).
- [ ] Photos: correct rotation, selfies NOT mirrored, no heads cropped, faces/private data blurred where needed.
- [ ] Screen recordings: no keyboard, errors, real passwords, emails, IDs or customer names.
- [ ] Audio: whooshes land on cuts, booms on reveals, no clipping (`ffmpeg -i final.mp4 -af volumedetect -f null -` → max ≤ −0.5 dB).
- [ ] Video and audio have the same length; there is a fade at the end.
- [ ] Pace: no scene holds text much longer than it takes to read it.
- [ ] File size sensible (Instagram/LinkedIn ≈ 30–60 MB for a minute; WhatsApp ≤ 16 MB → `-crf 24`).

## Mistakes that already happened once
- Logo drawn on top of the tagline in the outro → compute vertical positions (logo top 200 / width 700, tagline 660, URL 780 at 1080 px high).
- A 96 px hook line wider than the frame → split it or reduce size.
- Text hidden behind the stat card → reserve columns (text 150–1150, card 1290–1790 at 1920 wide).
- Phone mockup over the step text → phone x 300–760, text from 880.
- Mirrored selfies (writing on shirts reversed) → never flip unless asked.
- Translated video out of sync → keep the original timings and original audio; translate only text.
- Chat bubbles wrapping → `white-space:nowrap` + shorter lines.
- CSS mask-image from a file path didn't render (CORS on file://) → masks are data URIs.
- A placeholder string inside a template literal (`${MASK}` + text replace) broke the URL → use unique placeholders like `%%MASK%%`.
- Overlay layers below scenes (scenes get z-index) → overlays use z-index ≥ 100.
- Handwriting wipe on a full-width div looked late → wrap text in `<span class="w">`.
- Same music in every video, shrill music-box melodies, slow funeral-like score → vary style/seed, keep it warm, use `uplifting` for celebrations.
- Number inside a donut ring overlapped the ring → the number must be ≤ 60 % of the ring's inner diameter
  (ring ≥ 240 px for a 3-character number at 50 px); center it with a flex box the same size as the ring.
- Template/example facts left in a video (a fake rating, a made-up user count, "brand.com") → facts are `{{…}}` placeholders;
  `render.py full` refuses while any is left. Fill them with real data or delete the element — never "something plausible".
