# Site Copy Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rephrase every visitor-visible string on the nostro.capital site (HTML static copy, JS-rendered strings, backend-generated texts) with zero loss of meaning, per the approved spec.

**Architecture:** Pure mechanical string replacement. Every replacement is authored IN THIS PLAN as an exact old ⇒ new pair; implementers transcribe them verbatim — no invention, no improvisation. Layer-by-layer tasks (index.html → console.html → front.js → app.js → server.py+tests), each with its own syntax/test verification, then a final browser pass.

**Tech Stack:** Plain text edits. Verification: `node --check`, `python3 -m py_compile`, `python3 -m unittest`, browser preview.

**Spec:** `docs/superpowers/specs/2026-08-29-site-copy-rewrite-design.md`.

## Global Constraints

- Replace ONLY the strings listed in the tables below, exactly as written. Every string not listed stays byte-identical. Do not rephrase anything on your own initiative.
- Markup, ids, classes, attributes (except listed `title`/`aria-label`/`content` VALUES), JSON keys, code logic, format specifiers (`%s`, `%d`, `%.1f`, `%%`), `{a}`/`{b}`/`{c}` placeholders and string-concatenation structure are untouchable.
- Protected verbatim (never altered inside a replaced string): $NSTRO, NSTRO, Nostro, Nostro Agent, Pons V2, Robinhood Chain, Uniswap V4/v4, USDG, ETH, WETH, MandateGuard, CommitStore, NostroVault, NostroCommits, AgentTreasury, keccak256, abi.encode, Merkle, MetaMask, Rabby, tickers, 0x-addresses, URLs, all numbers and percentages, `python3 server.py`, `./nstro connect <vault> [rpc]`, `./nstro sim`, `processWETH()`.
- Language stays English; ALL-CAPS strings stay ALL-CAPS; sentence-case stays sentence-case.
- Phase nouns (passive, shadow, reduced, full mandate), single-verb control labels (buy, sell, claim), metric labels (EPOCH, NAV, UNIT, RUNWAY, PHASE, block, chain id, etc.) and status chips listed as "keep" are terms — leave them.
- Each task ends with: run its verification, then `git commit`. Every commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Full suite command: `python3 -m unittest tests.test_server -v` (46 tests must pass after Task 5).

---

### Task 1: index.html

**Files:**
- Modify: `index.html`

**Interfaces:**
- Produces: the new slogan and badge wording reused verbatim by Tasks 3–4 for consistency: badge "GOING LIVE ON PONS V2"; slogan lines "THE MONEY IS YOURS." / "THE CALLS ARE THE AGENT'S." / "THE LIMITS ARE THE CONTRACT'S."

- [ ] **Step 1: Apply the replacements**

Replace exactly these strings (old ⇒ new). Text nodes only; tags/attributes/classes unchanged unless the attribute VALUE itself is listed.

Meta and header:
- meta description content: `An index token. A 3% trading tax buys tokenized stocks into a shared basket. An autonomous agent sets the weights; a contract enforces the mandate; every decision is hash-committed before execution.` ⇒ `An index token where a 3% tax on trades keeps purchasing tokenized stocks for a common basket. Weights are chosen by an autonomous agent, the mandate is policed by a contract, and each decision is committed as a hash before it runs.`
- `MECHANICS` ⇒ `THE MACHINERY`
- `PROOF` ⇒ `EVIDENCE`
- `ROLLOUT` ⇒ `LAUNCH PATH`
- `OPEN CONSOLE ↗` ⇒ `LAUNCH CONSOLE ↗`

Hero:
- `LAUNCHING ON PONS V2` ⇒ `GOING LIVE ON PONS V2`
- `$NSTRO — AN INDEX TOKEN THAT RUNS ITSELF, INSIDE HARD LIMITS` ⇒ `$NSTRO — A SELF-DRIVING INDEX TOKEN, BOXED IN BY HARD LIMITS`
- `YOUR CAPITAL.` ⇒ `THE MONEY IS YOURS.`
- `THE AGENT'S DECISIONS.` ⇒ `THE CALLS ARE THE AGENT'S.`
- `THE CONTRACT'S LIMITS.` ⇒ `THE LIMITS ARE THE CONTRACT'S.` (both occurrences: hero and the closing `fin` section)
- hero-sub paragraph: `A 3% tax on every trade keeps buying tokenized stocks into a shared basket. An autonomous agent sets the weights. MandateGuard rejects anything outside the mandate. The agent's key can propose — it can never withdraw.` ⇒ `Every trade pays a 3% tax that continuously purchases tokenized stocks for a common basket. The weights are chosen by an autonomous agent. Anything that steps outside the mandate is thrown out by MandateGuard. The agent's key may only propose — withdrawing is beyond its power.`
- `OPEN THE LIVE CONSOLE&nbsp;→` ⇒ `GO TO THE LIVE CONSOLE&nbsp;→` (both occurrences: hero and `fin`)
- `how it works ↓` ⇒ `see how it runs ↓`

