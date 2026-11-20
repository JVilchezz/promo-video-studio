# The brief — for any client, from zero

The studio adapts to whatever the person has and wants. Nothing is mandatory except the facts the
video states. Two kinds of decisions:

| Creative (you decide, show it, they approve or change it) | Facts (ONLY the client can give them — never invent) |
|---|---|
| style, colors (if they have none), fonts, music, pacing, transitions, scene order, mascot design proposal, on-screen copy built from their facts | the company/app name, what it does, who it's for, prices, features, numbers and stats, dates, awards, testimonials, people's names and roles, URLs, handles, store availability, contact data |

If a fact is missing: ask for it, or leave that scene/element out. Never fill it with something
plausible. Templates mark facts as `{{…}}` and `render.py full` refuses to render while any is left.

## First message when the person starts from nothing

Ask ONE short block (in their language), then work with whatever they answer:

1. What is the business or app called, and what does it do? (one sentence)
2. Who is it for, and what should the viewer do after watching? (download, visit, order, follow…)
3. Where will it be posted? (Instagram/TikTok vertical · LinkedIn/YouTube horizontal · presentation · screen at an event)
4. What do you have? logo · colors · photos · screen recordings · mascot · real numbers · a voice-over (ElevenLabs key or a recording) — "nothing" is a fine answer
5. Anything you do NOT want? (mascot, voice, music, a style…)

Defaults when they don't say: 20–30 s, vertical, no voice-over, original `uplifting` music, brand kit from
`brand.py init` (tone from the industry), no mascot unless they ask for one or the brand already has one.

## What to do with what they have

| They have | Do |
|---|---|
| nothing visual | `brand.py init --name … --industry …` → show `brand_sheet.png` → approve → `brand.py apply` |
| only a logo | `brand.py from-logo logo.png --name …` (palette from the logo, logo on the app icon) |
| full brand guide | put their hex colors in `:root`, their fonts in `@font-face` (ask for the files or use the closest bundled ones and say so) |
| photos | real photos beat illustrations; fix rotation; blur faces of people who didn't agree to appear |
| screen recordings | `recording.py` (crop, clean status bar, blur private data, speed up boring parts) |
| no photos / no recordings | type-driven design: big words, shapes, icons, the brand's colors, an app UI rebuilt in HTML from what they describe — never stock people pretending to be customers |
| a mascot (PNG) | `rig.py inspect` if the limbs are a different color; otherwise ask for layers → `rig.py layers`; or animate it whole (float, squash, enter, peek) |
| wants a mascot, has none | `mascot_make.py` with a shape that matches the business → show `sheet.png` as a PROPOSAL |
| doesn't want a mascot | don't use one. Ever. |
| real numbers | count-ups, bars, donut, stat tiles — with the source in small text if it's a survey |
| no numbers | no stat scene. Show the product, the steps, the benefit in words they gave you |
| ElevenLabs key | `voice.py check` → `voices` → `tts` (see voiceover.md) |
| a voice recording | `voice.py align` with the script → captions in sync |
| no voice | text + captions + music (the default — great for muted autoplay) |
| a licensed song | `score.py --sfx-only` and mix their song under the SFX; they're responsible for the license |

## Changes after the first version
Apply exactly what they ask, keep what they liked, deliver a new version (v2, v3…). If they ask for
something that would require inventing facts ("put that we have 10,000 users"), ask whether that number is
real before using it.
