# Limits Gene Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the «LIMITS IN THE DNA» helix+list block with five gene cards (code, big value, allowed/cap mini-scale, verbatim limit label), user-approved variant A.

**Architecture:** Task 1 swaps the section markup in index.html, removes the old block's CSS + its scroll-polish cascade lines, appends the gene-card CSS, and drops the dead `.dna-helix svg` parallax layer from front.js. Task 2 is the coordinator's browser pass, review, merge, deploy.

**Tech Stack:** Static HTML/CSS on existing tokens; reveal via the existing `.rv`/`--d` system. Verification: node --check, 58-test suite, browser at 4 widths.

**Spec:** `docs/superpowers/specs/2026-08-30-limits-genes-design.md`.

## Global Constraints

- Verbatim strings preserved: `LIMITS IN THE DNA`, the five limit lines, and `Any failing vector: the epoch is voided and the basket does not move.` The ONLY new visible strings: `LIM-01`…`LIM-05` and the value badges `≤35%`, `≥5%`, `≤20%`, `1×`, `0–100%`.
- No new keyframes; cascade uses the existing `rv` animation + `--d` staggers inside `@media (prefers-reduced-motion: no-preference)`.
- Only index.html / front.css / front.js change; console and other blocks untouched.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Swap the block + CSS + parallax layer cleanup

