# Mechanics Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 7-step dense ledger in #how with a 4+3 grid of compact cards (mono tag hero + title + one line), user-approved variant B with approved compressed copy.

**Architecture:** Task 1 swaps the `ol.ledger` markup for `.mech-grid`, removes ALL ledger/kpi CSS across four regions of front.css (keeping the shared `.no` rule and all `.w-col` styling), appends the card CSS + cascade. Task 2 is the coordinator's browser pass, review, merge, deploy.

**Tech Stack:** Static HTML/CSS on existing tokens; reveal via `.rv`/`--d`. Verification: 58-test suite, browser at 4 widths.

**Spec:** `docs/superpowers/specs/2026-08-30-mechanics-cards-design.md`.

## Global Constraints

- Card texts EXACTLY per the spec's table (tags `pons v2`, `80 / 13 / 7`, `bal × t`, `keccak256`, `8 checks`, `1 batch`, `N + 1`; titles and one-liners verbatim from the plan markup below). Section head (`01`, `THE ROUTINE THAT RUNS EVERY 24 HOURS`, seq-rule) untouched.
- The generic `.no` rule (front.css:184) MUST survive — it styles `.w-col .no` and `.ph .no`. All `.w-col` styling survives. Only `.ledger`- and `.kpi`-scoped rules die.
- No new keyframes; cascade via existing `rv` + `--d` in no-preference media.
- Only index.html and front.css change (front.js has zero ledger references — verified).
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Swap ledger → mech-grid + CSS cleanup

**Files:**
- Modify: `index.html` (replace the `<ol class="ledger">…</ol>` block in #how), `front.css` (4 removal regions + 1 appended block)

**Interfaces:**
- Consumes: `.rv` reveal + `--d`; tokens `--line-2`, `--blue`, `--ice`, `--ink`, `--dim`, `--glow-uv`, `--glow-gs`; `.mono` utility.

- [ ] **Step 1: Replace the markup** — in index.html, replace the ENTIRE `<ol class="ledger">` block (opens at line ~168 inside section#how, closes with its matching `</ol>` at line ~211, containing 7 `<li class="rv">`) with EXACTLY:

```html
    <div class="mech-grid">
      <div class="mcard rv">
        <span class="mono mc-no">00</span>
        <span class="mono mc-tag">pons v2</span>
        <b>Born on Pons V2</b>
        <span class="mc-txt">Bonding curve → Uniswap v4. Liquidity locked forever.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">01</span>
        <span class="mono mc-tag">80 / 13 / 7</span>
        <b>3% on every trade</b>
        <span class="mc-txt">80% basket · 13% agent · 7% protocol.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">02</span>
        <span class="mono mc-tag">bal × t</span>
        <b>Share = balance × time</b>
        <span class="mc-txt">No snapshots. Claim anytime.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">03</span>
        <span class="mono mc-tag">keccak256</span>
        <b>Decisions locked first</b>
        <span class="mc-txt">Sealed as a hash before anything moves.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">04</span>
        <span class="mono mc-tag">8 checks</span>
        <b>The vector is vetted</b>
        <span class="mc-txt">Fail one → epoch voided.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">05</span>
        <span class="mono mc-tag">1 batch</span>
        <b>One atomic batch</b>
        <span class="mc-txt">Bad slippage reverts all.</span>
      </div>
      <div class="mcard rv">
        <span class="mono mc-no">06</span>
        <span class="mono mc-tag">N + 1</span>
        <b>Thesis re-hashed</b>
        <span class="mc-txt">Failures are public, forever.</span>
      </div>
    </div>
```

- [ ] **Step 2: CSS removals in front.css** (four regions; `.no` rule at line ~184 and every `.w-col` rule SURVIVE):

  a) `/* ledger */` region (~173-187): delete `.ledger { … }`, `.ledger li { … }`, `.ledger li:hover { … }`, `.ledger li:hover .no, .ledger li:hover .kpi { … }`, `.ledger .no, .ledger .kpi { … }`, `.ledger h3 { … }`, `.ledger p { … }`, `.kpi { … }`. KEEP the standalone `.no { font-size: 13px; … }` rule and the `/* ledger */` comment can be deleted too.

  b) 640px media block (~274-275): delete the two lines `.ledger li { grid-template-columns: 44px 1fr; }` and `.ledger .kpi { grid-column: 2; text-align: left; padding-top: 2px; }`.

  c) sequencer micro-motion block (~310-316): EDIT four selectors to drop the ledger halves —
  `.ledger li, .w-col { transition: transform .3s ease; }` → `.w-col { transition: transform .3s ease; }`;
  `.ledger li .no, .w-col .no { transition: color .3s ease; }` → `.w-col .no { transition: color .3s ease; }`;
  inside its media: `.ledger li:hover, .w-col:hover { transform: translateY(-3px); }` → `.w-col:hover { transform: translateY(-3px); }`;
  `.ledger li:hover .no, .w-col:hover .no { color: var(--ice); }` → `.w-col:hover .no { color: var(--ice); }`;
  and delete the line `@media (max-width: 760px) { .ledger .kpi { display: none; } }`.

  d) scroll-polish cascade (~422-427): delete the six `.ledger li.rv:nth-child(N) { --d: …; }` lines (comment `/* лесенка шагов механики */` тоже).

