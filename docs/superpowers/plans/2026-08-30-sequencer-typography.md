# Sequencer Typography + Glow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved «Sequencer» typography treatment — light gel-green/UV text glow, blinking caret, type-on section titles, reading-barcodes, ▸ markers, underlined accents — to the landing page and (CSS-only) the console.

**Architecture:** Task 1 is all static typography: glow tokens + CSS rules in front.css and small additive HTML edits in index.html (caret span, 4 barcode divs, `<em class="seq-hl">` wraps). Task 2 adds the type-on effect for the four section titles to front.js behind the existing `REDUCED` flag. Task 3 appends glow rules to app.css for the console. Task 4 is the coordinator's browser pass.

**Tech Stack:** Vanilla CSS (text-shadow, keyframes, media queries), vanilla JS (IntersectionObserver, ES5 style matching front.js). Verification: `node --check`, `python3 -m unittest`, browser.

**Spec:** `docs/superpowers/specs/2026-08-30-sequencer-typography-design.md`.

## Global Constraints

- Not a single word of visible copy changes. Wrapping existing phrases in inline elements is allowed (characters byte-identical). The ONLY new visible strings anywhere: `SEQ 01`, `SEQ 02`, `SEQ 03`, `SEQ 04` (inside `aria-hidden="true"` decorative blocks).
- Glow is static `text-shadow`/`box-shadow` (allowed everywhere, including reduced-motion). Everything that blinks or animates lives inside `@media (prefers-reduced-motion: no-preference)`; JS animation is gated by the existing `REDUCED` flag; the caret is `display: none` under `prefers-reduced-motion: reduce`.
- Glow intensity caps: green alpha ≤ .3, UV alpha ≤ .4 (the token values below are final — do not brighten).
- `console.html`, `app.js`, `server.py`, tests — untouched. Console changes are app.css ONLY.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Static typography — tokens, glow, caret, barcodes, accents (index.html + front.css)

**Files:**
- Modify: `index.html` (caret span in hero h1; 4 barcode divs; 6 `<em class="seq-hl">` wraps)
- Modify: `front.css` (3 token lines in `:root`; appended rule block at EOF)

