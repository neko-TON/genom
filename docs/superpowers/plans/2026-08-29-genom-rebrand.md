# Genom Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the site from Nostro Agent / $NSTRO to Genom / $GENOM — texts, entities, CLI, and the new S1 double-helix logo — per the approved spec.

**Architecture:** Mechanical token swaps from exact tables (Tasks 1–2), then the logo replacement on four carriers with in-browser visual tuning (Task 3), then a repo-wide sweep + browser verification (Task 4). Every replacement is authored in this plan; implementers transcribe.

**Tech Stack:** Plain text edits + inline SVG. Verification: `node --check`, `py_compile`, `python3 -m unittest`, `grep`, browser preview.

**Spec:** `docs/superpowers/specs/2026-08-29-genom-rebrand-design.md` (authoritative for the rename map and the S1 logo geometry).

## Global Constraints

- Replace ONLY what the tables list; everything else stays byte-identical. Case matters: `NOSTRO→GENOM`, `Nostro→Genom`, `nostro→genom`, `NSTRO→GENOM`, `nstro→genom`.
- Numbers, addresses, chain id 4663, DEFAULT_RPC, external URLs, holder names, palette/fonts/layout — untouched.
- Acceptance sweep (Task 4): `grep -riE "nostro|nstro" --include="*" --exclude-dir=docs --exclude-dir=.git .` from the repo root must output NOTHING — comments included, `docs/` excluded (history).
- All logo SVGs draw with `stroke="currentColor"` (except favicon.svg which keeps its own `#050A12` plate + `#ABE0FF` stroke), round caps/joins.
- Suite: `python3 -m unittest tests.test_server -v` → 46/46 after Task 2.
- Every commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Brand tokens in HTML + JS

**Files:**
- Modify: `index.html`, `console.html`, `front.js`, `app.js`

- [ ] **Step 1: Apply the replacements** (text nodes / string literals / listed attribute values / the two file-header comments; nothing else)

index.html:
- `<title>Genom…` — old: `Nostro Agent — $NSTRO` ⇒ `Genom Agent — $GENOM`
- wordmark: `NOSTRO&nbsp;AGENT` ⇒ `GENOM&nbsp;AGENT`
- hero kicker: `$NSTRO — A SELF-DRIVING INDEX TOKEN, BOXED IN BY HARD LIMITS` ⇒ `$GENOM — A SELF-DRIVING INDEX TOKEN, BOXED IN BY HARD LIMITS`
- step-00 body: `$NSTRO begins life on the Pons bonding curve` ⇒ `$GENOM begins life on the Pons bonding curve` (rest of sentence unchanged)
- footer: `NOSTRO AGENT — GOING LIVE ON PONS V2` ⇒ `GENOM AGENT — GOING LIVE ON PONS V2`

console.html:
- `<title>`: `Nostro Console — $NSTRO local node` ⇒ `Genom Console — $GENOM local node`
- wordmark: `NOSTRO<em>CONSOLE</em>` ⇒ `GENOM<em>CONSOLE</em>`
- pill: `$NSTRO` ⇒ `$GENOM`
- cardBasket cn: `NostroVault` ⇒ `GenomVault`
- `TOP UP THE NOSTRO VAULT` ⇒ `TOP UP THE GENOM VAULT`
- aria-label: `$NSTRO amount to trade` ⇒ `$GENOM amount to trade`
- cardLive foot: `./nstro connect &lt;vault&gt; [rpc] · ./nstro sim` ⇒ `./genom connect &lt;vault&gt; [rpc] · ./genom sim`
- footer: `Nostro Agent · a full-cycle local simulation` ⇒ `Genom Agent · a full-cycle local simulation`

front.js:
- header comment: `/* NOSTRO front — digit-stream background + live node data */` ⇒ `/* GENOM front — digit-stream background + live node data */`
- (no other NSTRO/Nostro strings exist — verify with grep before finishing)

app.js:
- header comment: `/* NOSTRO CONSOLE — клиент локального узла */` ⇒ `/* GENOM CONSOLE — клиент локального узла */`
- renderBasketLive head: `<span class="cn mono">NostroBasket</span>` ⇒ `<span class="cn mono">GenomBasket</span>`
- commitsTrack: `each hash is an actual NostroCommits transaction` ⇒ `each hash is an actual GenomCommits transaction`
- live holder tags: `"bonding curve · supply still unsold"` stays; `"nostro fee vault"` ⇒ `"genom fee vault"`; `"nostro basket"` ⇒ `"genom basket"`
- renderHolders foot: `the sniper bot grabs 800k $NSTRO` ⇒ `the sniper bot grabs 800k $GENOM`
- wallet stats label: `<span>$NSTRO</span>` ⇒ `<span>$GENOM</span>`
- holders table headers (BOTH renderHolders and renderHoldersLive): `<th class='r'>$NSTRO</th>` ⇒ `<th class='r'>$GENOM</th>`

