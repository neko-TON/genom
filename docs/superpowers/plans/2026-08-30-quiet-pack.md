# Quiet Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove visual noise: decorative barcodes/markers/codes, near-universal text glow, half the background particles, and the type-on title effect — keeping the caret, progress line, diagram particles and DNA glow.

**Architecture:** Task 1 executes all removals across index.html / front.css / app.css / front.js with grep-verified zero-remainder checks. Task 2 is the coordinator's browser pass, review, merge, deploy.

**Tech Stack:** Deletions only (plus two numeric edits in front.js). Verification: node --check, 58-test suite, greps, browser.

**Spec:** `docs/superpowers/specs/2026-08-30-quiet-pack-design.md`.

## Global Constraints

- Page texts stay byte-identical except the removed decorative strings (`SEQ 01`–`SEQ 04`, `LIM-01`–`LIM-05`, card numbers `00`–`06` в mech-карточках).
- KEEP: `.type-caret` rules incl. its box-shadow and blink; `.scroll-progress` rules incl. box-shadow; `.fd`/`.fdm` particle rules; `--glow-*` tokens in BOTH `:root` blocks; all `.rv` reveal cascades; parallax IIFEs; helixSpin.
- Only index.html / front.css / app.css / front.js change.
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Remove the noise

**Files:**
- Modify: `index.html`, `front.css`, `app.css`, `front.js`

- [ ] **Step 1: index.html decor removals**
  - Delete all 4 `<div class="seq-rule" aria-hidden="true">…</div>` blocks (each holds 16 `<i>` + `<span>SEQ 0N</span>`) from the `.sec-head` blocks.
  - In the 5 `.gene` cards: delete each `<span class="mono gene-code">LIM-0N</span>` line.
  - In the 7 `.mcard` cards: delete each `<span class="mono mc-no">0N</span>` line.

- [ ] **Step 2: front.css removals** (rules deleted whole unless noted)
  - `.seq-rule { … }`, `.seq-rule i { … }`, `.seq-rule i:nth-child(2n) { … }`, `.seq-rule i:nth-child(3n) { … }`, `.seq-rule span { … }`.
  - In the scroll-polish no-preference media: the `/* прорисовка штрих-кода слева направо */` comment, `.sec-head.rv.in .seq-rule i { … }` and all 15 `.sec-head.rv.in .seq-rule i:nth-child(N)` delay lines; plus standalone `@keyframes tickin { … }`.
  - `.flow-title::before { … }` (маркер ▸). The `.flow-title` rule itself: удалить из него `text-shadow: var(--glow-gs);` (правило из sequencer-блока `.flow-title { color: var(--ice); opacity: .8; text-shadow: var(--glow-gs); }` становится `.flow-title { color: var(--ice); opacity: .8; }`).
  - `.gene-code { … }` and `.mc-no { … }`.
  - Text-glow strips (remove ONLY the `text-shadow: …;` declaration, keep the rest of each rule): `.hero-in h1 { text-shadow: var(--glow-g); }` (правило целиком, оно только из тени) и парное `.hl { text-shadow: none; }` (целиком); `.sec h2 { text-shadow: var(--glow-g); }` (целиком); в `.seq-hl { … }` — только строку `text-shadow: var(--glow-gs);`; `.strip b { text-shadow: var(--glow-gs); }` (целиком); `.strip-state .cursor { text-shadow: var(--glow-gs); }` (целиком); в `.gene-val { … }` — только строку `text-shadow: var(--glow-g);`; в `.mc-tag { … }` — только строку `text-shadow: var(--glow-gs);`.
  - Scale-glow strips (remove only the `box-shadow: …;` declaration): `.gt-fill`, `.gt-cap`, `.gt-dot`.
  - Type-on removals: in the scroll-polish media the rule `.sec-head h2.t-on .tch { … }`; standalone `@keyframes tch-in { … }`; standalone `.sec-head h2.t-done .tch { … }`.
  - DO NOT touch: `.type-caret` rules, `.scroll-progress`, `.fd*`/`.fdm*`, `--glow-*` tokens, `.rv` system.

- [ ] **Step 3: app.css removals**
  - Delete the whole `/* ---------- sequencer glow (console) ---------- */` block: `.wordmark { text-shadow: … }`, `.wordmark em { … }`, `.cn { text-shadow: … }`, `.cn::before { … }`, `.top-stats b { … }`, `.pill { … }` (эти шесть правил — только глоу-блок в конце файла; базовые правила тех же селекторов в начале файла НЕ трогать).
  - KEEP the `--glow-*` tokens in `:root` and the `body.observer …` rule.

- [ ] **Step 4: front.js edits**
  - `particleCount: window.innerWidth < 760 ? 320 : 700,` → `particleCount: window.innerWidth < 760 ? 160 : 350,`
  - Delete the ENTIRE `/* ============ sequencer type-on for section titles ============ */` IIFE (from its comment line through its closing `})();`).

- [ ] **Step 5: Verify + commit**

Run: `node --check front.js` — silent; `python3 -m unittest discover -s tests 2>&1 | tail -3` — 58 OK.
Zero-greps: `grep -c "seq-rule\|gene-code\|mc-no\|tickin\|typeOn\|t-done\|tch-in\|SEQ 0\|LIM-0" index.html front.css app.css front.js` → 0 в каждом файле; `grep -c "::before" app.css` → 0 или только не-cn (проверить, что `.cn::after` жив: `grep -c "cn::after" app.css` → 1).
Keep-greps: `grep -c "type-caret" front.css` → ≥3; `grep -c "scroll-progress" front.css` → 1; `grep -c "glow-" front.css` → 3 (только строки токенов в :root); `grep -c "glow-" app.css` → 3 (токены).

```bash
git add index.html front.css app.css front.js
git commit -m "style: пакет «Тишина» — минус декор-шум, свечение текстов, половина частиц и type-on

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator — browser pass, review, merge, deploy

- [ ] Лендинг 1280: нет штрих-кодов/▸/кодов; заголовки и теги матовые (без теней); титулы появляются целиком через reveal; фон спокойный; каретка мигает; прогресс-линия светится; частицы диаграммы бегут. 375: сетки складываются, переполнений нет.
- [ ] Консоль: ярлыки без ▸ (` /` суффикс жив), статы без свечения, витрина работает.
- [ ] Zero console errors; review; merge per user's menu; push; deploy.
