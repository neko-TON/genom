# Landing Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the two approved visualization blocks («THE 3% BLOODSTREAM», «LIMITS IN THE DNA»), the micro-animation package, and breathing-room simplification to the landing page — no text changes, no new claims.

**Architecture:** Task 1 inserts two self-contained sections into index.html and all new CSS into front.css. Task 2 adds parallax + count-up to front.js behind the existing REDUCED flag. Task 3 is the coordinator's browser pass with geometry polish.

**Tech Stack:** Inline SVG + CSS animations (offset-path, keyframes), vanilla JS. Verification: node --check, unittest, browser.

**Spec:** `docs/superpowers/specs/2026-08-29-landing-motion-design.md`.

## Global Constraints

- Existing section texts byte-untouched; new visible strings ONLY: `THE 3% BLOODSTREAM`, `EVERY TRADE`, `pays 3%`, `80%`, `13%`, `7%`, `GenomVault — the holders' basket`, `the agent's operations`, `the protocol`, `No one needs to lift a finger — the stream never pauses.`, `LIMITS IN THE DNA`, `WEIGHT ≤ 35%`, `POSITION ≥ 5% OR ZERO`, `TURNOVER ≤ 20% NAV`, `ONE REBALANCE PER EPOCH`, `CASH 0–100%`, `Any failing vector: the epoch is voided and the basket does not move.`
- Every new CSS animation lives inside `@media (prefers-reduced-motion: no-preference)`; every new JS animation is gated by the existing `REDUCED` flag.
- console.html / app.js / app.css / server.py untouched.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Two sections in index.html + all CSS in front.css

**Files:**
- Modify: `index.html` (two section inserts), `front.css` (append block styles + micro-anim + air tweaks)

- [ ] **Step 1: Insert Block 1** — in index.html, immediately AFTER the hero section's closing `</section>` (the one containing the `tape` div) and BEFORE the `<!-- ================= MECHANICS ================= -->` comment:

```html
<!-- ================= FLOW ================= -->
<section class="sec flow-sec">
  <div class="wrap">
    <p class="mono flow-title rv">THE 3% BLOODSTREAM</p>
    <svg viewBox="0 0 900 240" class="flow-svg rv d1" aria-hidden="true">
      <g class="flow-lines">
        <path d="M210 120 C390 120 420 52 610 52"/>
        <path d="M210 120 C390 120 420 120 610 120"/>
        <path d="M210 120 C390 120 420 188 610 188"/>
      </g>
      <g class="flow-dots">
        <circle r="4" class="fd fd80 fda"/>
        <circle r="4" class="fd fd80 fdb"/>
        <circle r="3.5" class="fd fd80 fdc"/>
        <circle r="3.5" class="fd fd80 fdd"/>
        <circle r="3.5" class="fd fd13 fda"/>
        <circle r="3" class="fd fd13 fdb"/>
        <circle r="3" class="fd fd7 fda"/>
      </g>
      <g class="mono flow-left">
        <text x="30" y="112">EVERY TRADE</text>
        <text x="30" y="136" class="flow-sub">pays 3%</text>
      </g>
      <g class="mono">
        <text x="630" y="57" class="flow-pct">80%</text>
        <text x="700" y="57" class="flow-lbl">GenomVault — the holders' basket</text>
        <text x="630" y="125" class="flow-pct">13%</text>
        <text x="700" y="125" class="flow-lbl">the agent's operations</text>
        <text x="630" y="193" class="flow-pct">7%</text>
        <text x="700" y="193" class="flow-lbl">the protocol</text>
      </g>
    </svg>
    <p class="flow-foot rv d2">No one needs to lift a finger — the stream never pauses.</p>
  </div>
</section>
```

- [ ] **Step 2: Insert Block 2** — immediately AFTER the `#how` section's closing `</section>` and BEFORE the `<!-- ================= PROOF ================= -->` comment:

```html
<!-- ================= DNA LIMITS ================= -->
<section class="sec dna-sec">
  <div class="wrap dna-wrap rv">
    <div class="dna-helix" aria-hidden="true">
      <svg viewBox="0 0 150 350">
        <g class="dna-strands">
          <path d="M100 8 C48 46 48 82 100 120 C152 158 152 194 100 232 C48 270 48 306 100 344"/>
          <path d="M50 8 C102 46 102 82 50 120 C-2 158 -2 194 50 232 C102 270 102 306 50 344"/>
        </g>
        <g class="dna-rungs">
          <path class="r1" d="M56 40 L94 40"/>
          <path class="r2" d="M50 96 L100 96"/>
          <path class="r3" d="M56 152 L94 152"/>
          <path class="r4" d="M50 208 L100 208"/>
          <path class="r5" d="M56 264 L94 264"/>
        </g>
      </svg>
    </div>
    <div class="dna-list mono">
      <p class="flow-title">LIMITS IN THE DNA</p>
      <ul>
        <li>WEIGHT ≤ 35%</li>
        <li>POSITION ≥ 5% OR ZERO</li>
        <li>TURNOVER ≤ 20% NAV</li>
        <li>ONE REBALANCE PER EPOCH</li>
        <li>CASH 0–100%</li>
      </ul>
      <p class="dna-foot">Any failing vector: the epoch is voided and the basket does not move.</p>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Append CSS to front.css** (one block, at the end of the file before any final media queries — or simply at EOF):

```css
/* ---------- flow block ---------- */
.flow-sec { padding-bottom: 0; }
.flow-title { font-size: 12px; letter-spacing: .35em; color: var(--dim); }
.flow-svg { width: 100%; max-width: 900px; display: block; margin: 30px auto 8px; }
.flow-lines path { stroke: var(--line-2); fill: none; stroke-width: 1.5; }
.fd { fill: var(--ice); }
.fd80 { offset-path: path("M210 120 C390 120 420 52 610 52"); }
.fd13 { offset-path: path("M210 120 C390 120 420 120 610 120"); }
.fd7  { offset-path: path("M210 120 C390 120 420 188 610 188"); }
.flow-left text { fill: var(--ink); font-size: 19px; letter-spacing: .08em; }
.flow-left .flow-sub { fill: var(--dim); font-size: 13px; }
.flow-pct { fill: var(--ice); font-size: 22px; font-weight: 700; }
.flow-lbl { fill: var(--dim); font-size: 13px; letter-spacing: .04em; }
.flow-foot { font-family: var(--fm); font-size: 12px; color: var(--mute); text-align: center; letter-spacing: .06em; }
@media (prefers-reduced-motion: no-preference) {
  .fd { animation: flowmove linear infinite; }
  .fd80.fda { animation-duration: 2.4s; }
  .fd80.fdb { animation-duration: 2.4s; animation-delay: .6s; }
  .fd80.fdc { animation-duration: 2.8s; animation-delay: 1.2s; }
  .fd80.fdd { animation-duration: 2.8s; animation-delay: 1.8s; }
  .fd13.fda { animation-duration: 3s; }
  .fd13.fdb { animation-duration: 3s; animation-delay: 1.5s; }
  .fd7.fda  { animation-duration: 3.6s; }
}
@media (prefers-reduced-motion: reduce) { .flow-dots { display: none; } }
@keyframes flowmove { from { offset-distance: 0%; } to { offset-distance: 100%; } }

/* ---------- dna limits block ---------- */
.dna-wrap { display: flex; gap: 64px; align-items: center; }
.dna-helix svg { width: 150px; display: block; }
.dna-strands path { stroke: var(--ice); opacity: .5; stroke-width: 5; fill: none; stroke-linecap: round; }
.dna-rungs path { stroke: var(--ice); stroke-width: 4; stroke-linecap: round; opacity: .35; }
@media (prefers-reduced-motion: no-preference) {
  .dna-rungs path { animation: rungpulse 3.2s ease-in-out infinite; }
  .dna-rungs .r2 { animation-delay: .64s; }
  .dna-rungs .r3 { animation-delay: 1.28s; }
  .dna-rungs .r4 { animation-delay: 1.92s; }
  .dna-rungs .r5 { animation-delay: 2.56s; }
}
@keyframes rungpulse { 0%, 100% { opacity: .3; } 50% { opacity: 1; } }
.dna-list ul { list-style: none; padding: 0; margin: 20px 0; display: grid; gap: 14px; }
.dna-list li { color: var(--ink); font-size: 14px; letter-spacing: .08em; }
.dna-list li::before { content: "— "; color: var(--ice); }
.dna-foot { color: var(--mute); font-size: 12px; letter-spacing: .06em; }
@media (max-width: 760px) { .dna-wrap { flex-direction: column; align-items: flex-start; gap: 30px; } }

