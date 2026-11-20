# Everything around the video

| Asset | Size / format | Notes |
|---|---|---|
| Cover / thumbnail | same size as the video, JPG | strongest frame (logo, award, product); LinkedIn shows frame 0 if no cover |
| Instagram reel cover | 1080×1920 (center 1080×1350 safe) | text inside the 4:5 center |
| LinkedIn post video | 1920×1080 or 1080×1350 | upload the cover separately |
| LinkedIn banner | 1584×396 (render @2× = 3168×792) | keep x 56–360 / y 212–396 empty (profile photo); `templates/linkedin-banner.html` |
| Profile picture | 400×400, circle-safe center | logo or mascot on the brand color |
| Gallery / website images | ≤ 1600 px wide, ≤ 1.5 MB JPG | fix EXIF rotation, never mirror selfies |
| Animated mascot for web | WebP ≤ 500 KB, transparent WebM | rig.py export |
| GIF for READMEs | 320–480 px wide, 12 fps, ≤ 8 MB | ffmpeg palettegen/paletteuse |
| Print (roll-up, poster) | PDF at final size, 150 dpi, 3–5 mm bleed | not video, but often requested with it |

## Post text templates
**LinkedIn (bilingual)**: line 1 hook with the achievement/launch → 2–3 short paragraphs (problem → what we
built → impact with a real number) → team credits (names + roles, tag them) → link → 5–8 hashtags.
English block below a divider line. Tag collaborators with "Add collaborators" when the platform allows it.
**Instagram**: emoji-light first line with the news → 3–5 lines of gratitude/story → CTA (link in bio /
update the app) → 6–10 hashtags.
Always offer the caption right after delivering the video.

## Team banners (LinkedIn)
Same layout for everyone: kicker (program · school/company), name (smaller font for long names; check
it doesn't reach the visuals), role · "Founding team of <b>Product</b>", 3 skill tags in brand colors + a store
badge, product visuals (phone mockups, mascot) on the right, brand stripe at the bottom.