Section 01 (MECHANICS):
- `WHAT HAPPENS<br>EVERY 24 HOURS` ⇒ `THE ROUTINE THAT RUNS<br>EVERY 24 HOURS`
- `Launched on Pons V2, Robinhood Chain` ⇒ `Born on Pons V2, on Robinhood Chain`
- step 00 body ⇒ `$NSTRO begins life on the Pons bonding curve, then graduates to a Uniswap v4 pool whose liquidity is locked forever. The launchpad collects trading fees in ETH and pipes them directly into the contracts described below — no step is manual.`
- `Every trade pays 3%` ⇒ `A 3% charge on every trade`
- step 01 body ⇒ `80% purchases the holders' basket, 13% pays for the agent's operations, and 7% is the protocol's share. On top, creator fees contribute 1% in USDG. No one needs to lift a finger — the stream never pauses.`
- `Shares accrue by balance × time` ⇒ `Your share builds up as balance × time`
- step 02 body ⇒ `There are no snapshots. A bot that shows up one block before the close walks away with nothing. Collect whenever it suits you — no payout calendar exists for anyone to snipe.`
- `The decision is sealed before the trade` ⇒ `Decisions are locked in before any trade`
- step 03 body ⇒ `Before a single asset moves, the agent publishes keccak256(epoch, weights, thesis, nonce). The reasoning is recorded first and the result arrives after — the order is never reversed.`
- `The contract checks the vector` ⇒ `The vector is vetted by the contract`
- step 04 body ⇒ `Whitelisted assets only. Weight ≤ 35%. Position ≥ 5%. Turnover ≤ 20% NAV. A single rebalance per epoch. Cash 0–100%. If any check fails, the epoch is voided and the basket does not move.`
- `Execution is one batch` ⇒ `All execution happens in one batch`
- step 05 body ⇒ `The swaps travel through Uniswap V4 pools as a group. If slippage breaches the limit, the whole batch reverts — no partial fills and no surprises.`
- `The thesis is revealed and re-hashed` ⇒ `The thesis is opened and hashed again`
- step 06 body ⇒ `In the following epoch the text is unsealed and checked against the committed hash. If they disagree, the epoch is branded failed — in public, permanently. Rewriting the track record is impossible.`
- kpi chips (`pons v2`, `80 / 13 / 7`, `bal × t`, `keccak256`, `8 checks`, `1 batch`, `N + 1`): keep.

Section 02 (PROOF):
- `THIS NODE IS RUNNING<br>THE WHOLE THING NOW` ⇒ `EVERYTHING HERE IS ALREADY<br>RUNNING ON THIS NODE`
- `LATEST SEALED DECISION` ⇒ `MOST RECENT SEALED DECISION`
- `/ submitted before execution` ⇒ `/ filed ahead of execution` (keep the surrounding `epoch <span>` markup)
- `connecting to node` ⇒ `linking to the node` (the `cStatus` initial text; keep the cursor span)
- proof-side paragraph ⇒ `In the console you can watch the basket rebalance, the guard throw out bad vectors, the sniper bot come away empty, the breaker, the votes — and trade and claim against it with a wallet of your own.`
- `OPEN THE CONSOLE&nbsp;→` ⇒ `STEP INTO THE CONSOLE&nbsp;→`

Section 03 (WORST CASE):
- `THE DOWNSIDE IS ENGINEERED,<br>NOT PROMISED` ⇒ `THE WORST CASE IS DESIGNED IN,<br>NOT TAKEN ON FAITH`
- `The agent breaks` ⇒ `The agent malfunctions`
- col A body ⇒ `At worst you hold whitelisted stocks in poor proportions, with no more than a fifth of NAV churned per day. Its key simply has no function for withdrawing assets.`
- `Drawdown hits −25% in 7 epochs` ⇒ `A −25% drawdown lands within 7 epochs`
- col B body ⇒ `The breaker halts the agent and moves the basket into USDG to wait. Turning it back on takes a holder vote plus a 3-day timelock — nothing else.`
- `Holders stop trusting it` ⇒ `Holders lose faith in it`
- col C body ⇒ `The limits, the whitelist, even the agent — a vote can swap out any of them. A 3-day timelock leaves those who disagree room to leave first.`

