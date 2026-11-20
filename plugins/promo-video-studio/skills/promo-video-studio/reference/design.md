# Design rules

## Palette (tokens in `:root`)
- `--dark` / `--dark2`: the brand's dark color and a deeper shade (navy, charcoal, bottle green…).
- `--light`: cream / warm white (#FAF4EC-ish) for light scenes and text on dark.
- `--accent`: ONE warm accent (gold, coral) for kickers and key words. `--accent2` optional.
- Alternate **dark** and **light (paper)** scenes — the contrast creates rhythm.
- Backgrounds are radial gradients, never flat. A soft accent glow (25–40 %) behind logos and heroes.
- No brand guide? Derive 4–5 colors from the logo and show them before animating.

## Typography (max two families + handwriting)
- `Display` (Anton, condensed, UPPERCASE) for headlines · `Sans` (Poppins 500/600/700) for body ·
  `Hand` (Caveat) for nostalgic lines, captions and names. All bundled in `pvs/fonts` (OFL).
- Sizes at 1080×1920: headline 96–180 px · kicker 30–38 px (letter-spacing 8–10 px, accent) ·
  body 38–48 px · handwriting 84–120 px. At 1920×1080: headline 84–130, body 30–34, kicker 28–36.
  Nothing readable under 22 px.
- Headlines: 2–6 words, manual line breaks, a final period adds weight ("LESS WAITING.").
- Bilingual videos: main language big; translation small and grey underneath.

## Layout
- Margins ≥ 80 px. Vertical safe zones: keep text out of the top 250 px and bottom 350 px
  (platform UI). Width check: Display at 96 px fits ~18 characters per line at 1080 px wide.
- Two-column horizontal scenes: phone at x 300–760, text from x 880.
- Polaroids: 24 px border, 110 px bottom strip with a handwritten caption, slight rotation (±2–7°).
- Film date stamp (`.stamp`, orange LCD glow) on photos for nostalgia ("'26 EXPO").

## Story structures
**Thank-you / milestone reel (vertical, 45–65 s)**
hook (handwritten "A few weeks ago…") → the team (polaroid) → the place/product (photo → portal → logo)
→ memories (polaroid stack) → the people who used it (notification stack + "thank you for believing
in us" + heart) → the achievement (award cut-out reveal) → thanks to mentors/partners → "see you next
year" → logo + "this is just the beginning".

**Product / app promo (horizontal, 45–75 s)**
hook → problem + one real stat → logo reveal → how it works (3–5 steps with phone mockup and real
screen frames) → new feature → proof (3 stat tiles) → team photo → logo + tagline + URL.

**Short ad (vertical, 15–30 s)**
hook 2 s → product in action 3 × 3 s → proof 3 s → CTA 4 s.

**Booth / screen loop (horizontal, 30–60 s)**
no hook, no voice; last frame = first frame; quiet or no sound.

## Things clients called ugly (don't)
Neon + buttons "quiz" look · cartoon mascot animation (keep mascots small and calm) · robotic or
"in a room" TTS voices · phonk/trap music · shrill music-box/bell melodies · funeral-slow pacing ·
mirrored selfies · text overlapping the logo.