/* ---------- micro-motion & air ---------- */
.ledger li, .w-col { transition: transform .3s ease; }
.ledger li .no, .w-col .no { transition: color .3s ease; }
@media (prefers-reduced-motion: no-preference) {
  .ledger li:hover, .w-col:hover { transform: translateY(-3px); }
}
.ledger li:hover .no, .w-col:hover .no { color: var(--ice); }
@media (max-width: 760px) { .ledger .kpi { display: none; } }
```

- [ ] **Step 4: Air tweaks in front.css existing rules** (surgical edits):
- `.sec { padding: 120px 0 30px; }` → `padding: 150px 0 30px;`
- In `:root`: `--line: rgba(99, 245, 166, .12);` → `--line: rgba(99, 245, 166, .09);`
- `.worst` grid gap `30px` → `42px` (locate the `.worst` rule; if its gap differs in form, raise whatever gap it declares by 12px).

- [ ] **Step 5: Verify + commit**

`python3 -m unittest tests.test_server -q` (46 OK — landing still contains GENOM); open file sanity `grep -c "flow-sec\|dna-sec" index.html front.css` → 1+1 each in html, 1+1 in css.

```bash
git add index.html front.css
git commit -m "feat: tax-flow and DNA-limits blocks + micro-motion and breathing room

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Parallax + count-up in front.js

**Files:**
- Modify: `front.js`

- [ ] **Step 1:** Inside the main IIFE, after the digit-stream section, add:

```js
  /* ============ hero ghost parallax ============ */
  (function parallax() {
    if (REDUCED) return;
    var ghost = document.querySelector(".hero-ghost");
    if (!ghost) return;
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        ghost.style.transform = "translateY(" + (window.scrollY * 0.08) + "px)";
        ticking = false;
      });
    }, { passive: true });
  })();
```

- [ ] **Step 2:** Add the count-up helper near `tick()` and wire the FIRST successful sim state through it. Add above `tick()`:

```js
  var COUNTED = false;
  function countUp(el, target, render) {
    var t0 = null;
    function step(ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / 800);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = render(target * eased);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
```

In `tick()`, replace the four direct strip assignments:

```js
      $("stEpoch").textContent = s.epoch;
      $("stNav").textContent = fmt(s.nav);
      $("stUnit").textContent = s.unit_value.toFixed(4);
      $("stRun").textContent = fmt(s.treasury.runway_days, 0);
```

with:

```js
      var noSimEarly = s.mode === "live" || s.public;
      if (!COUNTED && !noSimEarly && !REDUCED) {
        COUNTED = true;
        countUp($("stEpoch"), s.epoch, function (v) { return Math.round(v); });
        countUp($("stNav"), s.nav, function (v) { return fmt(v); });
        countUp($("stUnit"), s.unit_value, function (v) { return v.toFixed(4); });
        countUp($("stRun"), s.treasury.runway_days, function (v) { return fmt(v, 0); });
      } else if (COUNTED || noSimEarly || REDUCED) {
        $("stEpoch").textContent = s.epoch;
        $("stNav").textContent = fmt(s.nav);
        $("stUnit").textContent = s.unit_value.toFixed(4);
        $("stRun").textContent = fmt(s.treasury.runway_days, 0);
      }
```

(The animation lasts 0.8s; the next poll is 2s later, so ordinary updates never fight the animation. `COUNTED` also guards live/public modes correctly: they skip straight to direct writes.)

- [ ] **Step 3:** Verify + commit

`node --check front.js` (silent); `python3 -m unittest tests.test_server -q` (46 OK).

```bash
git add front.js
git commit -m "feat: hero-ghost parallax and first-load count-up (reduced-motion aware)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Coordinator browser pass

- [ ] Landing at desktop width: both blocks render in their slots; particles flow along the three streams with 4/2/1 density; helix rungs pulse in sequence; hovers lift the mechanic steps and worst-case cards; scroll moves the ghost; first load counts the strip up; sections breathe (150px rhythm).
- [ ] Geometry polish (SVG path/coordinate tuning only) via fix rounds if a block reads poorly.
- [ ] Code-review check for reduced-motion coverage (all new keyframes inside no-preference media, JS behind REDUCED).
- [ ] Zero console errors; screenshots to the user; then finishing-a-development-branch.
