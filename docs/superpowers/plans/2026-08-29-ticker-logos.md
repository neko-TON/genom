# Ticker Logos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add single-color stylized brand glyphs next to every asset ticker (10 stocks + USDG; $GENOM excluded) in the console basket (sim+live), landing tape, and landing mini-basket.

**Architecture:** New `icons.js` (map + `window.tkrIcon(sym)` helper, full code in the spec) loaded by both pages before their main scripts; four one-line injection points in app.js/front.js; one CSS rule per stylesheet. Coordinator polishes glyph paths visually afterwards.

**Tech Stack:** Vanilla JS/SVG/CSS. Verification: node --check, unittest, browser.

**Spec:** `docs/superpowers/specs/2026-08-29-ticker-logos-design.md` — contains the COMPLETE icons.js source, exact injection-point old⇒new lines, and the CSS rules. The implementer MUST read it; this plan does not restate the code.

## Global Constraints

- icons.js content EXACTLY as in the spec; the four injection points and two script tags exactly as listed; the two CSS rules exactly as listed. Nothing else changes.
- `window.tkrIcon` must return "" for unknown symbols (no GENOM entry).
- Commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: icons.js + wiring + CSS

**Files:**
- Create: `icons.js`
- Modify: `app.js` (2 lines), `front.js` (2 lines), `console.html` (1 script tag), `index.html` (1 script tag), `app.css` (+1 rule), `front.css` (+1 rule)

- [ ] **Step 1:** Create `icons.js` with the spec's exact source. Apply the spec's six insertion points and two CSS rules.
- [ ] **Step 2:** Verify: `node --check icons.js front.js app.js` (silent); `grep -c "tkrIcon" app.js front.js` → 2 each; `grep -c "icons.js" index.html console.html` → 1 each; `python3 -m unittest tests.test_server -q` → 46 OK (static-page test still passes; icons.js is served by the existing .js content-type).
- [ ] **Step 3:** Commit:
```bash
git add icons.js app.js front.js console.html index.html app.css front.css
git commit -m "feat: stylized brand glyphs beside asset tickers (basket, tape, mini)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator browser pass

- [ ] Open `/` and `/console.html`: glyphs render beside every stock ticker and USDG in basket/tape/mini; rows aligned; zero console errors; $GENOM rows (wallet/holders) have no glyph.
- [ ] Judge each silhouette at real size (13px): must read as its brand. Path-data polish (only `d`/geometry inside icons.js) goes through fix rounds.
- [ ] Screenshots to the user; then finishing-a-development-branch.