Section 04 (ROLLOUT):
- `TRUST IS EARNED<br>IN PUBLIC` ⇒ `CONFIDENCE IS BUILT<br>OUT IN THE OPEN`
- P0 title `Passive index`: keep (phase term). Body `Static weights. Accrual and claims running, agent off.` ⇒ `Weights fixed in place. Accrual and claiming live; the agent stays off.`
- P1 title `Shadow mode`: keep. Body `30 epochs of sealed public calls, zero execution. Hypothetical charted next to real.` ⇒ `30 epochs of calls sealed in public with zero execution. The hypothetical curve is plotted beside the real one.`
- P2 title `Reduced limits`: keep. Body `Execution live at 7% NAV turnover, 20% weight cap.` ⇒ `Trading switched on with turnover held to 7% NAV and weights capped at 20%.`
- P3 title `Full mandate`: keep. Body `A holder vote unlocks 35% weights, 20% NAV turnover, new whitelist entries.` ⇒ `By holder vote: weights up to 35%, NAV turnover up to 20%, and fresh whitelist entries.`
- `● CURRENT` markers: keep.

Footer:
- `NOSTRO AGENT — LAUNCHING ON PONS V2 · ROBINHOOD CHAIN (4663) · UNISWAP V4.\n  NOT AN OFFER. AGENT DECISIONS ARE HASH-COMMITTED ON-CHAIN BEFORE EXECUTION.` ⇒ `NOSTRO AGENT — GOING LIVE ON PONS V2 · ROBINHOOD CHAIN (4663) · UNISWAP V4.\n  THIS IS NOT AN OFFER. EVERY AGENT DECISION IS COMMITTED ON-CHAIN AS A HASH BEFORE IT EXECUTES.`
- `<title>` tag: keep (product name).

- [ ] **Step 2: Verify**

Run: `git diff --word-diff index.html | head -100` — confirm only text changed, no tags/attrs (other than the meta description value). Grep sanity: `grep -c 'class="' index.html` must equal the pre-edit count (run `git stash` compare if unsure — simpler: `git diff index.html | grep -E '^[+-].*(class=|id=|href=|<)' | grep -vE 'meta name="description"'` and eyeball that every changed line is a text change inside existing tags).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "copy: rewrite landing page text (same meaning, new wording)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: console.html

**Files:**
- Modify: `console.html`

- [ ] **Step 1: Apply the replacements**