**Interfaces:**
- Produces: CSS classes `.type-caret`, `.seq-rule`, `.seq-hl`, `.tch`, `.t-on` and keyframes `caret-blink`, `tch-in` (Task 2's JS adds `.tch`/`.t-on` to section h2s; Task 3 reuses the same token names in app.css).

- [ ] **Step 1: Add glow tokens to front.css `:root`** — inside the existing `:root { … }` block (starts line 3), after the `--line-2` line, add:

```css
  --glow-g:  0 0 22px rgba(99, 245, 166, .24);
  --glow-gs: 0 0 14px rgba(99, 245, 166, .38);
  --glow-uv: 0 0 16px rgba(157, 123, 255, .40);
```

- [ ] **Step 2: Caret in hero h1** — in index.html the h1 currently reads (lines 70–74):

```html
    <h1 class="rv d1">
      <span>THE MONEY IS YOURS.</span>
      <span>THE CALLS ARE THE AGENT'S.</span>
      <span class="hl">THE LIMITS ARE THE CONTRACT'S.</span>
    </h1>
```

Add ONE line after the `.hl` span (inside the h1):

```html
      <span class="hl">THE LIMITS ARE THE CONTRACT'S.</span><span class="type-caret" aria-hidden="true"></span>
```

(i.e. the caret span is appended on the same line, immediately after the closing `</span>` of `.hl` — inline flow keeps it on the highlighted line.)

- [ ] **Step 3: Barcode under each section title** — in index.html there are exactly 4 `.sec-head` blocks (lines 137, 223, 249, 276), each shaped like:

```html
    <div class="sec-head rv">
      <span class="mono sec-idx">01</span>
      <h2>THE ROUTINE THAT RUNS<br>EVERY 24 HOURS</h2>
    </div>
```

Immediately after each `</h2>` (still inside `.sec-head`) insert the barcode, with the label matching that section's `sec-idx` number (`SEQ 01`…`SEQ 04`):

```html
      <div class="seq-rule" aria-hidden="true">
        <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i>
        <span>SEQ 01</span>
      </div>
```

- [ ] **Step 4: Accent wraps** — wrap these existing phrases in `<em class="seq-hl">…</em>`, characters unchanged, exactly these 6 occurrences and no others:
  - index.html:77 (`.hero-sub` paragraph): `3% tax` and `MandateGuard`
  - index.html:151 (step 01 paragraph «A 3% charge on every trade»): `80%`, `13%`, and `7%`
  - index.html:169 (step 04 mandate paragraph): `the epoch is voided`

Example for line 77 (result): `…pays a <em class="seq-hl">3% tax</em> that continuously…` and `…thrown out by <em class="seq-hl">MandateGuard</em>.`

- [ ] **Step 5: Append CSS block to front.css at EOF:**

```css
/* ---------- sequencer typography & glow ---------- */
.hero-in h1 { text-shadow: var(--glow-g); }
.hl { text-shadow: none; }
.sec h2 { text-shadow: var(--glow-g); }

.type-caret {
  display: inline-block; width: .38em; height: .09em;
  background: var(--ice); margin-left: .18em;
  box-shadow: 0 0 12px rgba(99, 245, 166, .9);
}
.hero-in h1 span.type-caret { display: inline-block; }
@media (prefers-reduced-motion: no-preference) {
  .type-caret { animation: caret-blink 1.1s steps(1) infinite; }
}
@media (prefers-reduced-motion: reduce) { .type-caret { display: none; } }
@keyframes caret-blink { 50% { opacity: 0; } }

.seq-rule { display: flex; align-items: center; gap: 10px; margin-top: 18px; }
.seq-rule i { display: block; height: 10px; border-left: 2px solid var(--ice); opacity: .9; }
.seq-rule i:nth-child(2n) { height: 6px; opacity: .45; border-color: rgba(157, 123, 255, .9); }
.seq-rule i:nth-child(3n) { height: 8px; opacity: .6; }
.seq-rule span { font-family: var(--fm); font-size: 9px; letter-spacing: .3em; color: var(--mute); }

.flow-title { color: var(--ice); opacity: .8; text-shadow: var(--glow-gs); }
.flow-title::before { content: "\25B8  "; color: rgba(157, 123, 255, .95); text-shadow: var(--glow-uv); }

.seq-hl {
  font-style: normal; color: var(--ink);
  border-bottom: 1px solid rgba(99, 245, 166, .55);
  text-shadow: var(--glow-gs);
}

.strip b { text-shadow: var(--glow-gs); }
.strip-state .cursor { text-shadow: var(--glow-gs); }

@media (prefers-reduced-motion: no-preference) {
  .sec-head h2.t-on .tch { opacity: 0; animation: tch-in .01s steps(1) forwards; }
}
@keyframes tch-in { to { opacity: 1; } }
```

- [ ] **Step 6: Verify + commit**

Run: `python3 -m unittest tests.test_server -q` — expected: 46 tests OK.
Sanity: `grep -c "seq-rule" index.html` → 4; `grep -c "seq-hl" index.html` → 6; `grep -c "type-caret" index.html` → 1; `grep -c "SEQ 0" index.html` → 4.
Word-integrity check (tags stripped, whitespace normalized — the wrapped phrases must read exactly as before): `python3 -c "import re; t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',open('index.html').read())); print('OK' if all(s in t for s in ['pays a 3% tax that continuously','thrown out by MandateGuard','80% purchases','and 7% is','the epoch is voided and the basket does not move']) else 'FAIL')"` → OK.

```bash
git add index.html front.css
git commit -m "feat: sequencer typography — glow tokens, hero caret, section barcodes, accent underlines

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Type-on effect for section titles (front.js)

**Files:**
- Modify: `front.js`

**Interfaces:**
- Consumes: CSS classes `.tch` / `.t-on` and keyframe `tch-in` from Task 1 (already merged when this task runs); existing `REDUCED` flag (front.js:6) and the main IIFE structure.

- [ ] **Step 1: Add the type-on IIFE** — in front.js, inside the main IIFE, immediately AFTER the `/* ============ hero ghost parallax ============ */` block's closing `})();` and BEFORE the next section comment, insert:

```js
  /* ============ sequencer type-on for section titles ============ */
  (function typeOn() {
    if (REDUCED || !("IntersectionObserver" in window)) return;
    var heads = document.querySelectorAll(".sec-head h2");
    if (!heads.length) return;

    function wrap(h2) {
      h2.setAttribute("aria-label", h2.textContent);
      var total = h2.textContent.length || 1;
      var step = Math.min(40, 700 / total);
      var idx = 0;
      Array.prototype.slice.call(h2.childNodes).forEach(function (node) {
        if (node.nodeType !== 3) return; /* keep <br> etc. */
        var frag = document.createDocumentFragment();
        node.textContent.split("").forEach(function (ch) {
          if (ch === " ") { frag.appendChild(document.createTextNode(ch)); return; }
          var s = document.createElement("span");
          s.className = "tch";
          s.textContent = ch;
          s.style.animationDelay = Math.round(idx * step) + "ms";
          idx += 1;
          frag.appendChild(s);
        });
        h2.replaceChild(frag, node);
      });
      h2.classList.add("t-on");
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        wrap(e.target);
      });
    }, { threshold: 0.4 });
    Array.prototype.forEach.call(heads, function (h) { io.observe(h); });
  })();
