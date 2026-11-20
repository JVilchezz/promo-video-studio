# Video types: every format this studio has shipped

Times are a starting point. Always re-time on the beat grid of the chosen music (see music.md).
⭐ = the moment that has to land on a downbeat with a hit.

## 1 · Thank-you / milestone / award reel (vertical, 45–65 s)
handwritten hook "A few weeks ago…" (blurred photo behind) → the team on a polaroid with handwritten names
→ "this is where it began": photo → ⭐ **portal through the logo letter** → logo + tagline → memories: 4–5
polaroids dropping on a table ("…and they left their mark") → zoom to the signatures/names and circle them
in gold, one by one with soft notes → "to you, who ordered/used/came…": **notification stack** → blur →
heart drawn in gold → "THANK YOU FOR BELIEVING IN US." → half-beat silence → ⭐ **award cut-out** with
golden sweep, bokeh and "FIRST PLACE" → thanks to mentors and partners (name in handwriting) → "see you
next year / keep ordering" → logo + mascot + "this is just the beginning".
Music: `uplifting` 90–100 bpm. Never slow and sad ("sounds like a funeral").
Example: `examples/thank-you-reel`.

## 2 · Launch / LinkedIn promo (horizontal 1920×1080, 60–75 s, no voice)
hook on dark ("EVERY DAY, AT BREAK TIME…") → problem on paper: two stacked headlines in two colors + a card
with ONE real stat (a survey %) → ⭐ logo reveal (clip wipe + glow) + tagline → how it works: phone
on the left playing real screen-recording frames, "01 / 05 · HOW IT WORKS" + 2-line headline + one line,
4.8 s per step → the new feature on dark (kicker "NEW · VERSION X", phone + mascot) → proof: 3 stat tiles
popping in (orders, platforms, tests passed) → the team photo with Ken Burns + names and roles → outro: mascot
waving + logo + tagline in two colors + URL. Bilingual: main language big, translation small and grey.
Deliver also: cover frame, the LinkedIn post text (both languages), team banners (deliverables.md).

## 3 · New version / feature update (vertical, 30–50 s, with voice-over)
"NEW VERSION" (letter-spacing collapsing) + huge version number popping with `back` easing + logo →
mascot centered with rotating `rays`, soft glow and orbiting `sparkles`: "[MASCOT] IS NOW SMARTER" →
phone demo (screen recording sped up where boring) with `captions()`: pills with a line icon for each step
("Tap the microphone", "It builds your order", "It asks if something is missing", "You confirm") and the
spoken user line as a handwritten quote revealed word by word → outro "UPDATE [APP]" + store badges:
iPhone "Update on the App Store", Android "New version at the link in bio".
Voice: ElevenLabs, natural, dry; captions synced to word timings (voiceover.md).

## 4 · Coming-soon teaser (vertical, 25–35 s)
real footage of the problem (queues, crowd), darkened and blurred, with short white lines and one word in the
accent color ("Break lasts **20 minutes.**" → "And if you didn't have to wait?") → 3–4 features: kicker
"01 · ORDER", headline, phone with the screen; soft icon pattern in the paper background → logo on dark +
"AVAILABLE FOR" + Android/iOS chips + "COMING SOON" in wide letter-spacing.

## 5 · "It's live!" store-launch announcement (vertical, 40–50 s)
dark teaser: phone flying in, mascot peeking from behind it: "[MASCOT] has something to tell you…" →
app icon pops in on paper, headline types on ("[APP] is now on the **App Store**!") + store badges →
STEP 1 · iPhone: download from the App Store (phone with the store page) → STEP 2 · Android: download the
file and install (phone with the download page) → mascot waving with soft rays: logo + "It's **official**."
Music: uplifting, energetic. SFX: pop on the icon, typing on the headline, whoosh per step.

## 6 · Quick tutorials (vertical, 15–20 s each, a series)
paper background; header kicker "[APP] · QUICK TUTORIAL" + title "How to order"; a big phone in the
center playing the real recording (prepared with `recording.py`: status bar cleaned, boring parts at 2–3×,
private data blurred); a dark caption pill under the phone that changes with each step ("Go to Menu, pick
your product and add it to the cart" → "Choose how to pay and tap Confirm" → "Show your QR at the counter").
Same template for every tutorial (order, pay, customize, pick up, cancel; admin versions). Soft music, clicks.

## 7 · Presentation opening "dynamic" (12–15 s) + closing with real data (25–30 s)
**Opening** — a relatable story as a chat: `chatUI` in a phone, two friends ("Are you at the cafeteria?" /
"Yes, but the line is huge." / typing… / "Then I'm missing lunch.") and the app's notification dropping in at
the end ("Order ready"). The presenter talks over it; keep it silent or very soft.
**Closing** — the real data since launch: "SINCE MONDAY…" (mascot entering) → a huge counter rolling to the
number of orders with a bump + bars per day (`bars`) → 3 stat tiles (money through the app, best seller,
payment methods) → "THE FIRST ORDER" + a giant time ("7:38 A.M.") de-blurring → the chat payoff ("I ordered
on [APP] / See you at break / Finally, no line!") + notification → logo + mascot waving.
Only real numbers. No customer names without permission (show the time, not the name).
**Bilingual versions:** same timings, same audio, translated text only; check bubble widths (`nowrap`).

## 8 · Booth / stand screen loop (horizontal, 30–90 s, loops forever)
no hook, no voice: a sequence of app scenes (phone + one caption each) and the logo, with the last frame
identical to the first. Two versions: very soft sound (pad + gentle whoosh/pop per scene, −20 dB) and silent.
A small QR code corner for people walking by.

## 9 · Mascot clips and in-app animations (square 1080 or vertical)
- greeting (wave + "Hi!" bubble), entrance (walks/runs in from the side with speed lines, stops, waves),
  celebrate, point left/right (to place next to text), idle loop, think, bow, jump, peek — `rig.py` presets.
- talking loop for voice lines — `mascot_talk.py`.
- **splash / intro**: mascot peeks from behind a counter and the logo appears with a tagline bubble;
  or the logo writes on with sparkle accents.
- **logout / closing**: the little stand closes its shutters ("CLOSED" sign swings), the mascot walks out,
  "See you soon!" bubble, logo; or the mascot sends a heart and fades.
Export transparent WebM + animated WebP for apps and websites, MP4 for social (rig.py export).
Keep it calm and well-made — clients called cartoon-y slapstick "too childish".

## 10 · Short-form for a small business (TikTok/Reels, 15–40 s)
music + sound effects + visual effects (never only raw screen-recording cuts — "horrible"); text on screen or
a natural voice (no robotic TTS, no owner's voice unless asked); serious mascot appearances; no phonk/trap.
Hook in the first 1.5 s, one idea per beat, CTA at the end (link in bio, discount code).

## 11 · Social posts around a video
Cover image (strongest frame), post text in the user's language (+ English if bilingual), hashtags,
LinkedIn banners for each team member, gallery images. See deliverables.md.
