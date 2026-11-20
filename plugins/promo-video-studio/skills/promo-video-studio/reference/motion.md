# motion.js — API and recipes

Load order in `video.html`: `<link rel="stylesheet" href="pvs/base.css">` … `<script src="pvs/motion.js"></script>`.
Every helper accepts an element or an id string. `t` is the time in seconds.

## Page contract
```js
const SC=[{id:'s1',start:0,end:5},{id:'s2',start:5,end:11},{id:'s3',start:11,end:18,cut:true}];
overlays({W:1080,H:1920});                 // light leaks, vignette, grain, fade layer
ready(['assets/photo.jpg', …]);            // preload EVERYTHING, then window.READY=true
window.R=function(t){
  const cur=scenes(SC,t);                  // crossfade (0.8 s, 1.035→1 settle) unless cut:true
  if(t>=5&&t<11.8){ … }                    // only compute a scene inside its time window (+0.8 s)
  atmosphere(t,{cuts:SC.map(s=>s.start),dark:['s1','s3'].includes(cur),end:END});
};
```
Rules: `R(t)` is pure — same `t`, same frame. No CSS animations/transitions, no timers, no `Date.now()`.
Text that is written with `write()` must be wrapped: `<div id="x"><span class="w">Text</span></div>`.

## Helpers
| call | effect |
|---|---|
| `rise(el,t,t0,dy=40,out=null,dur=.9)` | fade + rise + unblur; `out` = time to fade away |
| `write(el,t,t0,dur=1.2)` | handwriting wipe (left→right) |
| `pop(el,t,t0,dur=.7,dy=80)` | card entrance with soft overshoot |
| `counter(el,t,t0,dur,from,to,fmt)` | count-up number |
| `type(el,t,t0,text,cps=28)` | type-on text |
| `drawPath(path,t,t0,dur=.6)` | draw an SVG stroke (circles, hearts, underlines) |
| `sweep(el,t,[starts],dur=1.1)` | light sweep over a masked element |
| `ken(el,t,t0,t1,s0,s1,origin)` | slow Ken Burns zoom |
| `drop(el,t,t0,rot,dur=.6)` | polaroid falling onto a table (lands at ≈ t0+0.33·…) |
| `stack([cards],t,[drops],gap=200)` | iOS notification stack, newest on top |
| `portal(t,{cam,next,mask,rect,start,dur,zmax,W,H})` | fly through a shape into the next scene |
| `bokeh(container,n,W,H).update(t,t0)` | slow floating golden bokeh |
| `seq(img,t,t0,folder,count,fps,loop)` | play a PNG/JPG frame sequence (mascots, recordings) |
| `ease.out4 / out3 / inOut4 / inOut3 / inOutSine / back`, `lerp`, `cl` | math |

Default rhythm: stagger elements 0.2–0.5 s apart (kicker → headline → body → small print).
Big elements move 40–60 px, small ones 16–24 px.

Text fitting: `fit(el, maxWidth, minPx=28)` shrinks a one-line title until it fits — use it for brand names
and translated headlines (call it after `document.fonts.ready`).

## Recipe · Portal through a logo letter (the "wow" transition)
1. `python3 SKILL_DIR/scripts/make_mask.py assets/wall.jpg --color "#1E2A6E" --tol 60 --box x0,y0,x1,y1 --out portal_mask.js`
   → check `mask_check.png`: the letter's strokes red, nothing else.
2. In the page: `<script src="portal_mask.js"></script>` (defines `window.PORTAL`) and put the photo
   scene's content inside a camera layer:
```html
<div class="S paper" id="s3"><div id="cam3" style="position:absolute;inset:0">
  … title …
  <div style="position:absolute;left:40px;top:640px;width:1000px;height:667px;border-radius:30px;overflow:hidden">
    <img src="assets/wall.jpg" style="width:1000px;height:667px"></div>
</div></div>
<div class="S dark" id="s3b"> … logo reveal … </div>
```
3. Scenes: `{id:'s3',start:13,end:19.6},{id:'s3b',start:16.2,end:26,cut:true}` and in `R`:
```js
if(t>=13&&t<19.6) portal(t,{cam:'cam3',next:'s3b',mask:PORTAL,rect:{x:40,y:640,w:1000,h:667},start:17.2,dur:2.2,zmax:95,W:1080,H:1920});
```
The strokes "light up" with the next scene's colors (1.3 s), then the camera accelerates into the
thickest part of the shape and the next scene fills the screen. Reveal the logo right after `start+dur`
on a downbeat, with a `boom` hit and a reversed swell in the music.

## Recipe · Award / product hero with light sweep
`python3 SKILL_DIR/scripts/cutout.py assets/medal.jpg --hsv 15,38,110,120 --out assets/medal_cut.png --js medal_mask.js --var MEDAL`
```html
<script src="medal_mask.js"></script>
<div id="hero" style="position:absolute;left:215px;top:400px;width:650px;height:660px;perspective:1600px"><div id="hero3d" style="position:absolute;inset:0">
  <img src="assets/medal_cut.png" style="position:absolute;inset:0;width:650px;height:660px;filter:drop-shadow(0 50px 50px rgba(0,0,0,.55)) drop-shadow(0 0 40px rgba(242,195,82,.35))">
  <div class="sweep" id="hsw"></div></div></div>
<script>document.getElementById('hsw').style.webkitMaskImage=`url(${MEDAL.uri})`;</script>
```
```js
const a=ease.out3((t-T0)/1.4);
$('hero3d').style.transform=`translateY(${(1-a)*120-10*Math.sin(t*1.1)}px) rotateY(${(1-a)*-38+5*Math.sin(t*.7)}deg) scale(${lerp(.82,1,a)})`;
sweep('hsw',t,[T0+3.2,T0+6.4]);
```
Pair with: dark radial background, golden glow, `bokeh`, a 0.5-beat silence before `T0` and a `boom` hit at `T0`.
Masks and CSS `mask-image` MUST be data URIs (file:// URLs are blocked by CORS).

## Recipe · Notification stack ("thank you to everyone who ordered")
```js
const NT=[['7:12 AM','Order confirmed','We’re preparing your breakfast.'], …];  // the app's own messages — never customer names
NT.forEach(([tm,ti,bd],i)=>{const d=document.createElement('div');d.className='nt';d.id='n'+i;
 d.innerHTML=`<img class="ic" src="assets/appicon.png"><div class="tx"><div class="hd"><span>APP</span><span>${tm}</span></div><div class="ti">${ti}</div><div class="bd">${bd}</div></div>`;$('notifs').appendChild(d)});
// in R:
stack(NT.map((_,i)=>'n'+i),t,[58.8,59.2,59.6,60.0,60.4]);
```
Then blur/dim the stack (`filter:blur(9px); opacity:.18`), draw a heart with `drawPath`, and reveal the
big line ("THANK YOU FOR BELIEVING IN US."). Give each notification a soft `ding` in the cue sheet.

## Recipe · Signature circles on a photo
Put an `<svg>` the size of the photo inside the same transformed container as the `<img>`, add one
hand-drawn ellipse `path` per name (radius jitter + small overshoot), zoom the container to the
names, then `drawPath` each one 0.4 s apart with a matching note in the music.

## Recipe · Phone with a real screen recording
Frames: `ffmpeg -i rec.mp4 -vf "fps=30,scale=436:-2" -q:v 3 assets/rec/%04d.jpg`. Inside `.phone .screen`
put `<img id="scr">` and in `R`: `seq('scr',t,T0,'assets/rec',COUNT,30*speed,false,4,'jpg','')`.
Slow down (0.45×) or trim parts with the keyboard or errors. Float the phone: `translateY(-8*sin(t*1.1))`.