```

- [ ] **Step 2: Verify + commit**

Run: `node --check front.js` — expected: silent.
Run: `python3 -m unittest tests.test_server -q` — expected: 46 tests OK.

```bash
git add front.js
git commit -m "feat: type-on reveal for section titles (reduced-motion aware)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Console glow (app.css only)

**Files:**
- Modify: `app.css` (3 token lines in `:root`; appended rule block at EOF)

**Interfaces:**
- Consumes: token names `--glow-g` / `--glow-gs` / `--glow-uv` (same values as Task 1; app.css does not import front.css, hence the duplication).

- [ ] **Step 1: Add the same glow tokens to app.css `:root`** — inside the existing `:root { … }` block (starts line 2), at its end add:

```css
  --glow-g:  0 0 22px rgba(99, 245, 166, .24);
  --glow-gs: 0 0 14px rgba(99, 245, 166, .38);
  --glow-uv: 0 0 16px rgba(157, 123, 255, .40);
```

- [ ] **Step 2: Append CSS block to app.css at EOF:**

```css
/* ---------- sequencer glow (console) ---------- */
.wordmark { text-shadow: var(--glow-g); }
.wordmark em { text-shadow: var(--glow-uv); }
.cn { text-shadow: var(--glow-gs); }
.cn::before { content: "\25B8  "; color: rgba(157, 123, 255, .95); text-shadow: var(--glow-uv); }
.top-stats b { text-shadow: var(--glow-gs); }
.pill { text-shadow: var(--glow-gs); }
```

(Note: `.cn::after` already exists and stays; only `::before` is new. No animations are added to the console.)

- [ ] **Step 3: Verify + commit**

Run: `python3 -m unittest tests.test_server -q` — expected: 46 tests OK.
Sanity: `grep -c "glow-uv" app.css` → 3 (1 token + 2 uses); `git diff --stat` shows only app.css.

```bash
git add app.css
git commit -m "feat: sequencer glow for console wordmark, card labels and stats

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Coordinator browser pass

- [ ] Landing, desktop: hero h1 glows softly, `.hl` line has NO glow, caret blinks at the end of the highlighted line without wrapping; scrolling to each section 01–04 types the title on once (~0.7s), barcode + `SEQ 0N` renders under each; `.flow-title` labels show UV ▸ and green glow; the 6 accent phrases are underlined and glowing; strip values glow.
- [ ] Console: wordmark/`GENOM CONSOLE` glows, card `.cn` labels have ▸, top-stats values glow, nothing animates that didn't before.
- [ ] Reduced-motion (code-review check): caret blink and `.tch` stagger are inside `no-preference` media; caret `display:none` under `reduce`; type-on JS returns early on `REDUCED`.
- [ ] Mobile 375px: barcodes don't overflow, caret stays on the line, accents wrap normally.
- [ ] Zero console errors; screenshots to the user; then finishing-a-development-branch.