- [ ] **Step 3: Append card CSS to front.css at EOF:**

```css
/* ---------- mechanics cards ---------- */
.mech-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.mcard {
  border: 1px solid var(--line-2); background: rgba(99, 245, 166, .03);
  padding: 16px 14px 18px; display: flex; flex-direction: column; gap: 8px;
}
.mc-no { font-size: 9px; letter-spacing: .3em; color: var(--blue); text-shadow: var(--glow-uv); }
.mc-tag { font-weight: 700; font-size: 14px; letter-spacing: .08em; color: var(--ice); text-shadow: var(--glow-gs); }
.mcard b { font-weight: 600; font-size: 12.5px; color: var(--ink); line-height: 1.35; }
.mc-txt { font-size: 11px; color: var(--dim); line-height: 1.55; }
@media (max-width: 1060px) { .mech-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 760px) { .mech-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px) { .mech-grid { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: no-preference) {
  .mech-grid .mcard.rv:nth-child(2) { --d: .07s; }
  .mech-grid .mcard.rv:nth-child(3) { --d: .14s; }
  .mech-grid .mcard.rv:nth-child(4) { --d: .21s; }
  .mech-grid .mcard.rv:nth-child(5) { --d: .28s; }
  .mech-grid .mcard.rv:nth-child(6) { --d: .35s; }
  .mech-grid .mcard.rv:nth-child(7) { --d: .42s; }
}
```

- [ ] **Step 4: Verify + commit**

Run: `python3 -m unittest discover -s tests 2>&1 | tail -3` — 58 OK.
Sanity: `grep -c "mech-grid" index.html front.css` → 1 и 1; `grep -c "ledger\|\.kpi" index.html front.css front.js` → 0 в каждом; `grep -c "THE ROUTINE THAT RUNS" index.html` → 1; `grep -c "w-col" front.css` → прежнее ненулевое число (w-col-правила живы); `grep -cE "^\.no " front.css` → 1.

```bash
git add index.html front.css
git commit -m "feat: механика — 7 компактных карточек вместо плотного леджера

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator — browser pass, review, merge, deploy

- [ ] Desktop: 4+3 карточки, каскад слева направо; 1060/760/480 → 3/2/1 колонки; заголовок секции + штрих-код нетронуты; тексты ровно из таблицы спеки.
- [ ] Проверить, что worst-колонки (`.w-col`) сохранили hover-подъём и стили `.no`, а фазы rollout — свои номера.
- [ ] Zero console errors; review; merge per user's menu; push; deploy; prod screenshot.