- [ ] **Step 2: Verify**

Run: `node --check front.js && node --check app.js` (silent). Then `grep -nE "NSTRO|Nostro|NOSTRO|nostro" index.html console.html front.js app.js` — zero matches.

- [ ] **Step 3: Commit**

```bash
git add index.html console.html front.js app.js
git commit -m "rebrand: Genom / \$GENOM across frontend texts

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: server.py, CLI rename, tests, .gitignore, README

**Files:**
- Modify: `server.py`, `tests/test_server.py`, `.gitignore`, `README.md`
- Rename: `nstro` → `genom` (git mv, keep executable bit)

- [ ] **Step 1: Update the tests FIRST (watch them fail)**

In `tests/test_server.py`:
- `cli = str(Path(server.__file__).parent / "nstro")` ⇒ `... / "genom"` (both occurrences)
- `NSTRO_CONFIG` ⇒ `GENOM_CONFIG` (both occurrences)
- `self.assertIn(b"NOSTRO", body)` ⇒ `self.assertIn(b"GENOM", body)`

Run: `python3 -m unittest tests.test_server.TestLive -v` → FAIL (no `genom` file yet). Note: the static-page assertion already passes because Task 1 put GENOM on the page — the failing part is the CLI path/env.

- [ ] **Step 2: Rename the CLI and apply replacements**

```bash
git mv nstro genom
```

In `genom`:
- docstring: `nstro — switch the Nostro node between sim and live modes.` ⇒ `genom — switch the Genom node between sim and live modes.`
- usage lines: `./nstro connect <token-or-vault-address> [rpc-url]`, `./nstro sim`, `./nstro status [port]` ⇒ `./genom …` (three lines)
- `os.environ.get("NSTRO_CONFIG")` ⇒ `os.environ.get("GENOM_CONFIG")`
- usage error: `usage: ./nstro connect <0x-address> [rpc-url]` ⇒ `usage: ./genom connect <0x-address> [rpc-url]`
- User-Agent `"nstro-node/0.1"` ⇒ `"genom-node/0.1"`

In `server.py`:
- module docstring: `Nostro node — backend for the nostro.capital frontend.` ⇒ `Genom node — backend for the site frontend.`
- `server_version = "NostroNode/0.1"` ⇒ `"GenomNode/0.1"`
- User-Agent `"nstro-node/0.1"` ⇒ `"genom-node/0.1"`
- `os.environ.get("NSTRO_CONFIG")` ⇒ `os.environ.get("GENOM_CONFIG")`; `ROOT / "nstro.json"` ⇒ `ROOT / "genom.json"`
- hermetic-test comment mentioning `nstro.json` ⇒ `genom.json`
- log strings: `800k $NSTRO` ⇒ `800k $GENOM`; `your wallet has %s %s $NSTRO` ⇒ `your wallet has %s %s $GENOM`
- argparse `description="Nostro node"` ⇒ `"Genom node"`; startup print `nostro node: http://localhost:%d` ⇒ `genom node: http://localhost:%d`

`.gitignore`: `nstro.json` ⇒ `genom.json`.

`README.md` — replace brand lines (keep everything else):
- header `# nostro.capital — локальный узел` ⇒ `# Genom — локальный узел`
- `Сайт Nostro Agent ($NSTRO): …` ⇒ `Сайт Genom Agent ($GENOM): …`
- the three CLI lines `./nstro connect|sim|status` ⇒ `./genom …`
- `Узел подхватывает nstro.json на лету` ⇒ `Узел подхватывает genom.json на лету`

- [ ] **Step 3: Run the full suite + CLI smoke**

`python3 -m unittest tests.test_server -v` → 46/46. `python3 -m py_compile server.py`. `ls -l genom` shows `-rwxr-xr-x`. Smoke: `./genom sim && cat genom.json && rm genom.json` (writes `{"mode": "sim"}`).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "rebrand: Genom node backend, ./genom CLI, tests, README

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: The S1 helix logo on four carriers