- `<title>`: keep. Wordmark `NOSTRO<em>CONSOLE</em>`, pill `$NSTRO`: keep.
- navlink `overview` ⇒ `front page`
- `CONNECT WALLET` ⇒ `LINK WALLET`
- btnPause `title="Pause / resume"` ⇒ `title="Halt / continue"`
- selSpeed `title="Simulation speed"` ⇒ `title="Speed of the simulation"`; options (`epoch = 15s` etc.): keep.
- `next epoch →` ⇒ `skip to next epoch →`; its `title="Close the epoch now"` ⇒ `title="Finish the epoch immediately"`
- cardLive h2 text `Connected contract` ⇒ `Contract currently attached` (keep the `cn` span `on-chain` and the status span)
- cardLive foot: `configured from the terminal: ./nstro connect &lt;vault&gt; [rpc] · ./nstro sim` ⇒ `set up via the terminal: ./nstro connect &lt;vault&gt; [rpc] · ./nstro sim`
- cardOnWallet h2 `On-chain balance & claim` ⇒ `Live balance & claiming` (cn `your wallet`: keep)
- cardActions h2 `Do it on-chain — connected wallet signs` ⇒ `Act on-chain — signed by the attached wallet` (cn `actions`: keep)
- `TRADE ON THE CURVE` ⇒ `DEAL ON THE CURVE`
- `buy with ETH` ⇒ `spend ETH to buy`
- `sell tokens` ⇒ `unload tokens`
- hint `buy/sell run against the Pons bonding curve · 1% fee` ⇒ `buys and sells settle against the Pons bonding curve · 1% fee`
- `FEED THE NOSTRO VAULT` ⇒ `TOP UP THE NOSTRO VAULT`
- `send ETH fees` ⇒ `push ETH fees in`
- `process WETH → split`: keep (maps to processWETH()). `burn stray token` ⇒ `torch a stray token`
- hint `ETH/WETH → 80/13/7 split · other tokens → burned to dead` ⇒ `ETH/WETH are split 80/13/7 · anything else is burned to the dead address`
- cardBasket h2 `Basket` ⇒ `The basket` (cn `NostroVault`: keep)
- cardChart h2 `Unit value: actual vs shadow` ⇒ `Unit value — realized vs shadow` (cn `NAV`: keep)
- legend `actual (executed)` ⇒ `realized (executed)`; `agent shadow (no execution)` ⇒ `the agent's shadow (never executed)`
- cardTrack h2 `Track record · hash lands before the swap · click an epoch for details` ⇒ `Track record · the hash arrives ahead of the swap · open any epoch for detail` (cn `CommitStore`: keep)
- cardWallet h2 `Balance & claim` ⇒ `Holdings & claiming` (cn `your wallet`: keep); buttons `buy`/`sell`/`claim`: keep
- cardWallet foot `No claim schedule: whatever has accrued can be taken at any moment.` ⇒ `There is no claiming timetable — anything accrued is yours to take at any time.`
- cardHolders h2 `Holders` ⇒ `The holders` (cn `weight × time`: keep)
- cardGuard h2 `Latest vector check` ⇒ `Most recent vector check` (cn `MandateGuard`: keep)
- cardTreasury h2 `Operations` ⇒ `Operating budget` (cn `AgentTreasury`: keep)
- cardGov h2 `Governance`: keep (term); cn `vote · 3-day timelock`: keep
- cardLog h2 `Node log` ⇒ `Node journal`; cn `events` ⇒ `activity`
- aria-labels: `ETH to spend` ⇒ `amount of ETH to spend`; `tokens to sell` ⇒ `how many tokens to sell`; `ETH to send` ⇒ `amount of ETH to send`; `Trade amount, $NSTRO` ⇒ `$NSTRO amount to trade`
- footer: `Nostro Agent · local full-cycle simulation of concept v0.1 · genuine keccak256 + abi.encode ·\n  Robinhood Chain / Pons V2 / Uniswap V4 are emulated by this node` ⇒ `Nostro Agent · a full-cycle local simulation of concept v0.1 · real keccak256 + abi.encode ·\n  this node emulates Robinhood Chain / Pons V2 / Uniswap V4`

- [ ] **Step 2: Verify**

`git diff --word-diff console.html` — text-only changes (plus the listed title/aria-label values). All ids (`btnBuy`, `cardBasket`, …) and classes unchanged.

- [ ] **Step 3: Commit**

```bash
git add console.html
git commit -m "copy: rewrite console page text

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: front.js strings

**Files:**
- Modify: `front.js`

**Interfaces:**
- Consumes: Task 1's badge wording (`GOING LIVE ON PONS V2`).
- Produces: chip texts reused by Task 4: `ON-CHAIN · LIVE`, `ON STANDBY`.

- [ ] **Step 1: Apply the replacements** (string literals only; concatenation structure untouched)

- `"NODE OFFLINE — RUN: python3 server.py"` ⇒ `"NODE DOWN — START IT: python3 server.py"`
- `"LIVE ON-CHAIN"` ⇒ `"ON-CHAIN · LIVE"`
- `"STANDBY / LAUNCHING ON PONS V2"` ⇒ `"ON STANDBY / GOING LIVE ON PONS V2"`
- `"SIM DATA / LOCAL NODE / CONCEPT V0.1"` ⇒ `"SIMULATED DATA / LOCAL NODE / CONCEPT V0.1"`
- `"THE TOKEN ADDRESS IS NOT CONNECTED YET"` ⇒ `"NO TOKEN ADDRESS HAS BEEN ATTACHED YET"`
- `"reading the chain…"` ⇒ `"pulling chain state…"`
- `'thesis sealed until the epoch closes<span class="cursor">▌</span>'` ⇒ `'the thesis stays sealed until the epoch ends<span class="cursor">▌</span>'`
- `"revealed / keccak256 verified / on the public record"` ⇒ `"opened / keccak256 checked out / part of the public record"`
- `"revealed / hash mismatch / epoch marked failed"` ⇒ `"opened / hashes disagree / epoch stamped failed"`
- `'commits go on the public record once the vault is live<span class="cursor">▌</span>'` ⇒ `'once the vault is live, commits land on the public record<span class="cursor">▌</span>'`
- Live-strip fragments (`"CHAIN <b>"`, `"BLOCK <b>"`, `" SUPPLY <b>"`, `"CURVE <b>"`, `"TOKEN <b>"`, `"EPOCH <b>"`, `"VAULT <b>"`, `"GRADUATED · UNISWAP V4"`): keep (metric labels/terms).

- [ ] **Step 2: Verify**

Run: `node --check front.js` → no output (syntax OK). `git diff --word-diff front.js` — only string literal contents changed.

- [ ] **Step 3: Commit**

```bash
git add front.js
git commit -m "copy: rewrite landing status strings

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: app.js strings

