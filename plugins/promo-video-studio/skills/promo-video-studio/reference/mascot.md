# Mascots: rig, animate, talk, export

A mascot is optional. Use one only if the brand has it or the client asks for it.

## 0 · Which path?
| The client has… | Path |
|---|---|
| a mascot PNG with arms/legs in a different color than the body (stick limbs) | §1 `rig.py inspect` — fully automatic |
| a mascot whose limbs are the same color, furry, 3D-looking, overlapping | §1b ask for it **in layers** → `rig.py layers` |
| a mascot that can't be split and no layers | animate it whole: float, squash on landings, rotate, enter/peek, blink/talk (`mascot_talk.py`) |
| no mascot, but wants one | §1c `mascot_make.py` — an original character in the brand colors, already rigged |

## 1 · Split the mascot into parts (`rig.py inspect`)
Ask for the cleanest still of the mascot (front-facing, arms and legs visible, transparent PNG).
```bash
python3 SKILL_DIR/scripts/rig.py inspect mascot.png --limb-color "#3E2216" --tol 40 --out rig.json --preview rig_check.png
```
- Pick `--limb-color` from the limbs (sample the image). Raise `--tol` if parts are missing, lower it if
  body shading gets detected. Eyes, mouth and logos INSIDE the body are kept on the body automatically.
- It writes `rig_body.png` (the body with the limbs removed and the overlaps repaired) and `rig.json`:
  each limb with pivot (shoulder/hip), end, thickness, hand/foot size and color. Limbs are **redrawn
  procedurally** in every pose, so a raised arm looks clean even if it was hidden behind the body.
- **Look at `rig_check.png`.** Fix in `rig.json` if needed: pivots, `kind`, `z` (−1 behind the body,
  1 in front), lengths (`end`). For mascots whose parts aren't color-separable (ears, wings, tails, a hat),
  add `"mode":"cut"` parts with a polygon and a pivot — they are cut out of the image and rotated.

## 1b · Any mascot, from layers (`rig.py layers`)
Ask: "Export the mascot in separate PNGs with transparent background and the SAME canvas size: the body
(with head and face), each arm, each leg (and tail/ears if they should move)." In Canva/Photoshop/Procreate/
Figma that's hiding all layers but one and exporting, once per part.
```bash
python3 SKILL_DIR/scripts/rig.py layers --body body.png --part arm_l=arm_l.png --part arm_r=arm_r.png \
        --part leg_l=leg_l.png --part leg_r=leg_r.png --out rig.json --preview rig_check.png
```
Pivots (shoulder/hip) and ends (hand/foot) are detected from each piece's two extremities; check
`rig_check.png` and override with `--pivot arm_r=412,380` if one is off. Arms go in front of the body and
legs behind by default (`--front` / `--behind`). Pieces are rigid (no elbow bend) — the presets still
wave, point, celebrate, walk, jump… with a clean cut-out-animation look.

## 1c · No mascot yet (`mascot_make.py`)
Pick the shape from what the business is (cup → coffee/drinks, box → shop/delivery/app, phone → apps,
drop → water/cleaning/health, bag → store/fashion, bun → bakery/food, blob → anything friendly). Never
imitate a known character.
```bash
python3 SKILL_DIR/scripts/mascot_make.py --shape cup --brand brand/brand.json --letter A --out mascot
```
Show `mascot/sheet.png` (rest + 3 poses) as a proposal; adjust `--body`/`--accent`/`--limb` colors,
`--mouth smile|open|calm`, `--no-band`, `--no-cheeks` until they like it. It writes `rig.json` directly.

## 2 · Animate (`rig.py animate`)
```bash
python3 SKILL_DIR/scripts/rig.py animate rig.json --preset wave --dur 4.5 --size 1080 --out assets/m_wave --bubble "Hi!" --shadow
```
Presets: `idle` (breathing, sway — loop it) · `wave` · `point_right` / `point_left` · `celebrate` (jumps with
arms up) · `walk` · `enter` (walks in, stops, waves) · `exit` · `jump` (anticipation squash → jump → landing
squash) · `peek` (rises from below, waves) · `bow` · `think`.
Custom moves with keyframes (`--keys keys.json`), smooth interpolation between keys:
```json
{"body":  {"y": [[0,0],[0.35,-60],[0.7,0]], "sy": [[0,1],[0.3,0.92],[0.45,1.04],[0.7,1]]},
 "arm_r": {"abs": [[0,60],[0.4,-60]], "w": [[0,0],[0.4,1]], "bend": [[0,0],[0.4,-25]]},
 "leg_l": {"rot": [[0,0],[0.35,15],[0.7,0]]}}
```
`abs` = absolute arm direction in degrees (0 right, −90 up, 180 left) blended with weight `w` — the reliable
way to say "arm up-right" for any mascot. `rot` is relative to the rest pose, `bend` bends the elbow/knee.
Body: `x` (px, or −1…1 = canvas widths), `y`, `rot`, `sx`, `sy` (squash & stretch).

Principles: anticipation before big moves, squash on landings, overlapping motion (arms lag the body by
~0.1 s), ease in/out everywhere, a breathing idle so it's never frozen. Calm amplitude in serious videos.

## 3 · Talking & blinking (`mascot_talk.py`)
```bash
python3 SKILL_DIR/scripts/mascot_talk.py mascot.png --mouth 584,571:660,557 --eyes 532,547:685,512 --eye-size 37,48 --loop 3 --out assets/talk
```
Erases the drawn mouth/eyes (surface-fit fill + matching grain) and animates an open/close mouth with tongue
and a blink. Loop it while a voice line plays; cut on phrase ends.

## 4 · In a video page
```html
<img id="m" style="position:absolute;left:260px;top:300px;width:560px">
```
```js
seq('m', t, T0, 'assets/m_wave', N, 30);              // once
seq('m', t, T0, 'assets/m_idle', N, 30, true);        // loop
$('m').style.transform = `translateY(${(1-ease.out4((t-T0)/.9))*120 - 6*Math.sin(t*1.4)}px)`;  // enter + float
```
Speech bubbles can also be HTML (navy pill + tail) so they're crisp and translatable.

## 5 · Export for apps, web and social
```bash
python3 SKILL_DIR/scripts/rig.py export assets/m_wave --webm wave.webm --webp wave.webp --webp-size 512 --mp4 wave.mp4 --bg "#FAF4EC"
```
WebM (VP9 + alpha) for websites/apps/editors, animated WebP (small, loops) for landing pages, MP4 on the
brand color for social. For a website hero keep the WebP under ~500 KB (fewer frames, 512 px).

## 6 · Scenes with props (splash, closing)
Build props in HTML/CSS in the page (a counter/stand made of divs, shutters that slide down, a sign that
swings with a damped `sin`), put the mascot frames behind/in front with z-index, and mask with a
`clip-path` for "peeking from behind". Logo reveal + tagline bubble at the end.
