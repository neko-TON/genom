# Scroll Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** «Глубина» pack — cascading reveals, barcode draw-in, depth parallax layers, scroll progress hairline. Transform/opacity only; measured 0 jank frames must stay 0.

**Architecture:** Task 1 is CSS-only cascades + the progress bar element/styles (index.html + front.css). Task 2 adds one unified rAF scroll handler (depth layers + progress) to front.js. Task 3 is the coordinator's browser/perf pass, final review, merge, deploy.

**Tech Stack:** Vanilla CSS animations (existing `rv` keyframes + `--d` variable), ES5 JS matching front.js. Verification: node --check, 58-test suite, in-browser 300-frame scroll probe.

**Spec:** `docs/superpowers/specs/2026-08-30-scroll-polish-design.md`.

## Global Constraints

- Only transform/opacity animate. All new CSS animation lives inside `@media (prefers-reduced-motion: no-preference)`; the JS depth parallax is gated by the existing `REDUCED` flag (progress-bar width updates stay active under reduce — user-driven, no transition).
- No text changes; console.html / app.* / server-side untouched. Only index.html, front.css, front.js change.
- Acceptance gate: the 300-frame scroll probe (Task 3) shows 0 frames >20ms and 0 long tasks after the changes.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Cascades + barcode draw-in + progress element (index.html + front.css)

**Files:**
- Modify: `index.html` (one div), `front.css` (append one block)

**Interfaces:**
- Consumes: existing keyframes `rv` (front.css:46) and the `--d` delay variable read by `.rv.in`'s animation (front.css:45); existing markup: 7× `.ledger li.rv`, 3× `.worst .w-col.rv`, `ol.ph.rv` with 4 plain `li`, `.dna-wrap.rv` containing `.dna-list` with 5 plain `li`, `.sec-head.rv` containing `.seq-rule` with 16 `<i>`.
- Produces: `.scroll-progress` element (Task 2 writes its `transform`).

- [ ] **Step 1: Progress element** — in index.html, immediately BEFORE the opening `<header class="hd">` tag insert:

```html
<div class="scroll-progress" aria-hidden="true"></div>
```

- [ ] **Step 2: Append CSS to front.css at EOF:**

```css
/* ---------- scroll polish: каскады, штрих-код, прогресс ---------- */
.scroll-progress {
  position: fixed; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--ice), var(--blue));
  box-shadow: var(--glow-gs);
  transform: scaleX(0); transform-origin: 0 0;
  z-index: 60; pointer-events: none;
}

@media (prefers-reduced-motion: no-preference) {
  /* лесенка шагов механики */
  .ledger li.rv:nth-child(2) { --d: .07s; }
  .ledger li.rv:nth-child(3) { --d: .14s; }
  .ledger li.rv:nth-child(4) { --d: .21s; }
  .ledger li.rv:nth-child(5) { --d: .28s; }
  .ledger li.rv:nth-child(6) { --d: .35s; }
  .ledger li.rv:nth-child(7) { --d: .42s; }
  /* лесенка worst-колонок */
  .worst .w-col.rv:nth-child(2) { --d: .11s; }
  .worst .w-col.rv:nth-child(3) { --d: .22s; }
  /* каскад фаз rollout от появления родителя */
  .ph.rv.in li { animation: rv .55s cubic-bezier(.22, .61, .36, 1) both; }
  .ph.rv.in li:nth-child(2) { animation-delay: .09s; }
  .ph.rv.in li:nth-child(3) { animation-delay: .18s; }
  .ph.rv.in li:nth-child(4) { animation-delay: .27s; }
  /* каскад лимитов ДНК от появления родителя */
  .dna-wrap.rv.in .dna-list li { animation: rv .5s cubic-bezier(.22, .61, .36, 1) both; }
  .dna-wrap.rv.in .dna-list li:nth-child(2) { animation-delay: .08s; }
  .dna-wrap.rv.in .dna-list li:nth-child(3) { animation-delay: .16s; }
  .dna-wrap.rv.in .dna-list li:nth-child(4) { animation-delay: .24s; }
  .dna-wrap.rv.in .dna-list li:nth-child(5) { animation-delay: .32s; }
  /* прорисовка штрих-кода слева направо */
  .sec-head.rv.in .seq-rule i { animation: tickin .25s both; }
  .sec-head.rv.in .seq-rule i:nth-child(2)  { animation-delay: .025s; }
  .sec-head.rv.in .seq-rule i:nth-child(3)  { animation-delay: .05s; }
  .sec-head.rv.in .seq-rule i:nth-child(4)  { animation-delay: .075s; }
  .sec-head.rv.in .seq-rule i:nth-child(5)  { animation-delay: .1s; }
  .sec-head.rv.in .seq-rule i:nth-child(6)  { animation-delay: .125s; }
  .sec-head.rv.in .seq-rule i:nth-child(7)  { animation-delay: .15s; }
  .sec-head.rv.in .seq-rule i:nth-child(8)  { animation-delay: .175s; }
  .sec-head.rv.in .seq-rule i:nth-child(9)  { animation-delay: .2s; }
  .sec-head.rv.in .seq-rule i:nth-child(10) { animation-delay: .225s; }
  .sec-head.rv.in .seq-rule i:nth-child(11) { animation-delay: .25s; }
  .sec-head.rv.in .seq-rule i:nth-child(12) { animation-delay: .275s; }
  .sec-head.rv.in .seq-rule i:nth-child(13) { animation-delay: .3s; }
  .sec-head.rv.in .seq-rule i:nth-child(14) { animation-delay: .325s; }
  .sec-head.rv.in .seq-rule i:nth-child(15) { animation-delay: .35s; }
  .sec-head.rv.in .seq-rule i:nth-child(16) { animation-delay: .375s; }
}
@keyframes tickin { from { opacity: 0; } }
```

