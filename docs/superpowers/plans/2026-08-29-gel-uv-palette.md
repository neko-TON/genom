# Gel & UV Palette Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recolor the Genom site from ice-blue to the approved biotech × Robinhood palette (gel green + UV violet) with zero layout/text changes.

**Architecture:** One mechanical task: token swaps per the spec's exact mapping table across front.css, app.css, front.js, app.js, favicon.svg. Then a coordinator-led browser pass (contrast, chart, digit stream, optional banner hue filter decision).

**Tech Stack:** CSS/JS text edits. Verification: grep, node --check, unittest, browser.

**Spec:** `docs/superpowers/specs/2026-08-29-gel-uv-palette-design.md` — its mapping table is the single source of truth; this plan does not restate it to avoid divergence. The implementer MUST read the spec file.

## Global Constraints

- Apply EXACTLY the spec's mapping table — every listed old value replaced with its listed new value, alphas preserved; nothing unlisted changes (no layout, no texts, no fonts, no SVG geometry).
- The optional `.pg-banner` hue filter is NOT applied by the implementer — the coordinator decides it during the browser pass.
- Acceptance grep (case-insensitive) over front.css app.css front.js app.js favicon.svg: zero matches for `171, 224, 255`, `171,224,255`, `#abe0ff`, `#4da3ff`, `#030609`, `#041018`.
- Commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Apply the palette mapping

**Files:**
- Modify: `front.css`, `app.css`, `front.js`, `app.js`, `favicon.svg`

- [ ] **Step 1:** Read the spec's «Карта замен» section and apply every replacement it lists, file by file. Alphas and formatting (spaces inside rgba) follow the EXISTING code style at each site — the mapping speaks in values, not whitespace.

- [ ] **Step 2: Verify**

```bash
grep -inE "171, ?224, ?255|#abe0ff|#4da3ff|#030609|#041018" front.css app.css front.js app.js favicon.svg
```
→ empty (exit 1). Then `node --check front.js && node --check app.js` (silent) and `python3 -m unittest tests.test_server -q` → 46 OK.

- [ ] **Step 3: Commit**

```bash
git add front.css app.css front.js app.js favicon.svg
git commit -m "style: Gel & UV palette — gel green + UV violet over lab-dark base

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator browser pass

- [ ] Open `/` and `/console.html` at desktop width: contrast of ink/dim/mute on the new bg; chart shows green solid + violet dashed; good/bad/warn badges distinct; digit stream green with green-violet sparks; favicon green.
- [ ] Judge the brand-banner: if its blue cast clashes with the green palette, apply the spec's sanctioned one-liner (`.pg-banner { filter: hue-rotate(-60deg) saturate(.8); }` — tune angle/saturation visually) via a fix dispatch; otherwise leave it.
- [ ] Screenshots of both pages to the user. Fixes (if any) go through the fix loop, then merge via finishing-a-development-branch.
