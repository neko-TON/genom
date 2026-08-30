# Mobile Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the flow diagram readable on phones (vertical variant ≤760px), compact the console top bar on mobile, and enlarge tap targets — desktop/laptop visuals untouched.

**Architecture:** Task 1 adds a second inline SVG (vertical composition) to the flow section plus all its CSS in front.css; visibility switches purely via the existing 760px breakpoint. Task 2 is media-query-only tweaks: console `.top` compaction (app.css) and invisible tap-target extension via absolutely-positioned `::after` overlays (front.css + app.css). Task 3 is the coordinator's browser pass.

**Tech Stack:** Inline SVG + CSS (offset-path particles reuse keyframes `flowmove`), no JS changes. Verification: unittest, browser at 375/768/1280/1680.

**Spec:** `docs/superpowers/specs/2026-08-30-mobile-pack-design.md`.

## Global Constraints

- Zero new visible strings: the vertical SVG reuses verbatim `EVERY TRADE`, `pays 3%`, `80%`, `GenomVault — the holders' basket`, `13%`, `the agent's operations`, `7%`, `the protocol`. No other text anywhere changes.
- All particle animation lives inside `@media (prefers-reduced-motion: no-preference)`; under `reduce` the mobile dots group `.flow-dots-m` is hidden (mirror of `.flow-dots`).
- Visual changes apply only at `max-width: 760px`; wider layouts stay pixel-identical.
- console.html / app.js / front.js / server.py untouched.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Vertical mobile flow diagram (index.html + front.css)

**Files:**
- Modify: `index.html` (one SVG insert in `.flow-sec`)
- Modify: `front.css` (append one CSS block at EOF)

**Interfaces:**
- Consumes: existing classes `.flow-lines`, `.flow-pct`, `.flow-lbl`, `.flow-left`, `.mono`, `.rv`/`.d1` and keyframes `flowmove` (front.css) — the new SVG reuses them all.
- Produces: `.flow-svg-m`, `.flow-top`, `.flow-dots-m`, `.fdm`/`.fdm80`/`.fdm13`/`.fdm7`, timing classes `.fma`–`.fmd` (Task 3 verifies them in browser).

- [ ] **Step 1: Insert the mobile SVG** — in index.html, inside `.flow-sec`, immediately AFTER the existing `</svg>` of `.flow-svg` (currently line ~129) and BEFORE the `.flow-foot` paragraph:

```html
    <svg viewBox="0 0 330 430" class="flow-svg-m rv d1" aria-hidden="true">
      <g class="flow-lines">
        <path d="M165 66 C165 105 30 105 30 146"/>
        <path d="M165 66 C165 165 30 185 30 266"/>
        <path d="M165 66 C165 225 30 265 30 386"/>
      </g>
      <g class="flow-dots-m">
        <circle r="4" class="fdm fdm80 fma"/>
        <circle r="4" class="fdm fdm80 fmb"/>
        <circle r="3.5" class="fdm fdm80 fmc"/>
        <circle r="3.5" class="fdm fdm80 fmd"/>
        <circle r="3.5" class="fdm fdm13 fma"/>
        <circle r="3" class="fdm fdm13 fmb"/>
        <circle r="3" class="fdm fdm7 fma"/>
      </g>
      <g class="mono flow-left flow-top">
        <text x="165" y="30">EVERY TRADE</text>
        <text x="165" y="52" class="flow-sub">pays 3%</text>
      </g>
      <g class="mono">
        <text x="44" y="152" class="flow-pct">80%</text>
        <text x="44" y="174" class="flow-lbl">GenomVault — the holders' basket</text>
        <text x="44" y="272" class="flow-pct">13%</text>
        <text x="44" y="294" class="flow-lbl">the agent's operations</text>
        <text x="44" y="392" class="flow-pct">7%</text>
        <text x="44" y="414" class="flow-lbl">the protocol</text>
      </g>
    </svg>
```

- [ ] **Step 2: Append CSS to front.css at EOF:**