**Files:**
- Modify: `app.js`

**Interfaces:**
- Consumes: Task 3's chips (`ON-CHAIN · LIVE`, `ON STANDBY`) — use identical texts.

- [ ] **Step 1: Apply the replacements** (string literals only; keep all HTML fragments' tags/classes; format of concatenations untouched)

Live renderers:
- `' Basket — real holdings on Uniswap v4'` ⇒ `' Basket — actual positions on Uniswap v4'`
- `"NAV ≈ "` keep; `" USDG · agent target: "` ⇒ `" USDG · the agent's target: "`
- `' Unit value — real prices, real epochs'` ⇒ `' Unit value — genuine prices, genuine epochs'`
- `'unit value since epoch 1 ('` ⇒ `'unit value from epoch 1 ('` (suffix `" epochs)</span>"` keep)
- `' Holders — indexed from Transfer logs'` ⇒ `' Holders — built from Transfer logs'`
- `"bonding curve · unsold supply"` ⇒ `"bonding curve · supply still unsold"`
- holders-live foot `'Shares accrue as balance × holding time, indexed straight from on-chain Transfer events.'` ⇒ `'Shares build up as balance × time held, derived directly from on-chain Transfer events.'`
- `' Latest vector check — epoch '` ⇒ `' Freshest vector check — epoch '`
- `'epoch cancelled: '` ⇒ `'epoch voided: '` (renderGuardLive)
- `'vector accepted'` ⇒ `'vector cleared'`; `" and executed on-chain via Uniswap v4"` ⇒ `" and carried out on-chain via Uniswap v4"`; `" · sealed, no trade needed"` ⇒ `" · sealed; no trade was required"`

commitsTrack + renderTrack badges (identical in both places):
- `'mismatch — failed'` ⇒ `'hashes disagree — failed'`
- `'keccak verified'` ⇒ `'keccak checked'`
- `'thesis sealed'` ⇒ `'thesis under seal'`
- `'ON-CHAIN TRACK RECORD · every hash is a real transaction in NostroCommits'` ⇒ `'TRACK RECORD ON-CHAIN · each hash is an actual NostroCommits transaction'`
- `" · on-chain, awaiting reveal"` ⇒ `" · on-chain, reveal pending"`
- `" · trade → reveal next epoch"` ⇒ `" · trade → unsealed next epoch"`
- `'the agent has not submitted a vector yet (phase 0)'` ⇒ `'no vector has come from the agent so far (phase 0)'`
- renderTrack `'epoch cancelled: '` ⇒ `'epoch voided: '`

renderLaunch:
- `"standby — the token address has not been connected yet"` ⇒ `"standby — no token address attached yet"`
- `"connecting…"` ⇒ `"linking up…"`
- `"chain unreachable"` ⇒ `"chain out of reach"`
- `"watching the launch token"` ⇒ `"tracking the launch token"`; `"reading the vault"` ⇒ `"polling the vault"` (suffix `" every 4s"` keep)
- cell labels: keep, except `"ready to graduate"` ⇒ `"graduation ready"`, `"creator fees accrued"` ⇒ `"creator fees piled up"`, `"nostro vault · received"` ⇒ `"nostro vault · taken in"`, `"100% — pool is live, LP locked"` ⇒ `"100% — the pool is live and LP is locked"`, `"registered"` ⇒ `"on record"`, `"not found"` ⇒ `"absent"`
- `'trade on pons ↗'` ⇒ `'swap on pons ↗'`; `'explorer ↗'` ⇒ `'block explorer ↗'`

renderTop:
- `"LIVE ON-CHAIN"` ⇒ `"ON-CHAIN · LIVE"`; `"STANDBY"` ⇒ `"ON STANDBY"`; `"SIM"` keep
- `"<span>waiting for the token address</span>"` ⇒ `"<span>awaiting a token address</span>"`
- `" · shadow"`, `" · passive"`, labels `epoch/phase/NAV/unit/runway … days`: keep

renderAlerts:
- breaker alert: `'BREAKER: drawdown exceeded −25% over 7 epochs — agent frozen since epoch '` ⇒ `'BREAKER: the drawdown passed −25% within 7 epochs — the agent has been frozen since epoch '`; `", basket moved to USDG. Unlock requires a vote."` ⇒ `" and the basket now sits in USDG. Only a vote can unlock it."`
- `>vote to unfreeze<` ⇒ `>cast an unfreeze vote<`
- hold alert `'Runway under 14 days: hold mode — one rebalance every three days.'` ⇒ `'Less than 14 days of runway: hold mode — rebalancing only once every three days.'`

renderBasket foot:
- `"tax queued for the batch buy: "` ⇒ `"tax waiting for the batch purchase: "`; `" USDG · epoch volume: "` ⇒ `" USDG · volume this epoch: "`

trackDetails:
- `"<h4>MandateGuard · vector check at submission</h4>"` ⇒ `"<h4>MandateGuard · check performed at submission</h4>"`
- `"<h4>Executor · batch (" + ... + " bps max impact, cost " + ... + " USDG)</h4>"` ⇒ change the literal fragments to `" bps of max impact, "` and `" USDG in costs)</h4>"`, i.e. `"<h4>Executor · batch (" + submitted.exec.max_impact_bps + " bps of max impact, " + fmt(submitted.exec.cost, 2) + " USDG in costs)</h4>"`
- `'shadow phase — no execution'` ⇒ `'shadow phase — nothing is executed'`

renderGuard:
- `'phase '` + phase + `" limits: weight ≤ "` ⇒ `'limits in phase '` + phase + `": weight ≤ "` (rest of the fragment `"% · turnover ≤ " … "% NAV"` keep)
- `'no checks yet'` ⇒ `'nothing checked yet'`
- `'Epoch ' + (last.n + 1) + " cancelled: "` ⇒ `'Epoch ' + (last.n + 1) + " voided: "`
- `'vector for epoch ' + (last.n + 1) + " accepted"` ⇒ `'vector for epoch ' + (last.n + 1) + " cleared"`; `" and executed in one batch"` ⇒ `" and run as a single batch"`; `" (shadow, no execution)"` ⇒ `" (shadow — not executed)"`

renderHolders foot:
- `'The sniper bot buys 800k $NSTRO twelve seconds before every close — its share tends to zero: weight is balance × time.'` ⇒ `'Twelve seconds before each close the sniper bot grabs 800k $NSTRO — and its share still approaches zero, because weight is balance × time.'`
- table headers and `you`/`bot` tags: keep

renderTreasury:
- `"<span>days of runway"` ⇒ `"<span>runway, days"`
- `"Cost per epoch (inference + gas)"` ⇒ `"Per-epoch cost (inference + gas)"`
- `"Inflow: 13% of the tax"` ⇒ `"Incoming: the tax's 13%"`
- `"Inflow: 1% creator fees"` ⇒ `"Incoming: 1% creator fees"`
- `"Protocol fund (7%)"` ⇒ `"Protocol pot (7%)"`
- `"USDG balance"`, `badge-hold` text `hold mode`: keep

renderGov:
- `'queue is empty'` ⇒ `'nothing in the queue'`
- `" — <b>timelock until epoch "` ⇒ `" — <b>locked until epoch "`
- `>vote: phase 3<` ⇒ `>vote for phase 3<`; `>vote: unfreeze<` ⇒ `>vote to unfreeze<`
- foot `'Every change is a holder vote plus a 3-day timelock (3 epochs). Three days for dissenters to exit.'` ⇒ `'Any change takes a holder vote and a 3-day timelock (3 epochs) — three days in which dissenters can leave.'`
- phase steps `P0 · passive` …: keep

Wallet actions:
- `"No wallet extension found. Install MetaMask / Rabby and reload."` ⇒ `"No wallet extension detected. Add MetaMask / Rabby and reload the page."`
- `"connect a wallet first"` ⇒ `"attach a wallet first"`
- `" — confirm in your wallet…"` ⇒ `" — approve it in your wallet…"`
- `" sent: "` ⇒ `" dispatched: "` (both occurrences: sendTx and sell)
- `" failed: "` ⇒ `" did not go through: "` (all occurrences)
- `"rejected"` ⇒ `"declined"` (all occurrences)
- `"no curve — token may have graduated"` ⇒ `"curve missing — the token has likely graduated"` (both occurrences)
- `"approve curve → sell (two signatures)…"` ⇒ `"approve the curve, then sell (two signatures)…"`
- `"buy " + eth + " ETH"` ⇒ `"buy for " + eth + " ETH"`
- `"feed " + eth + " ETH to vault"` ⇒ `"top up vault with " + eth + " ETH"`
- `"Token address to burn from the vault (0x…):"` ⇒ `"Which token should the vault burn (0x… address):"`
- `"bad address"` ⇒ `"address is invalid"`
- `"claiming " + open.length + " epochs, one signature per epoch…"` ⇒ `"claiming " + open.length + " epochs — one signature each…"`
- `"claim epoch "` (both occurrences): keep (action label)

renderClaimBox:
- `'Nothing distributed to this wallet yet. Rewards accrue as balance × time and are published on-chain each epoch.'` ⇒ `'This wallet has received no distributions so far. Rewards build up as balance × time and go on-chain every epoch.'`
- `"claimable ETH"` ⇒ `"ETH claimable"`; `"open epochs"` ⇒ `"epochs open"`; `"already claimed"` ⇒ `"claimed already"`
- foot `'Each epoch\'s payout is fixed on-chain by a Merkle root — the amount is proven, not trusted.'` ⇒ `'Every epoch\'s payout is pinned on-chain by a Merkle root — the sum is proven rather than trusted.'`
- `">claim "` button prefix: keep

- [ ] **Step 2: Verify**

Run: `node --check app.js` → OK. `git diff --word-diff app.js` — string contents only; every id/class/selector (`data-trade`, `#btnClaim`, `.t-badge`, SEL constants, `h.kind === "user"`, `action` strings) untouched.

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "copy: rewrite console UI strings

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: server.py visible texts + test sync

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py` (guard-name assertions)

**Interfaces:**
- Produces: new guard check names, exact list and order (Task 6 relies on them rendering): `whitelist`, `weight cap`, `position floor`, `turnover`, `one rebalance`, `cash range`, `weights total`, `agent state`.

- [ ] **Step 1: Update the test FIRST (it must fail)**

In `tests/test_server.py`:
- `test_guard_checks_present_and_named`: replace the expected list with
  `["whitelist", "weight cap", "position floor", "turnover", "one rebalance", "cash range", "weights total", "agent state"]`
- `test_frozen_agent_cancels_epochs`: `c["name"] == "agent status"` ⇒ `c["name"] == "agent state"`

Run: `python3 -m unittest tests.test_server.TestAgent.test_guard_checks_present_and_named -v` → FAIL (old names still in server.py).

- [ ] **Step 2: Apply server.py replacements**

Thesis templates:
```python
THESIS_LEADS = [
    "The momentum behind {a} and {b} is still alive; buying into the strength.",
    "Cutting back {a} after its run and rotating the proceeds into {b}.",
    "The earnings setup leans toward {a}; {b} stays at its benchmark weight.",
    "With the volatility regime climbing, concentration in {a} is being reduced.",
    "Inflows to tokenized {a} continue to build; {b} remains the funding leg.",
]
THESIS_TAILS = [
    "Keeping {c}% in cash as dry powder.",
    "Lifting cash to {c}% before the macro print.",
    "Cash sits at {c}%; turnover stays comfortably within the mandate.",
]
```
- `"Basket parked in USDG; awaiting mandate."` ⇒ `"The basket is parked in USDG while a mandate is awaited."`

Guard check names (in `_guard_checks`, keep order):
- `"max weight"` ⇒ `"weight cap"`; `"min position"` ⇒ `"position floor"`; `"single rebalance"` ⇒ `"one rebalance"`; `"cash band"` ⇒ `"cash range"`; `"weights sum"` ⇒ `"weights total"`; `"agent status"` ⇒ `"agent state"`; `"whitelist"` and `"turnover"` keep.

Guard details (format specifiers untouched):
- `"%d assets checked"` ⇒ `"%d assets screened"`
- `"%s not whitelisted"` ⇒ `"%s is off the whitelist"`
- `"top %s %.1f%% %s %.1f%%"` ⇒ `"largest %s %.1f%% %s %.1f%%"`
- `"all positions ≥ 5% or zero"` ⇒ `"every position ≥ 5% or exactly zero"`
- `"%s at %.1f%% < 5%%"` ⇒ `"%s sits at %.1f%% < 5%%"`
- `"1 of 1 this epoch"` ⇒ `"1 rebalance of 1 this epoch"`
- `"hold mode: one rebalance per 3 epochs"` ⇒ `"hold mode: a single rebalance every 3 epochs"`
- `"cash %.1f%% within 0–100%%"` ⇒ `"cash %.1f%% inside 0–100%%"`
- `"sum %.2f%%"` ⇒ `"total %.2f%%"`
- `"agent frozen — breaker active"` ⇒ `"agent on ice — breaker engaged"`
- `"agent active"` ⇒ `"agent operational"`

Log messages:
- `"node online — passive index, phase 0"` ⇒ `"node up — passive index, phase 0"`
- `"phase 1 — shadow mode: sealed calls, no execution"` ⇒ `"phase 1 — shadow mode: calls are sealed, nothing executes"`
- `"phase 2 — execution live at reduced limits"` ⇒ `"phase 2 — trading enabled under reduced limits"`
- `"sniper bot bought 800k $NSTRO 12s before the close"` ⇒ `"12s before the close, the sniper bot picked up 800k $NSTRO"`
- `"sniper exited right after the close — share ~0 (balance × time)"` ⇒ `"right after the close the sniper left — share ~0 (balance × time)"`
- `"your wallet %s %s $NSTRO"` ⇒ `"your wallet has %s %s $NSTRO"` (args unchanged)
- `"you claimed %.2f USDG"` ⇒ `"you collected %.2f USDG"`
- `"epoch %d thesis revealed — keccak %s"` ⇒ `"epoch %d thesis unsealed — keccak %s"`; its args `"verified" if rec["verified"] else "MISMATCH"` ⇒ `"confirmed" if rec["verified"] else "MISMATCH"`
- `"epoch %d decision sealed: %s…"` ⇒ `"decision for epoch %d sealed: %s…"` (argument order already `(next_epoch, h[:18])` — unchanged)
- `"epoch %d CANCELLED by MandateGuard: %s"` ⇒ `"MandateGuard voided epoch %d: %s"`
- `"batch executed: %d trades, max impact %d bps, cost %.2f USDG"` ⇒ `"batch complete: %d trades, %d bps max impact, %.2f USDG in costs"`
- `"runway under 14 days — hold mode: one rebalance per 3 epochs"` ⇒ `"under 14 days of runway — hold mode: one rebalance every 3 epochs"`
- `"BREAKER: drawdown ≤ −25% over 7 epochs — frozen, basket parked in USDG"` ⇒ `"BREAKER: a −25% drawdown inside 7 epochs — agent frozen, basket sitting in USDG"`
- `"governance: phase 3 unlocked — full mandate"` ⇒ `"governance: full mandate — phase 3 is open"`
- `"governance: agent unfrozen by holder vote"` ⇒ `"governance: holders voted the agent back on"`
- `"governance vote queued: %s — timelock 3 epochs"` ⇒ `"vote queued: %s — 3-epoch timelock"`

Governance labels:
- `"Vote: unlock phase 3 (full mandate 35% / 20%)"` ⇒ `"Vote — open phase 3 (full mandate 35% / 20%)"`
- `"Vote: unfreeze the agent"` ⇒ `"Vote — lift the agent freeze"`

Do NOT touch: CLI/README strings, main() console prints, exception texts, RpcError messages (`"rpc unreachable: %s"`, `"no contract code at %s"` — these reach the live card; rephrase the second: `"no contract code at %s"` ⇒ `"no contract bytecode found at %s"`; keep `"rpc unreachable: %s"` as is — it is prefixed diagnostics).

- [ ] **Step 3: Run the full suite**

Run: `python3 -m unittest tests.test_server -v` → 46/46 PASS. Also `python3 -m py_compile server.py` → silent.

- [ ] **Step 4: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "copy: rewrite backend-visible texts (theses, log, guard wording)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Whole-site verification in the browser

**Files:** none (verification only; fixes loop back into the file they belong to).

- [ ] **Step 1:** Restart the dev server (preview tools), open `/` — strip shows `SIMULATED DATA / LOCAL NODE / CONCEPT V0.1`, hero shows the new slogan, zero console errors.
- [ ] **Step 2:** Advance ~10 epochs via `POST /api/control {"action":"advance"}`; open `/console.html` — check: track badges (`thesis under seal`, `keccak checked`), guard card (`limits in phase 2…`, new check names), holders foot, treasury labels, governance foot, node journal shows the new log wording; a voided epoch renders `epoch voided: largest … > …`.
- [ ] **Step 3:** `git diff --word-diff main -- index.html console.html front.js app.js server.py` reviewed once end-to-end against the spec's acceptance criterion (all statements preserved, none added, no verbatim survivors outside protected tokens).
- [ ] **Step 4:** Screenshots of landing + console to the user. No commit (nothing changed) unless fixes were needed.