**Files:**
- Modify: `index.html` (`.hd-mark` svg + `.hero-ghost` svg), `console.html` (`.mark` svg), `favicon.svg`

The spec's S1 geometry is authoritative. Base structure for the three inline SVGs (adjust ONLY stroke-widths per carrier; keep classes and aria-hidden of the old svgs):

```html
<svg viewBox="0 0 240 240" fill="none" class="hd-mark" aria-hidden="true">
  <g transform="rotate(-42 120 120) translate(20 5)">
    <g stroke="currentColor" stroke-width="14" stroke-linecap="round" stroke-linejoin="round">
      <path d="M146 -4 C119 10 106 31 100 54 C52 89 52 137 100 172 C106 195 119 216 146 230"/>
      <path d="M54 -4 C81 10 94 31 100 54 C148 89 148 137 100 172 C94 195 81 216 54 230"/>
    </g>
    <g stroke="currentColor" stroke-width="11" stroke-linecap="round">
      <path d="M95 11 L121 11"/><path d="M97 30 L110 30"/>
      <path d="M84 88 L120 88"/><path d="M80 113 L124 113"/><path d="M84 138 L116 138"/>
      <path d="M92 196 L105 196"/><path d="M81 215 L107 215"/>
    </g>
  </g>
</svg>
```

- [ ] **Step 1: Replace the three inline SVGs**

- `index.html` `.hd-mark`: the block above (strands 14 / rungs 11).
- `index.html` `.hero-ghost`: same paths, class `hero-ghost`, strands `6` / rungs `4.5`.
- `console.html` `.mark`: same block with class `mark` (strands 14 / rungs 11).
- Remove nothing else — only the old cube `<g>`+`<path>` content inside each `<svg>` is replaced, and each svg's `viewBox` becomes `0 0 240 240`.

- [ ] **Step 2: Replace favicon.svg**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#050A12"/>
  <g transform="translate(32 32) rotate(-42) scale(0.21) translate(-100 -113)">
    <g stroke="#ABE0FF" stroke-width="20" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M146 -4 C119 10 106 31 100 54 C52 89 52 137 100 172 C106 195 119 216 146 230"/>
      <path d="M54 -4 C81 10 94 31 100 54 C148 89 148 137 100 172 C94 195 81 216 54 230"/>
    </g>
    <g stroke="#ABE0FF" stroke-width="16" stroke-linecap="round" fill="none">
      <path d="M84 88 L120 88"/><path d="M84 138 L116 138"/>
    </g>
  </g>
</svg>
```

- [ ] **Step 3: Creative visual tuning (browser)**

Start the node (`python3 server.py --port 8123` in background or via the coordinator's preview). Open `/` and `/console.html`. Judge like a brand designer, then tune numbers in place:
- The header mark must carry the same optical weight as the old cube next to the wordmark (28px height). If it reads thin, raise strand width up to 16; if clogged, drop to 12.
- The hero-ghost must sit as a light watermark (like the old cube ghost) — if too loud, lower opacity is NOT yours to touch (CSS untouched); adjust stroke 6 → 5.
- Favicon: open `http://localhost:8123/favicon.svg` directly and squint at ~16px; the two rungs must stay visible. Scale factor 0.21 may go 0.19–0.23; keep the mark centered with ~7px margins.
- The composition must not clip: check no path exits the 240-viewBox after rotation (inspect bounding visually; adjust the inner `translate(20 5)` by ±6 if clipping).
Kill the server when done. Note every number you changed in the report.

- [ ] **Step 4: Verify + Commit**

`grep -c "currentColor" index.html console.html` — index has 2 svg marks, console 1. Pages open without errors.

```bash
git add index.html console.html favicon.svg
git commit -m "rebrand: S1 double-helix mark on header, ghost, console, favicon

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Repo sweep + full verification (coordinator-led browser pass)

- [ ] **Step 1:** `grep -riE "nostro|nstro" --exclude-dir=docs --exclude-dir=.git .` from repo root → empty output (exit 1). If anything surfaces, fix it in the file it belongs to and amend the relevant commit message style.
- [ ] **Step 2:** Full suite 46/46; `node --check` both JS; `py_compile server.py`.
- [ ] **Step 3 (coordinator):** browser verification — both pages, zero console errors, GENOM wordmark + helix mark in headers, $GENOM in tape/wallet/holders/log, favicon helix on the tab, `./genom status` against the running node. Screenshots to the user.
- [ ] **Step 4:** No commit unless fixes were needed.