(Каскады фаз/ДНК/тиков используют `both`: до старта — from-состояние
(opacity 0), после — собственные базовые стили элемента. Под reduce media
неактивна → всё статично; существующее правило reduce для `.rv` не
задевается.)

- [ ] **Step 3: Verify + commit**

Run: `python3 -m unittest discover -s tests 2>&1 | tail -3` — 58 OK.
Sanity: `grep -c "scroll-progress" index.html front.css` → 1 и 1; `grep -c "tickin" front.css` → 2 (использование + keyframes).

```bash
git add index.html front.css
git commit -m "feat: каскады появления, прорисовка штрих-кодов, элемент линии прогресса

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Unified depth-parallax + progress handler (front.js)

**Files:**
- Modify: `front.js`

**Interfaces:**
- Consumes: `.scroll-progress` from Task 1; existing `REDUCED` flag (front.js:6); elements `.sec-idx` (×4, базовый transform `translateY(2px)` из front.css), `.flow-svg`, `.flow-svg-m`, `.dna-helix svg`; insertion anchor — the caLine IIFE's closing `})();` (the `/* ============ contract address line ============ */` block).

- [ ] **Step 1: Insert the IIFE** — in front.js, immediately AFTER the caLine IIFE's closing `})();` and BEFORE the next section comment, insert:

```js
  /* ============ scroll depth layers & progress ============ */
  (function depth() {
    var bar = document.querySelector(".scroll-progress");
    var se = document.scrollingElement || document.documentElement;
    var layers = [];
    function add(el, factor, cap, base) {
      if (el) layers.push({ el: el, f: factor, cap: cap, base: base });
    }
    var idx = document.querySelectorAll(".sec-idx");
    for (var i = 0; i < idx.length; i++) add(idx[i], -0.05, 18, 2);
    add(document.querySelector(".flow-svg"), 0.04, 14, 0);
    add(document.querySelector(".flow-svg-m"), 0.04, 14, 0);
    add(document.querySelector(".dna-helix svg"), 0.04, 14, 0);

    var ticking = false;
    function frame() {
      ticking = false;
      if (bar) {
        var max = se.scrollHeight - window.innerHeight;
        var p = max > 0 ? Math.min(1, Math.max(0, se.scrollTop / max)) : 0;
        bar.style.transform = "scaleX(" + p + ")";
      }
      if (REDUCED) return;
      var mid = window.innerHeight / 2;
      for (var j = 0; j < layers.length; j++) {
        var L = layers[j];
        var r = L.el.getBoundingClientRect();
        if (r.bottom < -window.innerHeight || r.top > window.innerHeight * 2) continue;
        var d = (r.top + r.height / 2 - mid) * L.f;
        if (d > L.cap) d = L.cap;
        if (d < -L.cap) d = -L.cap;
        L.el.style.transform = "translateY(" + (L.base + d) + "px)";
      }
    }
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(frame);
    }
    window.addEventListener("scroll", onScroll, { passive: true, capture: true });
    window.addEventListener("resize", onScroll, { passive: true });
    onScroll();
  })();
```

(`capture: true` ловит скролл и когда скроллером выступает body, а не
вьюпорт. Чтение rect и запись transform — по одному на слой за кадр,
≤7 слоёв; прогресс-бар обновляется и при REDUCED — движение линии
управляется рукой пользователя.)

- [ ] **Step 2: Verify + commit**

Run: `node --check front.js` — silent; `python3 -m unittest discover -s tests 2>&1 | tail -3` — 58 OK.

```bash
git add front.js
git commit -m "feat: параллакс глубины и линия прогресса — единый rAF-обработчик скролла

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Coordinator — browser/perf pass, final review, merge, deploy

- [ ] Local browser (worktree server): cascades visible on ledger/ph/worst/dna; barcode ticks draw left→right; `.sec-idx` and diagrams drift subtly while scrolling; progress hairline grows; 375px OK; zero console errors.
- [ ] Perf gate: re-run the 300-frame scroll probe (same script as the audit) — 0 frames >20ms, 0 long tasks.
- [ ] Reduced-motion code check: all new CSS animation inside no-preference; JS depth behind REDUCED; bar update unconditional by design.
- [ ] Final whole-branch review; fixes if any; merge to main per user's menu choice; `npx vercel --prod --yes`; re-probe on https://genom-iota.vercel.app; git push.
