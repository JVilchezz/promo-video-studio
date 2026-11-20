# Promo Video Studio (Claude Code plugin)

Agent Skill that lets Claude make agency-quality promo videos and reels: motion graphics built as
animated HTML, rendered with Playwright + ffmpeg, scored with original royalty-free music.

- Skill: `skills/promo-video-studio/SKILL.md`
- Docs, demo and other install options: see the repository README.

Requirements: Python 3.10+, playwright (+ Chromium), numpy, scipy, pillow, opencv-python-headless, ffmpeg.
`python3 skills/promo-video-studio/scripts/doctor.py --fix --render-test` installs what is missing and runs a 1-second test.
