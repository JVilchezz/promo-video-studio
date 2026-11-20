# Example · "Aurora Coffee — one year" thank-you reel

Fictional brand, illustrated placeholder photos. Shows every signature effect:
handwriting hook · polaroid drop · **portal through the logo letter** · polaroid stack ·
notification stack + heart · **award cut-out with light sweep** · thanks · CTA.

```bash
SKILL=../../plugins/promo-video-studio/skills/promo-video-studio/scripts
python3 $SKILL/render.py video.html prev 3 9 15.6 17.2 27 34 37 42 53   # preview
python3 $SKILL/score.py cue.json --out music.wav                          # music + SFX
python3 $SKILL/render.py video.html full --dur 56.25 --out silent.mp4     # render
ffmpeg -i silent.mp4 -i music.wav -c:v libx264 -crf 19 -c:a aac -b:a 256k -shortest final.mp4
```
`portal_mask.js` was made with `make_mask.py assets/wall.jpg --color "#1F3480" --tol 40` and
`medal_mask.js` + `assets/medal_cut.png` with `cutout.py assets/src/medal_photo.jpg --hsv 12,40,90,90`.
