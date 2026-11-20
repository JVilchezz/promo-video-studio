# Example · closing with real data (horizontal 1920×1080)

28 s: mascot + "SINCE MONDAY…" → count-up to the total with a bump on landing → bar chart per day →
stat tiles + donut ring → "THE VERY FIRST ORDER" with the time de-blurring in → mascot waving + logo.
Fictional brand. **The numbers here are placeholders — in a real video use only real, verifiable data**
(and never a customer's name without permission: show the first order by its time only).

- Helpers: `counter`/`bump`, `bars()`, `donut()`, `pop`, `seq()` for the mascot frames.
- Mascot frames are generated from `../mascot/rig.json` (`rig.py animate --preset idle|wave`).

```bash
bash ../build.sh data-recap
```