**Files:**
- Modify: `index.html` (replace one section's inner markup), `front.css` (delete two blocks, append one), `front.js` (delete one line)

**Interfaces:**
- Consumes: existing `.rv` reveal system with `--d`; tokens `--line-2`, `--blue`, `--ice`, `--ink`, `--dim`, `--fd`, `--glow-g`, `--glow-uv`; existing `.flow-title` and `.dna-foot` styles (both kept).

- [ ] **Step 1: Replace the section markup** — in index.html, replace everything from `<section class="sec dna-sec">` through its closing `</section>` (the block containing `.dna-wrap`, the helix svg and `.dna-list`) with EXACTLY:

```html
<section class="sec dna-sec">
  <div class="wrap">
    <p class="mono flow-title rv">LIMITS IN THE DNA</p>
    <div class="gene-grid">
      <div class="gene rv mono">
        <span class="gene-code">LIM-01</span>
        <span class="gene-val">≤35%</span>
        <div class="gene-track"><i class="gt-fill" style="width:35%"></i><i class="gt-cap" style="left:35%"></i></div>
        <span class="gene-lbl">WEIGHT ≤ 35%</span>
      </div>
      <div class="gene rv mono">
        <span class="gene-code">LIM-02</span>
        <span class="gene-val">≥5%</span>
        <div class="gene-track"><i class="gt-zone" style="left:5%;right:0"></i><i class="gt-cap" style="left:5%"></i><i class="gt-dot" style="left:-2px"></i></div>
        <span class="gene-lbl">POSITION ≥ 5% OR ZERO</span>
      </div>
      <div class="gene rv mono">
        <span class="gene-code">LIM-03</span>
        <span class="gene-val">≤20%</span>
        <div class="gene-track"><i class="gt-fill" style="width:20%"></i><i class="gt-cap" style="left:20%"></i></div>
        <span class="gene-lbl">TURNOVER ≤ 20% NAV</span>
      </div>
      <div class="gene rv mono">
        <span class="gene-code">LIM-04</span>
        <span class="gene-val">1×</span>
        <div class="gene-track"><i class="gt-dot" style="left:calc(50% - 4px)"></i></div>
        <span class="gene-lbl">ONE REBALANCE PER EPOCH</span>
      </div>
      <div class="gene rv mono">
        <span class="gene-code">LIM-05</span>
        <span class="gene-val">0–100%</span>
        <div class="gene-track"><i class="gt-fill gt-open" style="width:100%"></i></div>
        <span class="gene-lbl">CASH 0–100%</span>
      </div>
    </div>
    <p class="dna-foot mono rv d2">Any failing vector: the epoch is voided and the basket does not move.</p>
  </div>
</section>
```

- [ ] **Step 2: Remove the old block CSS** — in front.css delete these rules (the `/* ---------- dna limits block ---------- */` region): `.dna-wrap { display: flex; ... }`, `.dna-helix svg { ... }`, `.dna-strands path { ... }`, `.dna-rungs path { ... }`, the `@media (prefers-reduced-motion: no-preference)` block containing `rungpulse` animations for `.dna-rungs`, `@keyframes rungpulse { ... }`, `.dna-list ul { ... }`, `.dna-list li { ... }`, `.dna-list li::before { ... }`, and `@media (max-width: 760px) { .dna-wrap { ... } }`. KEEP `.dna-foot { ... }` (still used). Also delete the five scroll-polish cascade lines in the later media block: `.dna-wrap.rv.in .dna-list li { ... }` and its four `:nth-child` delay lines.

- [ ] **Step 3: Append gene-card CSS to front.css at EOF:**

```css
/* ---------- gene cards (limits) ---------- */
.gene-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 30px; }
.gene {
  border: 1px solid var(--line-2); background: rgba(99, 245, 166, .03);
  padding: 16px 14px 18px; display: flex; flex-direction: column; gap: 12px;
}
.gene-code { font-size: 9px; letter-spacing: .3em; color: var(--blue); text-shadow: var(--glow-uv); }
.gene-val { font-family: var(--fd); font-weight: 600; font-size: 22px; color: var(--ink); text-shadow: var(--glow-g); }
.gene-lbl { font-size: 10px; letter-spacing: .12em; color: var(--dim); line-height: 1.55; }
.gene-track { position: relative; height: 5px; background: rgba(99, 245, 166, .1); }
.gene-track i { position: absolute; display: block; }
.gt-fill { top: 0; bottom: 0; left: 0; background: linear-gradient(90deg, rgba(99, 245, 166, .85), rgba(99, 245, 166, .5)); box-shadow: 0 0 10px rgba(99, 245, 166, .5); }
.gt-open { opacity: .55; }
.gt-zone { top: 0; bottom: 0; background: rgba(99, 245, 166, .35); }
.gt-cap { top: -3px; bottom: -3px; width: 2px; background: var(--blue); box-shadow: 0 0 8px rgba(157, 123, 255, .8); }
.gt-dot { top: -2px; width: 9px; height: 9px; border-radius: 50%; background: var(--ice); box-shadow: 0 0 8px rgba(99, 245, 166, .8); }
@media (max-width: 1060px) { .gene-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 760px) { .gene-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px) { .gene-grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: no-preference) {
  .gene-grid .gene.rv:nth-child(2) { --d: .08s; }
  .gene-grid .gene.rv:nth-child(3) { --d: .16s; }
  .gene-grid .gene.rv:nth-child(4) { --d: .24s; }
  .gene-grid .gene.rv:nth-child(5) { --d: .32s; }
}
```

- [ ] **Step 4: Drop the dead parallax layer** — in front.js, in the depth IIFE, delete the line:

```js
    add(document.querySelector(".dna-helix svg"), 0.04, 14, 0);
```

- [ ] **Step 5: Verify + commit**

Run: `node --check front.js` — silent; `python3 -m unittest discover -s tests 2>&1 | tail -3` — 58 OK.
Sanity: `grep -c "gene-grid" index.html front.css` → 1 и 1; `grep -c "dna-helix\|dna-rungs\|rungpulse\|dna-list\|dna-wrap" index.html front.css front.js` → 0 в каждом; `grep -c "LIMITS IN THE DNA" index.html` → 1; `grep -c "Any failing vector" index.html` → 1.

```bash
git add index.html front.css front.js
git commit -m "feat: блок лимитов — генные карточки со шкалами вместо спирали со списком

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator — browser pass, review, merge, deploy

- [ ] Desktop: 5 карточек в ряд, шкалы соответствуют лимитам (35/5+0/20/1×/весь диапазон), каскад появления слева направо; 1060px → 3 колонки, 760px → 2, 480px → 1; переполнений нет.
- [ ] Word-check: тексты лимитов/титула/хвоста дословны; zero console errors.
- [ ] Review, merge per user's menu, push, deploy, prod screenshot.
