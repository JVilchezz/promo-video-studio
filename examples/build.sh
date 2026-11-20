#!/usr/bin/env bash
# Build every example end-to-end (mascot frames → UI sounds → music → video → final MP4).
# Usage:  bash build.sh [example ...]      (default: all)   — needs python3 + playwright + ffmpeg
set -euo pipefail
cd "$(dirname "$0")"
SK=../plugins/promo-video-studio/skills/promo-video-studio/scripts
[ -d "$SK" ] || SK=../skills/promo-video-studio/scripts
RIG="python3 $SK/rig.py"

prep() {   # generated assets (not committed)
  case "$1" in
    feature-update)
      [ -d feature-update/assets/m_celebrate ] || $RIG animate mascot/rig.json --preset celebrate --dur 4.5 --size 720 --out feature-update/assets/m_celebrate
      [ -d feature-update/assets/m_wave ]      || $RIG animate mascot/rig.json --preset wave --dur 4.5 --size 720 --shadow --out feature-update/assets/m_wave
      [ -d feature-update/sounds ] || python3 $SK/sfx_pack.py --out feature-update/sounds --key A ;;
    data-recap)
      [ -d data-recap/assets/m_idle ] || $RIG animate mascot/rig.json --preset idle --dur 4 --size 720 --shadow --out data-recap/assets/m_idle
      [ -d data-recap/assets/m_wave ] || $RIG animate mascot/rig.json --preset wave --dur 4.5 --size 720 --shadow --out data-recap/assets/m_wave ;;
    chat-story)
      [ -d chat-story/sounds ] || python3 $SK/sfx_pack.py --out chat-story/sounds --key F ;;
  esac
}

for ex in ${@:-thank-you-reel chat-story data-recap feature-update}; do
  echo "── $ex"; prep "$ex"
  D=$(python3 -c "import json;print(json.load(open('$ex/cue.json'))['duration'])")
  python3 $SK/score.py "$ex/cue.json" --out "$ex/music.wav"
  python3 $SK/render.py "$ex/video.html" full --dur "$D" --out "$ex/silent.mp4"
  python3 $SK/mux.py "$ex/silent.mp4" "$ex/music.wav" --out "$ex/$ex.mp4"
  echo "   → $ex/$ex.mp4"
done
