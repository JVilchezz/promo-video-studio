# Example · fictional mascot rig

`mascot.png` (drawn for this repo) → `rig.json` + `rig_body.png` (made with `rig.py inspect`).
The other examples generate their mascot frames from it:

```bash
SK=../../plugins/promo-video-studio/skills/promo-video-studio/scripts
python3 $SK/rig.py inspect mascot.png --limb-color "#3E2618" --tol 30 --out rig.json --preview rig_check.png
python3 $SK/rig.py animate rig.json --preset wave --dur 4.5 --size 720 --out ../feature-update/assets/m_wave
python3 $SK/rig.py export ../feature-update/assets/m_wave --webm wave.webm --webp wave.webp --webp-size 400
```
