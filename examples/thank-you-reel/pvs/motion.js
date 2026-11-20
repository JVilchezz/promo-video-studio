/* ──────────────────────────────────────────────────────────────────────────
   Promo Video Studio · motion.js
   A tiny, deterministic animation kit for videos rendered frame-by-frame.
   Every function takes the current time `t` (seconds) and sets styles, so the
   same `t` always produces the same frame. Never use CSS animations,
   setTimeout or Date.now() in a video page.
   ────────────────────────────────────────────────────────────────────────── */
(function (G) {
  'use strict';
  const $ = (q) => (typeof q === 'string' ? (q[0] === '#' || q[0] === '.' ? document.querySelector(q) : document.getElementById(q)) : q);

  /* ── math & easing ─────────────────────────────────────────────────────── */
  const cl = (x) => Math.max(0, Math.min(1, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = {
    out4: (x) => 1 - Math.pow(1 - cl(x), 4),                 // entrances
    out3: (x) => 1 - Math.pow(1 - cl(x), 3),
    inOut4: (x) => { x = cl(x); return x < .5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2; }, // scene changes
    inOut3: (x) => { x = cl(x); return x < .5 ? 4 * x ** 3 : 1 - Math.pow(-2 * x + 2, 3) / 2; },
    inOutSine: (x) => { x = cl(x); return -(Math.cos(Math.PI * x) - 1) / 2; },             // handwriting, camera
    back: (x) => { x = cl(x); const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); }, // cards
  };
  // derivative of inOut3 (used for zoom-speed motion blur)
  const dInOut3 = (x) => (x < .5 ? 12 * x * x : 12 * (1 - x) * (1 - x));

  /* ── text & element reveals ───────────────────────────────────────────── */
  // Rise: fade + slide up + un-blur. Optional `out` time fades it away.
  function rise(el, t, t0, dy = 40, out = null, dur = .9) {
    el = $(el); const a = ease.out4((t - t0) / dur), o = out != null ? ease.inOut4((t - out) / .5) : 0;
    el.style.opacity = cl((t - t0) / .4) * (1 - o);
    el.style.transform = `translateY(${(1 - a) * dy - o * 16}px)`;
    el.style.filter = (a < .99 || o > 0) ? `blur(${(1 - a) * 8 + o * 6}px)` : 'none';
  }
  // Write: handwriting wipe, left → right. Put the text inside <span class="w">…</span>
  // so the wipe follows the text width (not the full-width container).
  function write(el, t, t0, dur = 1.2) {
    el = $(el); el = el.querySelector('.w') || el; const k = ease.inOutSine((t - t0) / dur);
    el.style.opacity = t < t0 ? 0 : 1; el.style.clipPath = `inset(-20% ${(1 - k) * 100}% -20% 0)`;
  }
  // Pop: scale-in with a soft overshoot (cards, badges, stat tiles)
  function pop(el, t, t0, dur = .7, dy = 80) {
    el = $(el); const a = ease.back((t - t0) / dur);
    el.style.opacity = cl((t - t0) / .25);
    el.style.transform = `translateY(${(1 - cl(a)) * dy}px) scale(${.92 + .08 * a})`;
  }
  // Count up a number: counter(el,t,t0,1.2,0,23, v=>Math.round(v))
  function counter(el, t, t0, dur, from, to, fmt = (v) => Math.round(v).toString()) {
    el = $(el); el.textContent = fmt(lerp(from, to, ease.out3((t - t0) / dur)));
  }
  // Type-on text (monospace / chat bubbles): reveals characters at `cps` chars/sec
  function type(el, t, t0, text, cps = 28) {
    el = $(el); const n = Math.max(0, Math.min(text.length, Math.floor((t - t0) * cps)));
    el.textContent = text.slice(0, n); el.style.opacity = t < t0 ? 0 : 1;
  }
  // Draw an SVG path (signature circles, hearts, underlines, arrows)
  const _len = new WeakMap();
  function drawPath(p, t, t0, dur = .6) {
    p = $(p); if (!_len.has(p)) _len.set(p, p.getTotalLength());
    const L = _len.get(p), k = ease.inOutSine((t - t0) / dur);
    p.setAttribute('stroke-dasharray', L); p.setAttribute('stroke-dashoffset', L * (1 - k)); p.style.opacity = t < t0 ? 0 : 1;
  }
  // Light sweep across a masked element (.sweep with -webkit-mask-image = data URI)
  function sweep(el, t, starts, dur = 1.1) {
    el = $(el); let sp = -1; starts.forEach((s) => { const k = (t - s) / dur; if (k > 0 && k < 1) sp = k; });
    el.style.opacity = sp < 0 ? 0 : Math.sin(Math.PI * sp); el.style.backgroundPosition = `${100 - Math.max(0, sp) * 100}% 0`;
  }
  // Ken Burns: slow scale between t0 and t1
  function ken(el, t, t0, t1, s0 = 1.0, s1 = 1.06, origin = '50% 50%') {
    el = $(el); el.style.transformOrigin = origin; el.style.transform = `scale(${lerp(s0, s1, ease.inOutSine((t - t0) / (t1 - t0)))})`;
  }
  // Polaroid / photo drop onto a table: lands at t0 + ~0.45·dur
  function drop(el, t, t0, rot = -3, dur = .6) {
    el = $(el); const k = (t - t0) / dur, a = ease.out3(k);
    el.style.display = t < t0 ? 'none' : 'block'; el.style.opacity = cl(k * 3);
    el.style.transform = `translateY(${(1 - a) * -70}px) rotate(${rot + (1 - a) * 9}deg) scale(${lerp(1.22, 1, a)})`;
    el.style.boxShadow = `0 ${lerp(70, 34, a)}px ${lerp(90, 60, a)}px rgba(60,38,14,${lerp(.18, .28, a)}),0 8px 16px rgba(60,38,14,.16)`;
  }
  // iOS-style notification stack: newest on top, older ones pushed down by `gap`
  function stack(cards, t, drops, gap = 200) {
    cards.forEach((c, i) => {
      c = $(c); const a = ease.out4((t - drops[i]) / .5); let push = 0;
      for (let j = i + 1; j < cards.length; j++) push += ease.out3((t - drops[j]) / .45);
      c.style.opacity = cl((t - drops[i]) / .25); c.style.zIndex = 10 + i;
      c.style.transform = `translateY(${push * gap + (1 - a) * -70}px) scale(${lerp(.92, 1, a) - .012 * push})`;
    });
  }

  /* ── scenes ───────────────────────────────────────────────────────────── */
  // SC = [{id:'s1', start:0, end:5}, {id:'s2', start:5, end:9, cut:true}, …]
  // Each scene crossfades in over `fade` s (with a 1.035→1 settle) unless cut:true.
  function scenes(SC, t, fade = .8) {
    let cur = SC[0].id;
    SC.forEach((s, i) => {
      const e = $(s.id); const on = t >= s.start && t < s.end + fade; e.style.display = on ? 'block' : 'none';
      if (t >= s.start) cur = s.id; if (!on) return;
      const k = s.cut ? 1 : ease.inOut4((t - s.start) / fade);
      e.style.opacity = i === 0 ? 1 : k; e.style.zIndex = i;
      e.style.transform = (i === 0 || k >= 1) ? '' : `scale(${1.035 - .035 * k})`;
    });
    return cur;
  }

  /* ── portal: fly THROUGH a shape (a letter of the logo on a wall, etc.) ──
     The next scene is revealed through a mask that matches the shape in the
     photo, while the camera zooms exponentially into a point inside it.
     o = { cam:'#cam3', next:'#s3b', mask: PORTAL (from scripts/make_mask.py),
           rect:{x,y,w,h}  photo position inside the cam layer at zoom 1,
           start, dur, zmax:95, W:1080, H:1920, lightUp:1.3 }                 */
  function portal(t, o) {
    const M = o.mask, sx = o.rect.w / M.w, FX = o.rect.x + M.tx * sx, FY = o.rect.y + M.ty * (o.rect.h / M.h);
    const W = o.W || 1080, H = o.H || 1920, zmax = o.zmax || 95, dur = o.dur || 2.2;
    const p = cl((t - o.start) / dur), z = Math.exp(Math.log(zmax) * ease.inOut3(p));
    const cc = ease.inOutSine(cl((t - (o.start - .8)) / dur)), Cx = lerp(FX, W / 2, cc), Cy = lerp(FY, H / 2, cc);
    const cam = $(o.cam), next = $(o.next);
    cam.style.transformOrigin = '0 0';
    cam.style.transform = `translate(${Cx - FX * z}px,${Cy - FY * z}px) scale(${z})`;
    const blur = (p > 0 && p < 1) ? Math.min(3.5, Math.log(zmax) * dInOut3(p) / dur * .45) : 0;
    cam.style.filter = blur > .3 ? `blur(${blur.toFixed(2)}px)` : 'none';
    if (t < o.start + dur) {
      const w = o.rect.w * z, h = o.rect.h * z, x = Cx + (o.rect.x - FX) * z, y = Cy + (o.rect.y - FY) * z;
      next.style.webkitMaskImage = `url(${M.uri})`; next.style.webkitMaskSize = `${w}px ${h}px`;
      next.style.webkitMaskPosition = `${x}px ${y}px`; next.style.webkitMaskRepeat = 'no-repeat';
      const lu = o.lightUp || 1.3; next.style.opacity = ease.inOutSine((t - (o.start - lu)) / lu);
    } else { next.style.webkitMaskImage = 'none'; next.style.opacity = 1; }
    return z;
  }

  /* ── atmosphere: light leaks, vignette, film grain, fades, bokeh ─────── */
  let OV = null;
  function overlays(opts = {}) {
    const mk = (id, css) => { const d = document.createElement(id === 'grain' ? 'img' : 'div'); d.id = 'pvs-' + id; d.style.cssText = css; document.body.appendChild(d); return d; };
    const W = opts.W || 1080, H = opts.H || 1920, big = Math.max(W, H);
    OV = {
      l1: mk('leak1', `position:absolute;z-index:100;border-radius:50%;mix-blend-mode:screen;pointer-events:none;width:${big * .78}px;height:${big * .78}px;background:radial-gradient(circle,rgba(255,168,92,.55) 0%,rgba(255,140,70,.18) 38%,rgba(255,140,70,0) 68%)`),
      l2: mk('leak2', `position:absolute;z-index:100;border-radius:50%;mix-blend-mode:screen;pointer-events:none;width:${big * .62}px;height:${big * .62}px;background:radial-gradient(circle,rgba(255,214,140,.5) 0%,rgba(255,200,120,.15) 40%,rgba(255,200,120,0) 70%)`),
      vig: mk('vig', 'position:absolute;z-index:101;inset:0;pointer-events:none;background:radial-gradient(ellipse 85% 75% at 50% 48%,rgba(0,0,0,0) 55%,rgba(30,16,4,.38) 100%)'),
      grain: mk('grain', `position:absolute;z-index:102;inset:0;width:${W}px;height:${H}px;opacity:${opts.grain ?? .06};mix-blend-mode:overlay`),
      fo: mk('fade', `position:absolute;z-index:104;inset:0;background:${opts.fadeColor || '#050D26'};opacity:1`),
      W, H, opts,
    };
    OV.grain.src = 'grain0.png';
    return OV;
  }
  // cuts: times where a light-leak flare should bloom; dark: is the current scene dark?
  function atmosphere(t, { cuts = [], dark = true, end, fadeIn = 1, fadeOut = 1, leaks = true } = {}) {
    if (!OV) return; const { W, H } = OV;
    let boost = 0; cuts.forEach((c) => { boost = Math.max(boost, Math.exp(-Math.pow((t - c - .2) / .6, 2))); });
    const base = leaks ? (dark ? .3 : .16) : 0;
    OV.l1.style.left = (-W * .65 + W * .28 * Math.sin(t * .13)) + 'px'; OV.l1.style.top = (-H * .26 + H * .26 * Math.sin(t * .09 + 1)) + 'px';
    OV.l1.style.opacity = leaks ? Math.min(.95, base + boost * .6) : 0;
    OV.l2.style.left = (W * .46 + W * .23 * Math.cos(t * .11)) + 'px'; OV.l2.style.top = (H * .57 + H * .2 * Math.sin(t * .07)) + 'px';
    OV.l2.style.opacity = leaks ? Math.min(.9, base * .8 + boost * .45) : 0;
    OV.fo.style.opacity = Math.max(1 - cl(t / fadeIn), end != null ? cl((t - (end - fadeOut)) / fadeOut) : 0);
    const g = 'grain' + (Math.floor(t * 24) % 4) + '.png'; if (OV.grain.getAttribute('src') !== g) OV.grain.src = g;
  }
  function bokeh(container, n = 14, W = 1080, H = 1920, color = '242,195,82') {
    container = $(container); const L = [];
    for (let i = 0; i < n; i++) {
      const b = document.createElement('div'); const s = 18 + ((i * 37) % 70);
      b.style.cssText = `position:absolute;border-radius:50%;width:${s}px;height:${s}px;filter:blur(2px);background:radial-gradient(circle,rgba(${color},.9),rgba(${color},0) 70%)`;
      container.appendChild(b); L.push([b, (i * 173) % W, (i * 311) % H, .12 + ((i * 7) % 10) / 40, .4 + ((i * 13) % 10) / 12]);
    }
    return { update(t, t0) { L.forEach(([b, x, y, o, sp], i) => { const yy = ((y - (t - t0) * 40 * sp) % (H + 180) + H + 180) % (H + 180) - 100; b.style.left = (x + 30 * Math.sin(t * .5 + i)) + 'px'; b.style.top = yy + 'px'; b.style.opacity = o * cl((t - t0) / 1.5); }); } };
  }

  /* ── preload everything, then signal the renderer ─────────────────────── */
  function ready(urls = [], extra) {
    const L = ['grain0.png', 'grain1.png', 'grain2.png', 'grain3.png', ...urls];
    Promise.all(L.map((u) => new Promise((r) => { const im = new Image(); im.onload = im.onerror = r; im.src = u; })))
      .then(() => document.fonts.ready).then(() => { if (extra) extra(); G.READY = true; });
  }
  const pad = (i, n = 3) => String(i).padStart(n, '0');
  function setSrc(e, s) { e = $(e); if (e.getAttribute('src') !== s) e.src = s; }
  // frame sequence (PNG/JPG folder) → src for time t
  function seq(el, t, t0, folder, count, fps = 30, loop = false, digits = 3, ext = 'png', prefix = 'f_') {
    let f = Math.floor((t - t0) * fps); f = loop ? ((f % count) + count) % count : Math.max(0, Math.min(count - 1, f));
    setSrc(el, `${folder}/${prefix}${pad(f + 1, digits)}.${ext}`);
  }

  /* ── icons (thin line SVG — use these instead of emojis) ──────────────── */
  const sv = (d, fill) => `<svg width="1em" height="1em" viewBox="0 0 24 24" fill="${fill ? 'currentColor' : 'none'}" stroke="${fill ? 'none' : 'currentColor'}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
  const ICONS = {
    mic: sv('<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>'),
    spark: sv('<path d="M12 2l2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/>', true),
    ask: sv('<path d="M4 5h16v11H9l-5 4z"/><path d="M10 9a2 2 0 1 1 2.6 1.9c-.4.2-.6.5-.6 1M12 14h.01"/>'),
    check: sv('<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16.5 9.5"/>'),
    cart: sv('<path d="M3 4h2l2.4 11h10.2L20 8H6.2"/><circle cx="9" cy="19" r="1.4"/><circle cx="17" cy="19" r="1.4"/>'),
    heart: sv('<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>'),
    star: sv('<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>'),
    bolt: sv('<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>'),
    clock: sv('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    qr: sv('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3M21 14v.01M14 21h7v-4"/>'),
    chat: sv('<path d="M4 5h16v11H9l-5 4z"/>'),
    bell: sv('<path d="M6 16V11a6 6 0 1 1 12 0v5l2 2H4zM10 21h4"/>'),
    card: sv('<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M2.5 10h19M6 15h4"/>'),
    users: sv('<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.6"/><path d="M15.5 14.2A5 5 0 0 1 21 19"/>'),
    trophy: sv('<path d="M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 14v4M8 21h8"/>'),
    chart: sv('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
    gift: sv('<rect x="3" y="8" width="18" height="5" rx="1"/><path d="M5 13v8h14v-8M12 8v13M12 8S10 3 7.5 4.5 9 8 12 8zM12 8s2-5 4.5-3.5S15 8 12 8z"/>'),
    apple: '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor"><path d="M16.4 12.7c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.2 2.5-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8s2 .8 3.3.8c1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.7-1-2.7-4zM13.9 5.1c.7-.9 1.2-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>',
    android: '<svg width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor"><path d="M6 9h12v8a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2zM6 8a6 6 0 0 1 12 0z"/><rect x="2.5" y="9" width="2.2" height="7" rx="1.1"/><rect x="19.3" y="9" width="2.2" height="7" rx="1.1"/></svg>',
  };

  /* ── captions synced to a voice-over or a demo ───────────────────────────
     CAPS = [[t0,t1,'cap','mic','Tap the microphone'],          // pill with icon
             [t0,t1,'sub',null,'"I want a latte with oat milk"'], // spoken quote, word-by-word
             [t0,t1,'sub',null,'text', [[w0,w1],…]]]              // optional per-word times (voice.py)  */
  function captions(container, CAPS) {
    container = $(container);
    CAPS.forEach((c, i) => {
      const d = document.createElement('div'); d.className = c[2] === 'cap' ? 'cap' : 'sub'; d.id = container.id + '_c' + i;
      d.innerHTML = c[2] === 'cap' ? `<i>${ICONS[c[3]] || ''}</i><span>${c[4]}</span>` : c[4].split(' ').map((w) => `<span class="wd">${w}</span>`).join(' ');
      container.appendChild(d);
    });
    return {
      update(t) {
        CAPS.forEach((c, i) => {
          const d = document.getElementById(container.id + '_c' + i); const on = t >= c[0] - .05 && t < c[1] + .4;
          d.style.display = on ? 'flex' : 'none'; if (!on) return;
          const a = ease.out4((t - c[0]) / .45), o = ease.inOut4((t - c[1]) / .35);
          d.style.opacity = cl((t - c[0]) / .2) * (1 - o); d.style.transform = `translateY(${(1 - a) * 30}px) scale(${.96 + .04 * a})`;
          if (c[2] !== 'cap') {
            const ws = d.querySelectorAll('.wd'), n = ws.length, span = c[1] - c[0] - .3;
            ws.forEach((w, k) => { const w0 = c[5] ? c[5][k][0] : c[0] + .15 + span * k / n; w.style.opacity = t >= w0 ? 1 : .28; });
          }
        });
      },
    };
  }

  /* ── messaging app conversation (opening "dynamics", stories) ────────────
     const C = chatUI('chat', {name:'Daniela', avatar:'D', status:'online', time:'12:05', lang:'en'});
     C.update(t, MSGS, TYPING, NOTIF)
       MSGS   = [[0.7,'me','Are you at the cafeteria?'], [2.8,'them','Yes, but the line is huge.'], …]
       TYPING = [[1.8,2.8], …]  (the other person is typing)
       NOTIF  = {t:11.2, app:'BRAND', icon:'assets/appicon.png', title:'Order ready', body:'Show your code at the counter.'} */
  function chatUI(container, o = {}) {
    container = $(container); const L = o.lang === 'es' ? { online: 'en línea', typing: 'escribiendo…', msg: 'Mensaje', now: 'ahora' } : { online: 'online', typing: 'typing…', msg: 'Message', now: 'now' };
    container.classList.add('chat');
    container.innerHTML = `<div class="ch-sb"><span>${o.time || '12:05'}</span></div>
      <div class="ch-hd"><span class="ch-back">‹</span><div class="ch-av">${o.avatar || '?'}</div><div><div class="ch-nm">${o.name || ''}</div><div class="ch-st">${L.online}</div></div></div>
      <div class="ch-list"></div><div class="ch-in"><div class="ch-box">${L.msg}</div><div class="ch-send"></div></div>
      <div class="ch-nt"><img><div class="ch-ntx"><div class="ch-nh"><b></b><span>${L.now}</span></div><div class="ch-nti"></div><div class="ch-nb"></div></div></div>`;
    const list = container.querySelector('.ch-list'), st = container.querySelector('.ch-st'), nt = container.querySelector('.ch-nt');
    const typ = document.createElement('div'); typ.className = 'ch-typ'; typ.innerHTML = '<i></i><i></i><i></i>';
    let built = null;
    return {
      update(t, MSGS, TYPING = [], NOTIF = null) {
        if (!built) { built = MSGS.map(([, w, txt, tm]) => { const d = document.createElement('div'); d.className = 'ch-m ' + w; d.innerHTML = `${txt}<span class="ch-tm">${tm || o.time || '12:05'}${w === 'me' ? '<span class="ch-tk">✓✓</span>' : ''}</span>`; return d; });
          if (NOTIF) { nt.querySelector('img').src = NOTIF.icon || ''; nt.querySelector('b').textContent = NOTIF.app || ''; nt.querySelector('.ch-nti').textContent = NOTIF.title || ''; nt.querySelector('.ch-nb').textContent = NOTIF.body || ''; } }
        list.innerHTML = '';
        MSGS.forEach(([t0], i) => { if (t >= t0) { const e = built[i], k = ease.out4((t - t0) / .25); e.style.opacity = k; e.style.transform = `scale(${.92 + .08 * k})`; list.appendChild(e); } });
        const typing = TYPING.some(([a, b]) => t >= a && t < b);
        if (typing) { list.appendChild(typ); [...typ.children].forEach((d, i) => d.style.opacity = .35 + .65 * Math.max(0, Math.sin(t * 7 - i * .9))); }
        st.textContent = typing ? L.typing : L.online;
        if (NOTIF) { const k = ease.out4((t - NOTIF.t) / .45); nt.style.opacity = t < NOTIF.t ? 0 : Math.min(1, k * 1.6); nt.style.transform = `translateY(${(1 - k) * -140}px)`; }
      },
    };
  }

  /* ── data: bar chart, donut, big number bump ─────────────────────────── */
  // bars('bars', [['MON',8,'#7A9862'],…], t, t0, {x0:560, gap:300, w:180, base:830, scale:26, color:'#0F3A93'})
  const _bars = new WeakMap();
  function bars(container, data, t, t0, o = {}) {
    container = $(container); const { x0 = 560, gap = 300, w = 180, base = 830, scale = 26, color = '#0F3A93', label = '#555', size = 64 } = o;
    if (!_bars.has(container)) {
      _bars.set(container, data.map((b, i) => { const x = x0 + i * gap; const mk = (css, txt = '') => { const d = document.createElement('div'); d.style.cssText = 'position:absolute;' + css; d.textContent = txt; container.appendChild(d); return d; };
        return { bar: mk(`left:${x}px;width:${w}px;top:${base}px;height:0;border-radius:24px 24px 6px 6px;background:${b[2]}`),
          num: mk(`left:${x}px;width:${w}px;text-align:center;font-family:Display;font-size:${size}px;color:${color}`),
          lab: mk(`left:${x}px;width:${w}px;text-align:center;top:${base + 18}px;font-family:Display;font-size:${size * .62}px;color:${label}`, b[0]) }; }));
    }
    _bars.get(container).forEach((e, i) => { const k = ease.out4((t - (t0 + i * .35)) / .9), h = data[i][1] * scale * k;
      e.bar.style.height = h + 'px'; e.bar.style.top = (base - h) + 'px'; e.num.style.top = (base - h - size * 1.25) + 'px';
      e.num.textContent = Math.round(data[i][1] * k); e.num.style.opacity = k > .05 ? 1 : 0; e.lab.style.opacity = cl((t - t0 + .2) / .3); });
  }
  // donut('ring', t, t0, 97, {spin:true}) — <svg id="ring" viewBox="0 0 200 200"><circle class="bg" …/><circle class="fg" …/></svg> + a number element
  function donut(svg, t, t0, pct, o = {}) {
    svg = $(svg); const fg = svg.querySelector('.fg'), r = +fg.getAttribute('r'), C = 2 * Math.PI * r, k = ease.out3((t - t0) / (o.dur || 1.6));
    fg.setAttribute('stroke-dasharray', `${C * pct / 100 * k} ${C}`);
    if (o.spin) svg.style.transform = `rotate(${-90 + (t - t0) * (o.spin === true ? 12 : o.spin)}deg)`; else svg.style.transform = 'rotate(-90deg)';
    if (o.num) $(o.num).textContent = Math.round(pct * k) + (o.suffix ?? '%');
  }
  // tiny bump when a counter lands: el.style.transform = `scale(${bump(t,tLand)})`
  // shrink a one-line title until it fits (long brand names, translations): fit('d1', W - 160)
  function fit(el, maxW, minPx = 28) {   // measured on a canvas, so it works while the scene is hidden
    el = $(el); el.style.whiteSpace = 'nowrap'; const cs = getComputedStyle(el), txt = el.textContent;
    const ctx = (fit.c = fit.c || document.createElement('canvas')).getContext('2d'); let fs = parseFloat(cs.fontSize);
    const ls = parseFloat(cs.letterSpacing) || 0, lsr = ls / fs;   // letter-spacing scales with the size
    const w = () => { ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${fs}px ${cs.fontFamily}`; return ctx.measureText(txt).width + lsr * fs * txt.length; };
    while (w() > maxW && fs > minPx) fs -= 2;
    el.style.fontSize = fs + 'px'; if (ls) el.style.letterSpacing = (lsr * fs) + 'px'; return fs;
  }
  const bump = (t, t0, amt = .06, dur = .5) => { const p = (t - t0) / dur; return p > 0 && p < 1 ? 1 + amt * Math.sin(Math.PI * p) : 1; };

  /* ── glory moments: rotating rays + orbiting 4-point sparkles (use sparingly) ── */
  function sparkles(canvas, t, t0, o = {}) {
    canvas = $(canvas); const x = canvas.getContext('2d'), { cx = canvas.width / 2, cy = canvas.height * .42, n = 40, r0 = 300, color = '#F2C352', color2 = '#FFF5D6' } = o;
    x.clearRect(0, 0, canvas.width, canvas.height); const k0 = t - t0; if (k0 < 0) return;
    for (let i = 0; i < n; i++) {
      const a0 = i * 2.399, r = r0 + (i * 53) % 220, s = .3 + ((i * 37) % 10) / 14, z = 4 + (i * 13) % 9, ph = i * .7, kk = k0 - .3 - ph * .05; if (kk < 0) continue;
      const ang = a0 + t * s, rr = r * (.6 + .4 * ease.out4(kk / 1.2)), px = cx + Math.cos(ang) * rr, py = cy + Math.sin(ang) * rr * .9;
      x.globalAlpha = cl(kk / .5) * (.5 + .5 * Math.sin(t * 4 + ph)); x.fillStyle = z % 2 ? color : color2; x.beginPath();
      x.moveTo(px, py - z * 2); x.lineTo(px + z * .5, py - z * .5); x.lineTo(px + z * 2, py); x.lineTo(px + z * .5, py + z * .5); x.lineTo(px, py + z * 2); x.lineTo(px - z * .5, py + z * .5); x.lineTo(px - z * 2, py); x.lineTo(px - z * .5, py - z * .5); x.fill();
    }
    x.globalAlpha = 1;
  }
  // rays: <div class="rays"></div> → rays(el,t,t0)
  function rays(el, t, t0, speed = 6) { el = $(el); el.style.transform = `rotate(${t * speed}deg)`; el.style.opacity = ease.out4((t - t0) / 1.2); }

  Object.assign(G, { $, cl, lerp, ease, rise, write, pop, counter, type, drawPath, sweep, ken, drop, stack, scenes, portal, overlays, atmosphere, bokeh, ready, pad, setSrc, seq,
    ICONS, captions, chatUI, bars, donut, bump, sparkles, rays, fit });
})(window);