```css
/* ---------- mobile flow diagram ---------- */
.flow-svg-m { display: none; width: 100%; max-width: 360px; margin: 26px auto 8px; }
.flow-top text { text-anchor: middle; }
.fdm { fill: var(--ice); }
.fdm80 { offset-path: path("M165 66 C165 105 30 105 30 146"); }
.fdm13 { offset-path: path("M165 66 C165 165 30 185 30 266"); }
.fdm7  { offset-path: path("M165 66 C165 225 30 265 30 386"); }
@media (prefers-reduced-motion: no-preference) {
  .fdm { animation: flowmove linear infinite; }
  .fdm80.fma { animation-duration: 2.4s; }
  .fdm80.fmb { animation-duration: 2.4s; animation-delay: .6s; }
  .fdm80.fmc { animation-duration: 2.8s; animation-delay: 1.2s; }
  .fdm80.fmd { animation-duration: 2.8s; animation-delay: 1.8s; }
  .fdm13.fma { animation-duration: 3s; }
  .fdm13.fmb { animation-duration: 3s; animation-delay: 1.5s; }
  .fdm7.fma  { animation-duration: 3.6s; }
}
@media (prefers-reduced-motion: reduce) { .flow-dots-m { display: none; } }
@media (max-width: 760px) {
  .flow-svg { display: none; }
  .flow-svg-m { display: block; }
}
```

- [ ] **Step 3: Verify + commit**

Run: `python3 -m unittest tests.test_server -q` — 46 OK.
Sanity: `grep -c "flow-svg-m" index.html` → 1; `grep -c "flow-svg-m" front.css` → 2 (base rule + media block).
Word check — after the insert, each reused string occurs exactly TWICE in index.html (desktop SVG + mobile SVG). Run and expect `2` from each:
`grep -c "GenomVault — the holders' basket" index.html`, `grep -c "the agent's operations" index.html`, `grep -c "the protocol" index.html`, `grep -c "EVERY TRADE" index.html`, `grep -c "pays 3%" index.html`.

```bash
git add index.html front.css
git commit -m "feat: вертикальная flow-диаграмма для мобильных (≤760px)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Console top compaction + tap targets (app.css + front.css)

**Files:**
- Modify: `app.css` (extend the existing `@media (max-width: 760px)` block; append tap-target rules)
- Modify: `front.css` (append tap-target rules)

**Interfaces:**
- Consumes: existing selectors `.top` (app.css:44), `.ctl` (app.css:66), `.top-stats` (app.css:61), `.navlink` (app.css:58), `.lnk` (front.css:128), `.hd-console` (front.css:65). None of these have existing `::after` pseudo-elements (verified).

- [ ] **Step 1: Compact the console top bar** — in app.css, inside the existing `@media (max-width: 760px) { … }` block (starts line ~258), add these rules after the `.b-p { display: none; }` line:

```css
  .top { gap: 10px 14px; padding: 9px 14px 11px; }
  .top-ctl { gap: 6px; }
  .ctl { padding: 5px 9px; font-size: 10.5px; }
  .top-stats { gap: 6px 14px; font-size: 11px; }
```

- [ ] **Step 2: Tap targets, console** — append at app.css EOF:

```css
/* ---------- mobile tap targets ---------- */
@media (max-width: 760px) {
  .navlink { position: relative; }
  .navlink::after { content: ""; position: absolute; left: -6px; right: -6px; top: -11px; bottom: -11px; }
}
```

- [ ] **Step 3: Tap targets, landing** — append at front.css EOF:

```css
/* ---------- mobile tap targets ---------- */
@media (max-width: 760px) {
  .lnk, .hd-console { position: relative; }
  .lnk::after, .hd-console::after { content: ""; position: absolute; left: -6px; right: -6px; top: -10px; bottom: -10px; }
}
```

- [ ] **Step 4: Verify + commit**

Run: `python3 -m unittest tests.test_server -q` — 46 OK.
Sanity: `grep -c "tap targets" app.css front.css` → 1 each; `git diff --stat` shows only app.css and front.css.

```bash
git add app.css front.css
git commit -m "feat: компактная шапка консоли и увеличенные тап-таргеты на мобильных

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Coordinator browser pass

- [ ] 375px landing: vertical diagram shown (horizontal hidden), particles run 4/2/1 along three down-curves, labels ≥11px effective (`13 * renderedWidth/330`), top node centered; no horizontal overflow (`document.documentElement.scrollWidth === innerWidth`).
- [ ] Breakpoint check: at 761px+ (including 768px tablet) the horizontal diagram is shown and the mobile one hidden; at 760px and below — the reverse.
- [ ] 1280/1680 landing: pixel-identical to before (horizontal diagram, no mobile rules active).
- [ ] 375px console: `.top` height ≈ 180px (±15px), all controls visible and clickable; tap-target overlays present (elementFromPoint 8px above a `.navlink` hits the link).
- [ ] Reduced-motion (code-review check): `.fdm` animation inside no-preference; `.flow-dots-m` hidden under reduce.
- [ ] Zero console errors both pages; screenshots (375 / 768 / 1280) to the user; then finishing-a-development-branch.
