# Nostro Backend Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the missing backend node (`server.py` + `nstro` CLI) that powers the existing, untouched frontend of nostro.capital — full economic simulation plus best-effort live chain reading.

**Architecture:** One stdlib-only Python process: ThreadingHTTPServer serves static files and the JSON API; a ticker thread advances an event-driven simulation engine (`Sim` class); an optional poller thread reads Robinhood Chain over JSON-RPC when `nstro.json` switches the node to live mode. Real keccak256 + Solidity-compatible `abi.encode` seal every agent decision.

**Tech Stack:** Python ≥ 3.9, standard library only (http.server, urllib, json, threading, unittest). No pip installs, no venv.

**Spec:** `docs/superpowers/specs/2026-08-29-nostro-backend-design.md` — the API contract there is extracted from `front.js`/`app.js` and is IMMUTABLE.

## Global Constraints

- Python ≥ 3.9, **stdlib only** — no third-party imports anywhere, including tests.
- Frontend files (`index.html`, `console.html`, `front.css`, `front.js`, `app.css`, `app.js`, `favicon.svg`, `brand-banner.jpg`) must remain byte-identical. Never edit them.
- `server.py` is the single backend file; `nstro` is the single CLI file; tests live in `tests/test_server.py`.
- Default port **8000**; entry point is exactly `python3 server.py` (the frontend's offline banner promises this).
- All strings that can reach the UI (log messages, guard check names/details, thesis texts, cancel reasons) are **English**. README is Russian.
- Sim time unit: seconds. One epoch = 86400 sim-seconds. `speed` = sim-seconds per real second (default 1440.0 → 60 s per epoch).
- Money unit for the sim: USDG floats. Weights: integer basis points, sum exactly 10000.
- Chain constants: chain id 4663 (0x1237), default RPC `https://rpc.mainnet.chain.robinhood.com` (verified working 2026-08-29), fee vault `0xB2FC6481A65BACc91277a3488dcc7f6b1C210813` (hardcoded in app.js).
- Every commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Run tests from the repo root: `python3 -m unittest tests.test_server -v` (add `-k <pattern>` to filter).

## File Structure

- `server.py` — everything, in labeled sections top-to-bottom: `# ==== crypto ====` (keccak256, abi_encode_commit), `# ==== simulation ====` (class Sim), `# ==== live chain ====` (rpc client, live snapshot builder, poller), `# ==== http ====` (handler, ticker thread, main). Import-safe: `if __name__ == "__main__": main()`.
- `nstro` — executable CLI (connect / sim / status), writes `nstro.json` next to itself.
- `tests/test_server.py` — all tests; imports server via `sys.path.insert`.
- `README.md` — Russian; quick start, controls, CLI, tests.
- `.claude/launch.json` — dev-server config for browser verification (Task 9).

---

### Task 1: keccak256 (pure Python)

**Files:**
- Create: `server.py` (module docstring, imports, `# ==== crypto ====` section)
- Create: `tests/test_server.py`

**Interfaces:**
- Produces: `keccak256(data: bytes) -> bytes` — 32-byte digest, original Keccak padding (0x01), NOT NIST SHA3.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_server.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server


class TestKeccak(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(
            server.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")

    def test_abc(self):
        self.assertEqual(
            server.keccak256(b"abc").hex(),
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")

    def test_fox(self):
        self.assertEqual(
            server.keccak256(b"The quick brown fox jumps over the lazy dog").hex(),
            "4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15")

    def test_erc20_selectors(self):
        # first 4 bytes of keccak256(signature) — canonical Ethereum selectors,
        # several of them are hardcoded in app.js and must match
        for sig, sel in [
            ("transfer(address,uint256)", "a9059cbb"),
            ("balanceOf(address)", "70a08231"),
            ("approve(address,uint256)", "095ea7b3"),
            ("allowance(address,address)", "dd62ed3e"),
            ("claim(uint256,uint256,bytes32[])", "ae0b51df"),
        ]:
            self.assertEqual(server.keccak256(sig.encode())[:4].hex(), sel, sig)

    def test_transfer_event_topic(self):
        self.assertEqual(
            server.keccak256(b"Transfer(address,address,uint256)").hex(),
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")

    def test_multiblock_sanity(self):
        # inputs straddling the 136-byte rate boundary: all distinct, all 32 bytes,
        # deterministic (correctness of multi-block absorb is backed by the padding
        # rule + single-block vectors above)
        outs = [server.keccak256(b"x" * n) for n in (135, 136, 137, 300)]
        self.assertEqual(len({o for o in outs}), 4)
        for o in outs:
            self.assertEqual(len(o), 32)
        self.assertEqual(server.keccak256(b"x" * 300), server.keccak256(b"x" * 300))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'server'` (or AttributeError once the file exists).

- [ ] **Step 3: Implement keccak256 in server.py**

Create `server.py`:

```python
#!/usr/bin/env python3
"""Nostro node — backend for the nostro.capital frontend.

Serves the static site + JSON API, runs the full economic simulation,
and (in live mode) reads Robinhood Chain over JSON-RPC.
Stdlib only. Run: python3 server.py
"""
import json
import os
import re
import sys
import math
import time
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from random import Random

# ==== crypto ====================================================
# keccak256 (original Keccak, 0x01 padding) — NOT hashlib.sha3_256,
# which is the NIST variant with 0x06 padding and different digests.

_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]
_M64 = (1 << 64) - 1


def _rol64(v, n):
    return ((v << n) | (v >> (64 - n))) & _M64


def _keccak_f(a):
    for rc in _KECCAK_RC:
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                a[x][y] ^= d[x]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rol64(a[x][y], _KECCAK_ROT[x][y])
        for x in range(5):
            for y in range(5):
                a[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y])
        a[0][0] ^= rc


def keccak256(data):
    rate = 136
    a = [[0] * 5 for _ in range(5)]
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate:
        padded.append(0x00)
    padded[-1] ^= 0x80
    for off in range(0, len(padded), rate):
        for i in range(rate // 8):
            lane = int.from_bytes(padded[off + 8 * i:off + 8 * i + 8], "little")
            a[i % 5][i // 5] ^= lane
        _keccak_f(a)
    out = b""
    for i in range(4):
        out += a[i % 5][i // 5].to_bytes(8, "little")
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all TestKeccak tests PASS. If a digest mismatches, the bug is almost always in lane ordering (`a[i % 5][i // 5]`, little-endian lanes) or the rotation table orientation — do not "fix" by changing the test vectors.

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: pure-python keccak256 with canonical test vectors

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: abi.encode + commit hash

**Files:**
- Modify: `server.py` (append to `# ==== crypto ====` section)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: `keccak256(data: bytes) -> bytes` (Task 1).
- Produces:
  - `abi_encode_commit(epoch: int, weights_bps: list[int], thesis: str, nonce32: bytes) -> bytes` — Solidity `abi.encode(uint256, uint256[], string, bytes32)`.
  - `commit_hash(epoch, weights_bps, thesis, nonce32) -> str` — `"0x" + 64 hex`.
  - `make_nonce(rng: Random | None = None) -> bytes` — 32 bytes.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
class TestAbiEncode(unittest.TestCase):
    def test_static_only(self):
        # abi.encode(uint256 1, uint256[] [], string "", bytes32 0x00..00)
        # head: value, arr offset 0x80, str offset 0xa0, bytes32; tails: two zero lengths
        out = server.abi_encode_commit(1, [], "", b"\x00" * 32)
        expect = (
            "0000000000000000000000000000000000000000000000000000000000000001"
            "0000000000000000000000000000000000000000000000000000000000000080"
            "00000000000000000000000000000000000000000000000000000000000000a0"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000"
        )
        self.assertEqual(out.hex(), expect)

    def test_full(self):
        # abi.encode(uint256 2, uint256[] [3500, 6500], string "hi", bytes32 0xaa..aa)
        # 3500 = 0xdac, 6500 = 0x1964, str offset = 0x80 + 32 + 2*32 = 0xe0
        out = server.abi_encode_commit(2, [3500, 6500], "hi", b"\xaa" * 32)
        expect = (
            "0000000000000000000000000000000000000000000000000000000000000002"
            "0000000000000000000000000000000000000000000000000000000000000080"
            "00000000000000000000000000000000000000000000000000000000000000e0"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            "0000000000000000000000000000000000000000000000000000000000000002"
            "0000000000000000000000000000000000000000000000000000000000000dac"
            "0000000000000000000000000000000000000000000000000000000000001964"
            "0000000000000000000000000000000000000000000000000000000000000002"
            "6869000000000000000000000000000000000000000000000000000000000000"
        )
        self.assertEqual(out.hex(), expect)

    def test_commit_hash_roundtrip(self):
        nonce = server.make_nonce()
        self.assertEqual(len(nonce), 32)
        h = server.commit_hash(7, [2000, 8000], "cash up", nonce)
        self.assertTrue(h.startswith("0x") and len(h) == 66)
        self.assertEqual(h, server.commit_hash(7, [2000, 8000], "cash up", nonce))
        self.assertNotEqual(h, server.commit_hash(7, [2000, 8000], "cash up!", nonce))
        self.assertNotEqual(h, server.commit_hash(8, [2000, 8000], "cash up", nonce))

    def test_deterministic_nonce(self):
        a = server.make_nonce(server.Random(1))
        b = server.make_nonce(server.Random(1))
        self.assertEqual(a, b)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestAbiEncode -v`
Expected: AttributeError — `abi_encode_commit` not defined.

- [ ] **Step 3: Implement**

Append to the crypto section of `server.py`:

```python
def abi_encode_commit(epoch, weights_bps, thesis, nonce32):
    """Solidity abi.encode(uint256, uint256[], string, bytes32)."""
    def word(n):
        return int(n).to_bytes(32, "big")
    text = thesis.encode("utf-8")
    arr_tail = word(len(weights_bps)) + b"".join(word(w) for w in weights_bps)
    str_tail = word(len(text)) + text + b"\x00" * ((32 - len(text) % 32) % 32)
    arr_off = 32 * 4
    str_off = arr_off + len(arr_tail)
    return word(epoch) + word(arr_off) + word(str_off) + nonce32 + arr_tail + str_tail


def commit_hash(epoch, weights_bps, thesis, nonce32):
    return "0x" + keccak256(abi_encode_commit(epoch, weights_bps, thesis, nonce32)).hex()


def make_nonce(rng=None):
    if rng is None:
        return os.urandom(32)
    return bytes(rng.randrange(256) for _ in range(32))
```

Note: `Random` is already imported in server.py (`from random import Random`), and the test references it as `server.Random`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: solidity-compatible abi.encode + commit hash

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Sim skeleton — clock, prices, basket, snapshot schema

**Files:**
- Modify: `server.py` (new `# ==== simulation ====` section)
- Modify: `tests/test_server.py`

**Interfaces:**
- Produces (later tasks build on these exact names):
  - `WHITELIST: list[str]` = `["AAPL","TSLA","NVDA","MSFT","AMZN","GOOGL","META","HOOD","COIN","PLTR"]`, `CASH = "USDG"`, `EPOCH_SIM = 86400.0`, `TOKEN_PRICE = 0.001`
  - `class Sim` with: `__init__(self, seed=None)`, `advance(self, dt_sim: float)`, `force_close(self)`, `set_speed(self, sim_per_real: float)`, `snapshot(self) -> dict`
  - Attributes read by later tasks: `rng: Random`, `t: float`, `epoch: int` (starts at 1), `epoch_start: float`, `paused: bool`, `speed: float`, `phase: int`, `prices: dict[str, float]`, `positions: dict[str, float]` (asset units; `positions["USDG"]` is USDG cash), `units: float`, `uv: list[float]` (unit values per closed epoch), `shadow_uv: list[float]`, `epochs: list[dict]`, `track: list[dict]`, `gov_queue: list[dict]`, `log_items: list[dict]`, `frozen: bool`
  - Internal hook for later tasks: `_on_close(self)` — called once per epoch close, after uv append, before `epoch += 1`; Task 3 leaves it minimal.
  - `nav(self) -> float`, `unit_value(self) -> float`, `weights_bps(self) -> dict[str, int]` (derived from positions×prices, sums to exactly 10000, USDG included)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
SIM_TOP_KEYS = {
    "mode", "public", "config", "epoch", "t", "phase", "paused", "speed",
    "epoch_progress", "nav", "unit_value", "unit_values", "shadow_uv",
    "weights", "prices", "pending_quote", "volume_epoch", "epochs", "track",
    "holders", "treasury", "guard", "gov_queue", "log",
}


class TestSimSkeleton(unittest.TestCase):
    def setUp(self):
        self.sim = server.Sim(seed=42)

    def test_snapshot_schema(self):
        s = self.sim.snapshot()
        self.assertEqual(SIM_TOP_KEYS - set(s), set())
        self.assertEqual(s["mode"], "sim")
        self.assertIs(s["public"], False)
        self.assertIn("rpc_url", s["config"])
        self.assertEqual(s["epoch"], 1)
        self.assertEqual(s["phase"], 0)
        json.dumps(s)  # must be JSON-serializable

    def test_weights_sum_10000(self):
        for _ in range(5):
            self.sim.advance(20000)
            self.assertEqual(sum(self.sim.weights_bps().values()), 10000)

    def test_epoch_rollover(self):
        self.sim.advance(86400 * 2.5)
        self.assertEqual(self.sim.epoch, 3)
        self.assertEqual(len(self.sim.uv), 2)
        prog = self.sim.snapshot()["epoch_progress"]
        self.assertGreater(prog, 0.45)
        self.assertLess(prog, 0.55)

    def test_force_close(self):
        self.sim.advance(100)
        self.sim.force_close()
        self.assertEqual(self.sim.epoch, 2)

    def test_pause_blocks_time(self):
        self.sim.paused = True
        t0 = self.sim.t
        self.sim.advance(5000)
        self.assertEqual(self.sim.t, t0)

    def test_phase_progression(self):
        for _ in range(2):
            self.sim.force_close()
        self.assertEqual(self.sim.phase, 1)   # epochs 1-2 passive, 3+ shadow
        for _ in range(6):
            self.sim.force_close()
        self.assertEqual(self.sim.phase, 2)   # epoch 9+ reduced limits

    def test_prices_move_and_stay_positive(self):
        p0 = dict(self.sim.prices)
        self.sim.advance(86400)
        moved = sum(1 for a in server.WHITELIST if self.sim.prices[a] != p0[a])
        self.assertGreater(moved, 5)
        for a, p in self.sim.prices.items():
            self.assertGreater(p, 0)

    def test_deterministic_with_seed(self):
        a, b = server.Sim(seed=1), server.Sim(seed=1)
        a.advance(50000), b.advance(50000)
        self.assertEqual(a.prices, b.prices)
```

Add `import json` to the top of the test file.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestSimSkeleton -v`
Expected: AttributeError — `Sim` not defined.

- [ ] **Step 3: Implement the Sim skeleton**

Append a `# ==== simulation ====` section to `server.py`:

```python
# ==== simulation ================================================

WHITELIST = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "HOOD", "COIN", "PLTR"]
CASH = "USDG"
EPOCH_SIM = 86400.0
TOKEN_PRICE = 0.001            # USDG per $NSTRO, for volume accounting
START_PRICES = {"AAPL": 235.0, "TSLA": 340.0, "NVDA": 185.0, "MSFT": 520.0,
                "AMZN": 230.0, "GOOGL": 200.0, "META": 780.0, "HOOD": 95.0,
                "COIN": 310.0, "PLTR": 155.0}
START_NAV = 250_000.0
DEFAULT_RPC = "https://rpc.mainnet.chain.robinhood.com"


class Sim:
    def __init__(self, seed=None):
        self.rng = Random(seed)
        self.t = 0.0
        self.epoch = 1
        self.epoch_start = 0.0
        self.paused = False
        self.speed = 1440.0                      # sim sec per real sec (epoch = 60s)
        self.phase = 0
        self.frozen = False
        self.prices = dict(START_PRICES)
        self._drift = {a: self.rng.uniform(-0.001, 0.002) for a in WHITELIST}
        self._sigma = {a: self.rng.uniform(0.015, 0.035) for a in WHITELIST}
        # initial basket: 8% each stock, 20% cash
        self.positions = {a: START_NAV * 0.08 / START_PRICES[a] for a in WHITELIST}
        self.positions[CASH] = START_NAV * 0.20
        self.units = START_NAV                   # unit_value starts at 1.0
        self.uv = []
        self.shadow_uv = []
        self.epochs = []
        self.track = []
        self.gov_queue = []
        self.log_items = []
        self.log("node online — passive index, phase 0")

    # ---- helpers ----
    def log(self, msg):
        self.log_items.append({"t": self.t, "msg": msg})
        del self.log_items[:-200]

    def nav(self):
        return sum(self.positions[a] * self.price_of(a) for a in self.positions)

    def price_of(self, asset):
        return 1.0 if asset == CASH else self.prices[asset]

    def unit_value(self):
        return self.nav() / self.units

    def weights_bps(self):
        nav = self.nav()
        out, acc, assets = {}, 0, list(self.positions)
        for a in assets[:-1]:
            w = round(self.positions[a] * self.price_of(a) / nav * 10000)
            out[a], acc = w, acc + w
        out[assets[-1]] = 10000 - acc            # force exact sum
        return out

    def set_speed(self, sim_per_real):
        self.speed = max(24.0, min(sim_per_real, 86400.0))

    # ---- time ----
    def advance(self, dt_sim):
        if self.paused:
            return
        remaining = dt_sim
        while remaining > 1e-9:
            boundary = self.epoch_start + EPOCH_SIM
            step = min(remaining, boundary - self.t)
            self._integrate(step)
            remaining -= step
            if self.t >= boundary - 1e-9:
                self._close_epoch()

    def force_close(self):
        self._close_epoch()

    def _integrate(self, dt):
        self.t += dt
        dt_days = dt / EPOCH_SIM
        for a in WHITELIST:
            g = self.rng.gauss(0.0, 1.0)
            mu, sg = self._drift[a], self._sigma[a]
            self.prices[a] *= math.exp((mu - 0.5 * sg * sg) * dt_days
                                       + sg * math.sqrt(dt_days) * g)

    def _close_epoch(self):
        uv_now = self.unit_value()
        prev = self.uv[-1] if self.uv else 1.0
        self.uv.append(uv_now)
        del self.uv[:-400]
        self.epochs.append({
            "n": self.epoch, "dnav_pct": (uv_now / prev - 1.0) * 100.0,
            "checks": [], "cancelled": None, "executed": False,
            "turnover_bps": 0, "exec": None, "phase": self.phase,
        })
        del self.epochs[:-200]
        self._on_close()
        self.epoch += 1
        self.epoch_start = self.t     # force_close may fire mid-epoch
        if self.phase < 1 and self.epoch >= 3:
            self.phase = 1
            self.log("phase 1 — shadow mode: sealed calls, no execution")
        if self.phase < 2 and self.epoch >= 9:
            self.phase = 2
            self.log("phase 2 — execution live at reduced limits")

    def _on_close(self):
        pass  # extended in later tasks

    # ---- snapshot ----
    def snapshot(self):
        return {
            "mode": "sim", "public": False,
            "config": {"rpc_url": DEFAULT_RPC},
            "epoch": self.epoch, "t": self.t, "phase": self.phase,
            "paused": self.paused, "speed": self.speed,
            "epoch_progress": max(0.0, min(1.0, (self.t - self.epoch_start) / EPOCH_SIM)),
            "nav": self.nav(), "unit_value": self.unit_value(),
            "unit_values": list(self.uv) or [1.0],
            "shadow_uv": list(self.shadow_uv),
            "weights": self.weights_bps(), "prices": dict(self.prices),
            "pending_quote": 0.0, "volume_epoch": 0.0,
            "epochs": list(self.epochs), "track": list(self.track),
            "holders": [], "treasury": {"runway_days": 0.0, "usdg": 0.0,
                                        "epoch_cost": 0.0, "inflow_tax": 0.0,
                                        "inflow_creator": 0.0, "protocol_fund": 0.0,
                                        "hold_mode": False},
            "guard": {"frozen": self.frozen, "freeze_epoch": 0,
                      "limits": {"max_weight_bps": 3500, "turnover_bps": 2000}},
            "gov_queue": list(self.gov_queue), "log": list(self.log_items),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS. `snapshot()["unit_values"]` fallback `[1.0]` matters: front.js reads `s.unit_values[len-1]` patterns and the chart needs ≥2 points to draw, but never crashes on fewer.

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: sim skeleton — event-driven clock, GBM prices, basket, snapshot schema

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Holders, balance×time accrual, sniper bot, trade/claim

**Files:**
- Modify: `server.py` (extend Sim: `__init__`, `_integrate`, `_on_close`, snapshot; new methods)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: Sim skeleton (Task 3), `TOKEN_PRICE`.
- Produces:
  - `Sim.holders: list[dict]` — each `{"id","name","kind","balance","integral","last_share","claimable_value","claimed_value"}`; ids: `"you"` (kind `"user"`), `"sniper"` (kind `"sniper"`), others kind `""`.
  - `Sim.trade(side: str, amount: float) -> None` (side `"buy"`/`"sell"`, amount in $NSTRO)
  - `Sim.claim() -> float` — pays out `you`'s claimable, returns amount
  - `Sim.volume_epoch: float`, `Sim.pending_quote()` -> float, `Sim.pool80_total: float` (cumulative), snapshot fields `volume_epoch`, `pending_quote`, `holders` become real.
  - Epoch tax pipeline inside `_on_close`: `tax = volume_epoch * 0.03`; 80% pool → holder claimables by share; 13/7/1% recorded in `self._tre_*` accumulators for Task 6 (`self._tre_inflow_tax`, `self._tre_inflow_creator`, `self._tre_protocol`); 80% also added to `positions[CASH]` (the basket buy).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
class TestAccrual(unittest.TestCase):
    def setUp(self):
        self.sim = server.Sim(seed=7)

    def full_epochs(self, n):
        for _ in range(n):
            self.sim.advance(server.EPOCH_SIM - (self.sim.t - self.sim.epoch_start))

    def holder(self, hid):
        return next(h for h in self.sim.holders if h["id"] == hid)

    def test_roster(self):
        ids = {h["id"] for h in self.sim.holders}
        self.assertIn("you", ids)
        self.assertIn("sniper", ids)
        self.assertGreaterEqual(len(ids), 7)
        self.assertEqual(self.holder("you")["kind"], "user")
        self.assertEqual(self.holder("sniper")["kind"], "sniper")

    def test_sniper_share_is_dust(self):
        self.full_epochs(3)
        sniper = self.holder("sniper")
        self.assertEqual(sniper["balance"], 0)          # exits after each close
        self.assertLess(sniper["last_share"], 0.005)    # bought 12s before close
        long_term = self.holder("whale")
        self.assertGreater(long_term["last_share"], 0.1)

    def test_trade_and_volume(self):
        you = self.holder("you")
        b0 = you["balance"]
        self.sim.trade("buy", 100_000)
        self.assertEqual(you["balance"], b0 + 100_000)
        self.assertGreaterEqual(self.sim.volume_epoch, 100_000 * server.TOKEN_PRICE)
        self.sim.trade("sell", 10 ** 12)                # clamped to balance
        self.assertEqual(you["balance"], 0)

    def test_claim_conservation(self):
        self.full_epochs(5)
        total_accrued = sum(h["claimable_value"] + h["claimed_value"]
                            for h in self.sim.holders)
        self.assertLessEqual(total_accrued, self.sim.pool80_total + 1e-6)
        you = self.holder("you")
        if you["claimable_value"] > 0:
            nav0 = self.sim.nav()
            paid = self.sim.claim()
            self.assertAlmostEqual(you["claimable_value"], 0.0)
            self.assertAlmostEqual(you["claimed_value"], paid)
            self.assertAlmostEqual(self.sim.nav(), nav0 - paid, places=6)

    def test_snapshot_holder_fields(self):
        self.full_epochs(2)
        h = self.sim.snapshot()["holders"][0]
        for k in ("id", "name", "kind", "balance", "last_share",
                  "claimable_value", "claimed_value"):
            self.assertIn(k, h)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestAccrual -v`
Expected: failures — `Sim` has no `holders`.

- [ ] **Step 3: Implement**

Extend `Sim.__init__` (after `self.log_items`):

```python
        self.holders = [
            {"id": "whale",   "name": "whale.eth",    "kind": "",       "balance": 120_000_000},
            {"id": "meridian","name": "meridian.eth", "kind": "",       "balance": 40_000_000},
            {"id": "w7a3f",   "name": "0x7a3f…c2d1",  "kind": "",       "balance": 25_000_000},
            {"id": "kepler",  "name": "kepler.eth",   "kind": "",       "balance": 18_000_000},
            {"id": "w94bb",   "name": "0x94bb…08aa",  "kind": "",       "balance": 12_000_000},
            {"id": "aurora",  "name": "aurora.eth",   "kind": "",       "balance": 8_000_000},
            {"id": "you",     "name": "you",          "kind": "user",   "balance": 2_000_000},
            {"id": "sniper",  "name": "0xf00d…babe",  "kind": "sniper", "balance": 0},
        ]
        for h in self.holders:
            h.update(integral=0.0, last_share=0.0,
                     claimable_value=0.0, claimed_value=0.0)
        self._supply_integral = 0.0
        self._sniper_fired = False
        self.volume_epoch = 0.0
        self._base_flow = self.rng.uniform(200_000, 400_000)   # USDG volume per epoch
        self.pool80_total = 0.0
        self._tre_inflow_tax = 0.0
        self._tre_inflow_creator = 0.0
        self._tre_protocol = 0.0
```

Extend `advance` — event-driven stepping so the sniper fires exactly at T−12 s. Replace the while-loop body:

```python
        while remaining > 1e-9:
            boundary = self.epoch_start + EPOCH_SIM
            events = [boundary]
            if not self._sniper_fired:
                events.append(boundary - 12.0)
            nxt = min(e for e in events if e > self.t + 1e-9)
            step = min(remaining, nxt - self.t)
            self._integrate(step)
            remaining -= step
            if not self._sniper_fired and self.t >= boundary - 12.0 - 1e-6:
                self._sniper_buy()
            if self.t >= boundary - 1e-9:
                self._close_epoch()
```

Extend `_integrate` (accrual + background volume + bot churn), after the price loop:

```python
        supply = 0.0
        for h in self.holders:
            h["integral"] += h["balance"] * dt
            supply += h["balance"]
        self._supply_integral += supply * dt
        self.volume_epoch += self._base_flow * dt / EPOCH_SIM
        if self.rng.random() < dt / 900.0:      # a bot trade every ~15 sim-min
            bot = self.rng.choice(self.holders[:6])
            delta = bot["balance"] * self.rng.uniform(-0.02, 0.02)
            bot["balance"] = max(0.0, bot["balance"] + delta)
            self.volume_epoch += abs(delta) * TOKEN_PRICE
```

New methods on `Sim`:

```python
    def _sniper_buy(self):
        self._sniper_fired = True
        sniper = self._holder("sniper")
        sniper["balance"] += 800_000
        self.volume_epoch += 800_000 * TOKEN_PRICE
        self.log("sniper bot bought 800k $NSTRO 12s before the close")

    def _holder(self, hid):
        return next(h for h in self.holders if h["id"] == hid)

    def pending_quote(self):
        return self.volume_epoch * 0.03 * 0.80

    def trade(self, side, amount):
        you = self._holder("you")
        amount = float(amount)
        if amount <= 0:
            return
        if side == "buy":
            you["balance"] += amount
        else:
            amount = min(amount, you["balance"])
            you["balance"] -= amount
        self.volume_epoch += amount * TOKEN_PRICE
        self.log("your wallet %s %s $NSTRO" % (
            "bought" if side == "buy" else "sold", format(int(amount), ",")))

    def claim(self):
        you = self._holder("you")
        paid = you["claimable_value"]
        if paid <= 0:
            return 0.0
        you["claimable_value"] = 0.0
        you["claimed_value"] += paid
        scale = max(0.0, 1.0 - paid / self.nav())
        for a in self.positions:
            self.positions[a] *= scale
        self.log("you claimed %.2f USDG" % paid)
        return paid
```

Extend `_on_close` (this task turns the stub into the tax/accrual settlement; Tasks 5–6 append more):

```python
    def _on_close(self):
        tax = self.volume_epoch * 0.03
        pool80 = tax * 0.80
        self._tre_inflow_tax = tax * 0.13
        self._tre_inflow_creator = self.volume_epoch * 0.01
        self._tre_protocol += tax * 0.07
        if self._supply_integral > 0:
            for h in self.holders:
                share = h["integral"] / self._supply_integral
                h["last_share"] = share
                h["claimable_value"] += share * pool80
        self.pool80_total += pool80
        self.positions[CASH] += pool80          # the basket buy (as cash inflow)
        sniper = self._holder("sniper")
        if sniper["balance"] > 0:
            sniper["balance"] = 0
            self.log("sniper exited right after the close — share ~0 (balance × time)")
        for h in self.holders:
            h["integral"] = 0.0
        self._supply_integral = 0.0
        self.volume_epoch = 0.0
        self._sniper_fired = False
```

Update `snapshot()`: replace `"pending_quote": 0.0, "volume_epoch": 0.0` with real values and holders:

```python
            "pending_quote": self.pending_quote(),
            "volume_epoch": self.volume_epoch,
            "holders": [{k: h[k] for k in ("id", "name", "kind", "balance",
                                           "last_share", "claimable_value",
                                           "claimed_value")}
                        for h in self.holders],
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS (including earlier suites — schema test still green because holder dicts are JSON-safe).

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: holders with balance-time accrual, sniper bot, trade/claim, tax split

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Agent, sealed commits, MandateGuard, batch execution, shadow NAV

**Files:**
- Modify: `server.py` (extend Sim)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: `commit_hash`, `make_nonce` (Task 2); Sim internals (Tasks 3–4).
- Produces:
  - `PHASE_LIMITS: dict[int, tuple[int, int]]` = `{0: (3500, 2000), 1: (3500, 2000), 2: (2000, 700), 3: (3500, 2000)}` — (max_weight_bps, turnover_bps).
  - `Sim.track` entries: `{"epoch","hash","revealed","verified","thesis","committed_at","revealed_at"}` (`thesis` is `None` until reveal).
  - `Sim.epochs[i]["checks"]`: list of 8 `{"name","ok","detail"}`; `"cancelled"`: reason str or None; `"executed"`: bool; `"turnover_bps"`: int; `"exec"`: `{"trades":[{"asset","value","impact_bps"}], "max_impact_bps", "cost}` or None.
  - `Sim._force_bad_next: bool` — test/demo hook: next proposal violates the weight cap.
  - Guard check names, exactly: `"whitelist"`, `"max weight"`, `"min position"`, `"turnover"`, `"single rebalance"`, `"cash band"`, `"weights sum"`, `"agent status"`.
  - `Sim.last_rebalance_epoch: int`, `Sim.hold_mode: bool` (False until Task 6).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
class TestAgent(unittest.TestCase):
    def setUp(self):
        self.sim = server.Sim(seed=11)

    def to_epoch(self, n):
        while self.sim.epoch < n:
            self.sim.force_close()

    def test_no_commits_in_phase0(self):
        self.assertEqual(self.sim.track, [])
        self.sim.force_close()
        self.assertEqual(self.sim.track, [])          # still phase 0 after epoch 1

    def test_commit_seal_and_reveal(self):
        self.to_epoch(4)
        sealed = [r for r in self.sim.track if not r["revealed"]]
        self.assertEqual(len(sealed), 1)              # exactly one pending decision
        rec = sealed[0]
        self.assertEqual(rec["epoch"], self.sim.epoch)
        self.assertIsNone(rec["thesis"])
        self.assertRegex(rec["hash"], r"^0x[0-9a-f]{64}$")
        self.sim.force_close()
        rec = next(r for r in self.sim.track if r["epoch"] == rec["epoch"])
        self.assertTrue(rec["revealed"])
        self.assertTrue(rec["verified"])              # keccak recomputed and matched
        self.assertTrue(rec["thesis"])

    def test_guard_checks_present_and_named(self):
        self.to_epoch(5)
        last = next(e for e in reversed(self.sim.epochs) if e["checks"])
        self.assertEqual(
            [c["name"] for c in last["checks"]],
            ["whitelist", "max weight", "min position", "turnover",
             "single rebalance", "cash band", "weights sum", "agent status"])

    def test_bad_vector_cancels_and_freezes_basket(self):
        self.to_epoch(10)                              # phase 2, execution on
        w_before = self.sim.weights_bps()
        self.sim._force_bad_next = True
        self.sim.force_close()
        rec = self.sim.epochs[-1]
        self.assertIsNotNone(rec["cancelled"])
        self.assertFalse(rec["executed"])
        bad = [c for c in rec["checks"] if not c["ok"]]
        self.assertTrue(bad)
        w_after = self.sim.weights_bps()
        for a in w_before:                             # basket did not move
            self.assertLessEqual(abs(w_after[a] - w_before[a]), 60)  # only price drift

    def test_execution_respects_turnover(self):
        self.to_epoch(16)
        executed = [e for e in self.sim.epochs if e["executed"]]
        self.assertTrue(executed)
        for e in executed:
            limit = server.PHASE_LIMITS[e["phase"]][1]
            self.assertLessEqual(e["turnover_bps"], limit)
            self.assertTrue(e["exec"]["trades"])
            self.assertGreater(e["exec"]["cost"], 0)

    def test_shadow_series_grows_from_phase1(self):
        self.to_epoch(12)
        self.assertGreater(len(self.sim.shadow_uv), 3)
        self.assertLessEqual(len(self.sim.shadow_uv), len(self.sim.uv))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestAgent -v`
Expected: failures (empty track, missing PHASE_LIMITS).

- [ ] **Step 3: Implement**

Module constant + `Sim.__init__` additions:

```python
PHASE_LIMITS = {0: (3500, 2000), 1: (3500, 2000), 2: (2000, 700), 3: (3500, 2000)}

THESIS_LEADS = [
    "Momentum in {a} and {b} remains intact; adding on strength.",
    "Trimming {a} after the run, rotating into {b}.",
    "Earnings setup favors {a}; keeping {b} at benchmark weight.",
    "Volatility regime is rising; concentration in {a} comes down.",
    "Flows into tokenized {a} keep improving; {b} stays a funding source.",
]
THESIS_TAILS = [
    "Cash held at {c}% as dry powder.",
    "Raising cash to {c}% ahead of the macro print.",
    "Cash at {c}%; turnover kept well inside the mandate.",
]
```

```python
        # __init__ additions (Task 5)
        self._pending_commit = None      # {"epoch","weights","thesis","nonce","hash","committed_at"}
        self._force_bad_next = False
        self._bad_cadence = self.rng.randrange(8, 13)
        self.last_rebalance_epoch = 0
        self.hold_mode = False
        self._shadow_positions = None    # dict like self.positions, set at phase 1 entry
```

Extend `_on_close` — append AFTER the Task 4 settlement code:

```python
        self._reveal_pending()
        if self.phase >= 1 or self.epoch >= 2:   # first proposal at close of epoch 2
            self._agent_cycle()
        self._update_shadow()
```

New Sim methods (full implementations):

```python
    def _reveal_pending(self):
        if not self._pending_commit or self._pending_commit["epoch"] != self.epoch:
            return
        p = self._pending_commit
        rec = next((r for r in self.track if r["epoch"] == p["epoch"]), None)
        if rec:
            rec["revealed"] = True
            rec["verified"] = commit_hash(p["epoch"], p["weights_list"],
                                          p["thesis"], p["nonce"]) == rec["hash"]
            rec["thesis"] = p["thesis"]
            rec["revealed_at"] = self.t
            self.log("epoch %d thesis revealed — keccak %s" %
                     (p["epoch"], "verified" if rec["verified"] else "MISMATCH"))
        self._pending_commit = None

    def _propose_weights(self):
        cur = self.weights_bps()
        max_w, max_turn = PHASE_LIMITS[self.phase]
        target = dict(cur)
        if self._force_bad_next or (self.epoch % self._bad_cadence == 0
                                    and self.phase >= 1):
            self._force_bad_next = False
            hot = self.rng.choice(WHITELIST)
            target[hot] = max_w + self.rng.randrange(500, 1500)   # deliberate violation
            self._rebalance_to_sum(target)
            return target
        if self.hold_mode and self.epoch - self.last_rebalance_epoch < 3:
            return dict(cur)                                       # keep-current
        budget = max_turn - 100                                    # stay inside limit
        for _ in range(self.rng.randrange(2, 5)):
            a = self.rng.choice(WHITELIST + [CASH])
            delta = self.rng.randrange(50, max(60, budget // 3))
            src = max(target, key=lambda s: target[s] if s != a else -1)
            delta = min(delta, target[src] - (0 if src == CASH else 500))
            if delta <= 0:
                continue
            target[a] = target.get(a, 0) + delta
            target[src] -= delta
        for a in WHITELIST:                                        # enforce caps/floors
            target[a] = min(target.get(a, 0), max_w)
            if 0 < target[a] < 500:
                target[CASH] += target[a]
                target[a] = 0
        self._rebalance_to_sum(target)
        return target

    def _rebalance_to_sum(self, target):
        diff = 10000 - sum(target.values())
        target[CASH] = max(0, target.get(CASH, 0) + diff)
        drift = 10000 - sum(target.values())
        if drift:                                    # cash clamped at 0 — adjust largest
            big = max((a for a in target if a != CASH), key=lambda a: target[a])
            target[big] += drift

    def _make_thesis(self, target):
        stocks = sorted((a for a in WHITELIST if target.get(a)),
                        key=lambda a: -target[a])
        if not stocks:
            return "Basket parked in USDG; awaiting mandate."
        a, b = stocks[0], stocks[1 if len(stocks) > 1 else 0]
        lead = self.rng.choice(THESIS_LEADS).format(a=a, b=b)
        tail = self.rng.choice(THESIS_TAILS).format(c=round(target.get(CASH, 0) / 100))
        return lead + " " + tail

    def _guard_checks(self, target):
        cur = self.weights_bps()
        max_w, max_turn = PHASE_LIMITS[self.phase]
        turnover = sum(abs(target.get(a, 0) - cur.get(a, 0))
                       for a in set(cur) | set(target)) // 2
        checks = []
        bad_assets = [a for a in target if a != CASH and a not in WHITELIST]
        checks.append({"name": "whitelist", "ok": not bad_assets,
                       "detail": ("%d assets checked" % len(target)) if not bad_assets
                       else "%s not whitelisted" % bad_assets[0]})
        top = max((a for a in target if a != CASH), key=lambda a: target[a])
        checks.append({"name": "max weight", "ok": target[top] <= max_w,
                       "detail": "top %s %.1f%% %s %.1f%%" % (
                           top, target[top] / 100,
                           "≤" if target[top] <= max_w else ">", max_w / 100)})
        small = [a for a in target if a != CASH and 0 < target[a] < 500]
        checks.append({"name": "min position", "ok": not small,
                       "detail": "all positions ≥ 5% or zero" if not small
                       else "%s at %.1f%% < 5%%" % (small[0], target[small[0]] / 100)})
        checks.append({"name": "turnover", "ok": turnover <= max_turn,
                       "detail": "%.1f%% %s %.1f%% NAV" % (
                           turnover / 100, "≤" if turnover <= max_turn else ">",
                           max_turn / 100)})
        allowed = (not self.hold_mode) or (self.epoch - self.last_rebalance_epoch >= 3) \
                  or turnover == 0
        checks.append({"name": "single rebalance", "ok": allowed,
                       "detail": "1 of 1 this epoch" if not self.hold_mode
                       else "hold mode: one rebalance per 3 epochs"})
        cash = target.get(CASH, 0)
        checks.append({"name": "cash band", "ok": 0 <= cash <= 10000,
                       "detail": "cash %.1f%% within 0–100%%" % (cash / 100)})
        total = sum(target.values())
        checks.append({"name": "weights sum", "ok": total == 10000,
                       "detail": "sum %.2f%%" % (total / 100)})
        checks.append({"name": "agent status", "ok": not self.frozen,
                       "detail": "agent frozen — breaker active" if self.frozen
                       else "agent active"})
        return checks, turnover

    def _agent_cycle(self):
        rec = self.epochs[-1]                        # record of the epoch just closed
        target = self._propose_weights()
        weights_list = [target.get(a, 0) for a in WHITELIST] + [target.get(CASH, 0)]
        thesis = self._make_thesis(target)
        nonce = make_nonce(self.rng)
        next_epoch = self.epoch + 1
        h = commit_hash(next_epoch, weights_list, thesis, nonce)
        self.track.append({"epoch": next_epoch, "hash": h, "revealed": False,
                           "verified": False, "thesis": None,
                           "committed_at": self.t, "revealed_at": None})
        del self.track[:-40]
        self._pending_commit = {"epoch": next_epoch, "weights_list": weights_list,
                                "thesis": thesis, "nonce": nonce}
        self.log("epoch %d decision sealed: %s…" % (next_epoch, h[:18]))
        checks, turnover = self._guard_checks(target)
        rec["checks"] = checks
        rec["turnover_bps"] = turnover
        failed = next((c for c in checks if not c["ok"]), None)
        if failed:
            rec["cancelled"] = failed["detail"]
            self.log("epoch %d CANCELLED by MandateGuard: %s" %
                     (next_epoch, failed["detail"]))
            return
        self._accepted_target = target
        if self.phase >= 2 and turnover > 0:
            rec["exec"] = self._execute(target, turnover)
            rec["executed"] = True
            self.last_rebalance_epoch = self.epoch

    def _execute(self, target, turnover_bps):
        nav = self.nav()
        trades, max_imp, cost = [], 0, 0.0
        for a in sorted(set(self.weights_bps()) | set(target)):
            dv = nav * (target.get(a, 0) - self.weights_bps().get(a, 0)) / 10000.0
            if abs(dv) < nav * 0.001 or a == CASH:
                continue
            impact = min(35, int(abs(dv) / nav * 10000 * 0.08) + self.rng.randrange(1, 6))
            trades.append({"asset": a, "value": dv, "impact_bps": impact})
            max_imp = max(max_imp, impact)
            cost += abs(dv) * impact / 10000.0
        nav_after = nav - cost
        for a in self.positions:
            tgt_v = nav_after * target.get(a, 0) / 10000.0
            self.positions[a] = tgt_v / self.price_of(a)
        self.log("batch executed: %d trades, max impact %d bps, cost %.2f USDG"
                 % (len(trades), max_imp, cost))
        return {"trades": trades, "max_impact_bps": max_imp, "cost": cost}

    def _update_shadow(self):
        if self.phase < 1:
            return
        if self._shadow_positions is None:
            self._shadow_positions = dict(self.positions)
        tgt = getattr(self, "_accepted_target", None)
        snav = sum(self._shadow_positions[a] * self.price_of(a)
                   for a in self._shadow_positions)
        if tgt:
            for a in set(self._shadow_positions) | set(tgt):
                self._shadow_positions[a] = snav * tgt.get(a, 0) / 10000.0 \
                                            / self.price_of(a)
        self.shadow_uv.append(snav / self.units)
        del self.shadow_uv[:-400]
        self._accepted_target = None
```

Ordering note (matches the frontend's assumption "the vector for epoch N is submitted at the close of N−1"): inside `_on_close` the epoch record for N already exists (created in `_close_epoch` before `_on_close` runs), `_reveal_pending` opens the commit made for N, then `_agent_cycle` seals the commit for N+1 and attaches its guard checks to record N.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS. Flakiness guard: everything is seeded via `Random(seed)`; if a threshold test is marginal, tune the seed constant in the TEST, never loosen the invariant.

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: agent proposals, sealed keccak commits, MandateGuard, batch exec, shadow NAV

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Treasury, breaker, governance, hold mode

**Files:**
- Modify: `server.py` (extend Sim)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: Tasks 3–5 internals (`_tre_*` accumulators, `frozen`, `hold_mode`, `gov_queue`).
- Produces:
  - `Sim.gov(action: str) -> bool` — `"phase3"` (only when phase == 2, not already queued), `"unfreeze"` (only when frozen, not queued); queues `{"label", "action", "eta"}` with `eta = epoch + 3`; returns False otherwise.
  - `Sim.treasury_usdg: float`, `Sim.epoch_cost: float`, `Sim.freeze_epoch: int`
  - snapshot `treasury` and `guard` blocks become real:
    `treasury = {"runway_days","usdg","epoch_cost","inflow_tax","inflow_creator","protocol_fund","hold_mode"}`,
    `guard = {"frozen","freeze_epoch","limits":{"max_weight_bps","turnover_bps"}}` with limits from `PHASE_LIMITS[phase]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
class TestTreasuryGov(unittest.TestCase):
    def setUp(self):
        self.sim = server.Sim(seed=5)

    def to_epoch(self, n):
        # advance real sim time (not force_close) so trading volume accrues
        # and the treasury actually receives tax inflows
        while self.sim.epoch < n:
            self.sim.advance(server.EPOCH_SIM)

    def test_treasury_snapshot(self):
        self.to_epoch(4)
        t = self.sim.snapshot()["treasury"]
        self.assertGreater(t["usdg"], 0)
        self.assertGreater(t["epoch_cost"], 0)
        self.assertGreater(t["inflow_tax"], 0)
        self.assertAlmostEqual(t["runway_days"], t["usdg"] / t["epoch_cost"], places=3)

    def test_guard_limits_follow_phase(self):
        self.to_epoch(10)
        g = self.sim.snapshot()["guard"]
        self.assertEqual(g["limits"], {"max_weight_bps": 2000, "turnover_bps": 700})

    def test_breaker_freezes_and_vote_unfreezes(self):
        self.to_epoch(10)
        for a in server.WHITELIST:            # market crash: −40% across the board
            self.sim.prices[a] *= 0.60
        self.sim.force_close()
        self.assertTrue(self.sim.frozen)
        w = self.sim.weights_bps()
        self.assertGreater(w["USDG"], 9500)   # basket parked in cash
        self.assertTrue(self.sim.gov("unfreeze"))
        self.assertFalse(self.sim.gov("unfreeze"))          # no duplicate votes
        eta = self.sim.gov_queue[0]["eta"]
        self.assertEqual(eta, self.sim.epoch + 3)
        self.to_epoch(eta)
        self.assertFalse(self.sim.frozen)
        self.assertEqual(self.sim.gov_queue, [])

    def test_phase3_vote(self):
        self.assertFalse(self.sim.gov("phase3"))            # not in phase 2 yet
        self.to_epoch(10)
        self.assertTrue(self.sim.gov("phase3"))
        self.to_epoch(self.sim.gov_queue[0]["eta"])
        self.assertEqual(self.sim.phase, 3)

    def test_frozen_agent_cancels_epochs(self):
        self.to_epoch(10)
        for a in server.WHITELIST:
            self.sim.prices[a] *= 0.60
        self.sim.force_close()
        self.sim.force_close()
        rec = self.sim.epochs[-1]
        self.assertIsNotNone(rec["cancelled"])
        status = next(c for c in rec["checks"] if c["name"] == "agent status")
        self.assertFalse(status["ok"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestTreasuryGov -v`
Expected: failures — no `gov`, treasury zeros.

- [ ] **Step 3: Implement**

`Sim.__init__` additions:

```python
        self.treasury_usdg = 2400.0
        self.epoch_cost = 120.0
        self.protocol_fund = 0.0
        self.freeze_epoch = 0
```

Append to `_on_close` (after `_update_shadow()`):

```python
        self.epoch_cost = 120.0 * self.rng.uniform(0.85, 1.20)
        self.treasury_usdg += self._tre_inflow_tax + self._tre_inflow_creator
        self.treasury_usdg = max(0.0, self.treasury_usdg - self.epoch_cost)
        was_hold = self.hold_mode
        self.hold_mode = (self.treasury_usdg / self.epoch_cost) < 14.0
        if self.hold_mode and not was_hold:
            self.log("runway under 14 days — hold mode: one rebalance per 3 epochs")
        if not self.frozen and len(self.uv) >= 2:
            peak = max(self.uv[-7:])
            if self.uv[-1] <= 0.75 * peak:
                self.frozen = True
                self.freeze_epoch = self.epoch
                nav = self.nav()
                self.positions = {a: 0.0 for a in WHITELIST}
                self.positions[CASH] = nav
                self.log("BREAKER: drawdown ≤ −25%% over 7 epochs — frozen, "
                         "basket parked in USDG")
        for g in [g for g in self.gov_queue if g["eta"] <= self.epoch + 1]:
            self.gov_queue.remove(g)
            if g["action"] == "phase3":
                self.phase = 3
                self.log("governance: phase 3 unlocked — full mandate")
            elif g["action"] == "unfreeze":
                self.frozen = False
                self.log("governance: agent unfrozen by holder vote")
```

`gov` method:

```python
    def gov(self, action):
        if any(g["action"] == action for g in self.gov_queue):
            return False
        if action == "phase3" and self.phase == 2:
            label = "Vote: unlock phase 3 (full mandate 35% / 20%)"
        elif action == "unfreeze" and self.frozen:
            label = "Vote: unfreeze the agent"
        else:
            return False
        self.gov_queue.append({"label": label, "action": action,
                               "eta": self.epoch + 3})
        self.log("governance vote queued: %s — timelock 3 epochs" % action)
        return True
```

Replace the placeholder `treasury`/`guard` blocks in `snapshot()`:

```python
            "treasury": {
                "runway_days": self.treasury_usdg / self.epoch_cost,
                "usdg": self.treasury_usdg, "epoch_cost": self.epoch_cost,
                "inflow_tax": self._tre_inflow_tax,
                "inflow_creator": self._tre_inflow_creator,
                "protocol_fund": self._tre_protocol,
                "hold_mode": self.hold_mode,
            },
            "guard": {
                "frozen": self.frozen, "freeze_epoch": self.freeze_epoch,
                "limits": {"max_weight_bps": PHASE_LIMITS[self.phase][0],
                           "turnover_bps": PHASE_LIMITS[self.phase][1]},
            },
```

Note for `test_frozen_agent_cancels_epochs`: when frozen, `_agent_cycle` still runs — the proposal is generated, and the `"agent status"` check fails, cancelling the epoch. That is intentional (the console shows the mechanism working). Verify `_guard_checks` already returns `ok: False` on `self.frozen` (Task 5 wrote it).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: agent treasury, -25% breaker, governance votes with 3-epoch timelock

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: HTTP server — static files + API, ticker thread

**Files:**
- Modify: `server.py` (new `# ==== http ====` section + `main()`)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: `Sim` (Tasks 3–6).
- Produces:
  - `ROOT = Path(__file__).resolve().parent`
  - `make_node(port: int, seed=None, public=False) -> ThreadingHTTPServer` — builds a server with a fresh `Sim` and per-server lock; `srv.sim`, `srv.sim_lock`, `srv.public` attributes. Binding port 0 gives an ephemeral port (tests use this).
  - `class NodeHandler(BaseHTTPRequestHandler)` — routes described below.
  - `start_ticker(srv) -> threading.Thread` (daemon) — advances `srv.sim` by `elapsed_real * sim.speed` every 0.25 s under `srv.sim_lock`.
  - `main(argv)` — argparse: `--port` (8000), `--seed`, `--public`; runs ticker + serve_forever; friendly message on `OSError: address in use`; Ctrl+C shuts down.
  - API contract: `GET /api/state`, `GET /api/claims?address=`, `POST /api/control {action: pause|resume|advance|speed, value}`, `POST /api/trade {side, amount}`, `POST /api/claim {}`, `POST /api/gov {action}`. POST replies `{"ok": true}` / 400 `{"ok": false, "error": ...}`. `/api/*` responses carry `Cache-Control: no-store`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
import json as _json
import urllib.request as _rq
import urllib.error as _rqerr


class TestHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = server.make_node(port=0, seed=3, config={"mode": "sim"})
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def url(self, path):
        return "http://127.0.0.1:%d%s" % (self.port, path)

    def get(self, path):
        with _rq.urlopen(self.url(path), timeout=5) as r:
            return r.status, r.read(), dict(r.headers)

    def post(self, path, body):
        req = _rq.Request(self.url(path), data=_json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with _rq.urlopen(req, timeout=5) as r:
            return r.status, _json.loads(r.read())

    def state(self):
        return _json.loads(self.get("/api/state")[1])

    def test_static_pages(self):
        status, body, headers = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"NOSTRO", body)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertEqual(self.get("/console.html")[0], 200)
        self.assertEqual(self.get("/front.js")[0], 200)
        self.assertEqual(self.get("/favicon.svg")[0], 200)

    def test_404_and_traversal(self):
        for path in ("/nope.html", "/../server.py", "/..%2fserver.py"):
            with self.assertRaises(_rqerr.HTTPError) as ctx:
                self.get(path)
            self.assertEqual(ctx.exception.code, 404)

    def test_state_contract(self):
        for _ in range(10):
            self.post("/api/control", {"action": "advance"})
        s = self.state()
        self.assertEqual(SIM_TOP_KEYS - set(s), set())
        self.assertGreaterEqual(s["epoch"], 11)
        self.assertTrue(s["track"])
        self.assertTrue(s["log"])
        self.assertTrue(any(e["checks"] for e in s["epochs"]))
        you = next(h for h in s["holders"] if h["id"] == "you")
        self.assertGreaterEqual(you["claimable_value"], 0)
        self.assertIn("no-store", self.get("/api/state")[2]["Cache-Control"])

    def test_control_pause_speed(self):
        self.post("/api/control", {"action": "pause"})
        self.assertTrue(self.state()["paused"])
        self.post("/api/control", {"action": "resume"})
        self.assertFalse(self.state()["paused"])
        self.post("/api/control", {"action": "speed", "value": 15})
        self.assertAlmostEqual(self.state()["speed"], 86400 / 15)

    def test_trade_claim_gov(self):
        before = next(h for h in self.state()["holders"] if h["id"] == "you")
        self.post("/api/trade", {"side": "buy", "amount": 50_000})
        after = next(h for h in self.state()["holders"] if h["id"] == "you")
        self.assertAlmostEqual(after["balance"], before["balance"] + 50_000)
        self.assertEqual(self.post("/api/claim", {})[1]["ok"], True)
        self.post("/api/gov", {"action": "phase3"})   # ok regardless of phase

    def test_bad_requests(self):
        for path, body in [("/api/control", {"action": "explode"}),
                           ("/api/trade", {"side": "buy", "amount": -5}),
                           ("/api/gov", {})]:
            req = _rq.Request(self.url(path), data=_json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with self.assertRaises(_rqerr.HTTPError) as ctx:
                _rq.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 400)
        req = _rq.Request(self.url("/api/trade"), data=b"{not json",
                          headers={"Content-Type": "application/json"})
        with self.assertRaises(_rqerr.HTTPError) as ctx:
            _rq.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)
```

Add `import threading` to the test file imports.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestHttp -v`
Expected: AttributeError — `make_node` not defined.

- [ ] **Step 3: Implement**

Append `# ==== http ====` section:

```python
# ==== http ======================================================

ROOT = Path(__file__).resolve().parent
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css",
                 ".js": "application/javascript", ".svg": "image/svg+xml",
                 ".jpg": "image/jpeg", ".json": "application/json",
                 ".ico": "image/x-icon"}


class NodeHandler(BaseHTTPRequestHandler):
    server_version = "NostroNode/0.1"

    def log_message(self, fmt, *args):
        pass                                          # keep the console quiet

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bad(self, msg):
        self._json({"ok": False, "error": msg}, 400)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            srv = self.server
            with srv.sim_lock:
                state = srv.sim.snapshot()
                state["public"] = srv.public
            return self._json(state)
        if path == "/api/claims":
            return self._json({"distributor": None, "rounds": []})
        self._static(path)

    def _static(self, path):
        name = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (ROOT / name)
        try:
            target = target.resolve()
            target.relative_to(ROOT)
        except (ValueError, OSError):
            return self._json({"error": "not found"}, 404)
        if not target.is_file() or target.suffix not in CONTENT_TYPES:
            return self._json({"error": "not found"}, 404)
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES[target.suffix])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return self._bad("bad json")
        srv = self.server
        with srv.sim_lock:
            sim = srv.sim
            if self.path == "/api/control":
                action = body.get("action")
                if action == "pause":
                    sim.paused = True
                elif action == "resume":
                    sim.paused = False
                elif action == "advance":
                    sim.force_close()
                elif action == "speed":
                    try:
                        per_epoch = float(body.get("value") or 0)
                    except (TypeError, ValueError):
                        return self._bad("bad speed")
                    if not 5 <= per_epoch <= 3600:
                        return self._bad("bad speed")
                    sim.set_speed(EPOCH_SIM / per_epoch)
                else:
                    return self._bad("unknown action")
                return self._json({"ok": True})
            if self.path == "/api/trade":
                side, amount = body.get("side"), body.get("amount")
                if side not in ("buy", "sell") or not isinstance(amount, (int, float)) \
                        or not amount > 0:
                    return self._bad("bad trade")
                sim.trade(side, amount)
                return self._json({"ok": True})
            if self.path == "/api/claim":
                return self._json({"ok": True, "paid": sim.claim()})
            if self.path == "/api/gov":
                if body.get("action") not in ("phase3", "unfreeze"):
                    return self._bad("unknown gov action")
                return self._json({"ok": sim.gov(body["action"])})
        self._bad("unknown endpoint")


def make_node(port, seed=None, public=False, config=None):
    # config override keeps tests hermetic: a developer's real nstro.json
    # (gitignored, possibly in live mode) must never leak into the suite
    srv = ThreadingHTTPServer(("127.0.0.1", port), NodeHandler)
    srv.sim = Sim(seed=seed)
    srv.sim_lock = threading.Lock()
    srv.public = public
    srv.config = config or {"mode": "sim"}   # Task 8 replaces the fallback with load_config()
    return srv


def start_ticker(srv):
    def run():
        last = time.monotonic()
        while True:
            time.sleep(0.25)
            now = time.monotonic()
            dt, last = now - last, now
            try:
                with srv.sim_lock:
                    srv.sim.advance(dt * srv.sim.speed)
            except Exception as exc:                       # sim must never die
                print("sim tick error: %r" % exc, file=sys.stderr)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Nostro node")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--public", action="store_true")
    args = ap.parse_args(argv)
    try:
        srv = make_node(args.port, seed=args.seed, public=args.public)
    except OSError:
        print("port %d is busy — pick another with --port" % args.port)
        return 1
    start_ticker(srv)
    print("nostro node: http://localhost:%d  (Ctrl+C to stop)" % args.port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Binding note: `make_node` binds `127.0.0.1` — local node by design. (If the user later wants LAN access, that's a one-line change, out of scope.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS.

- [ ] **Step 5: Manual smoke (no browser yet)**

```bash
python3 server.py --port 8123 & sleep 2 && curl -s localhost:8123/api/state | python3 -m json.tool | head -30; kill %1
```
Expected: JSON with `"mode": "sim"`, epoch ≥ 1.

- [ ] **Step 6: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: http server — static frontend + full sim JSON API + ticker thread

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Live mode — JSON-RPC reader, config watcher, nstro CLI

**Files:**
- Modify: `server.py` (new `# ==== live chain ====` section; extend handler/make_node/main)
- Create: `nstro` (executable)
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: `make_node`, `NodeHandler`, `DEFAULT_RPC` (earlier tasks).
- Produces:
  - `CONFIG_PATH = ROOT / "nstro.json"`; `load_config() -> dict` — `{"mode": "sim"|"live", "vault": str|None, "rpc_url": str|None}`; missing/corrupt file → `{"mode": "sim"}`.
  - `rpc_call(url: str, method: str, params: list, timeout=4) -> object` — raises `RpcError(Exception)` on transport/JSON-RPC errors.
  - `eth_call(url, to, data_hex) -> bytes` (empty on revert → raises RpcError).
  - `decode_abi_string(ret: bytes) -> str`, `decode_uint(ret: bytes) -> int`
  - `build_live(cfg: dict) -> dict` — the `live` object for the snapshot; on failure `{"ok": False, "error": "..."}`; on success at minimum `{"ok": True, "kind": "token"|"vault", "chain_id": int, "block": int, "code_size": int, "vault": str}` plus optional `name`, `symbol`, `decimals`, `total_supply`.
  - `start_live_poller(srv)` — daemon thread; every 4 s: reload config on mtime change; if live, `build_live` (network OUTSIDE the lock), store into `srv.live_snapshot` under lock.
  - `/api/state` in live mode: full sim snapshot + `"mode": "live"`, `"live": srv.live_snapshot`, `"config": {"rpc_url": cfg rpc}` (front.js reads sim fields like `s.nav` even in live mode — they must stay).
  - `nstro` CLI: `./nstro connect <0xaddr> [rpc]` (validates address, requires reachable RPC, warns if chain id ≠ 4663, writes config), `./nstro sim`, `./nstro status [--port N]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
import http.server as _hs
import subprocess
import tempfile


def _abi_str(s):
    b = s.encode()
    pad = b + b"\x00" * ((32 - len(b) % 32) % 32)
    return ((32).to_bytes(32, "big") + len(b).to_bytes(32, "big") + pad).hex()


MOCK_CALLS = {
    "0x06fdde03": _abi_str("Mock Token"),      # name()
    "0x95d89b41": _abi_str("MCK"),             # symbol()
    "0x313ce567": (18).to_bytes(32, "big").hex(),          # decimals()
    "0x18160ddd": (10 ** 27).to_bytes(32, "big").hex(),    # totalSupply()
}


class MockRpc(_hs.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = _json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        m, params = req["method"], req.get("params") or []
        if m == "eth_chainId":
            result = "0x1237"
        elif m == "eth_blockNumber":
            result = "0x100"
        elif m == "eth_getCode":
            result = "0x6080604052"
        elif m == "eth_call":
            sel = params[0]["data"][:10]
            if sel in MOCK_CALLS:
                result = "0x" + MOCK_CALLS[sel]
            else:                                   # previewUnits etc. → revert
                body = _json.dumps({"jsonrpc": "2.0", "id": req["id"],
                                    "error": {"code": 3, "message": "revert"}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        else:
            result = "0x0"
        body = _json.dumps({"jsonrpc": "2.0", "id": req["id"],
                            "result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class TestLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rpc = _hs.HTTPServer(("127.0.0.1", 0), MockRpc)
        cls.rpc_url = "http://127.0.0.1:%d" % cls.rpc.server_address[1]
        threading.Thread(target=cls.rpc.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.rpc.shutdown()

    def test_rpc_call(self):
        self.assertEqual(server.rpc_call(self.rpc_url, "eth_chainId", []), "0x1237")

    def test_build_live_token(self):
        cfg = {"mode": "live", "vault": "0x" + "12" * 20, "rpc_url": self.rpc_url}
        live = server.build_live(cfg)
        self.assertTrue(live["ok"])
        self.assertEqual(live["kind"], "token")
        self.assertEqual(live["chain_id"], 4663)
        self.assertEqual(live["block"], 256)
        self.assertEqual(live["name"], "Mock Token")
        self.assertEqual(live["symbol"], "MCK")
        self.assertEqual(live["decimals"], 18)
        self.assertAlmostEqual(live["total_supply"], 10 ** 9)   # 1e27 / 1e18
        self.assertGreater(live["code_size"], 0)

    def test_build_live_unreachable(self):
        cfg = {"mode": "live", "vault": "0x" + "12" * 20,
               "rpc_url": "http://127.0.0.1:1"}
        live = server.build_live(cfg)
        self.assertFalse(live["ok"])
        self.assertTrue(live["error"])

    def test_decode_abi_string(self):
        self.assertEqual(server.decode_abi_string(bytes.fromhex(_abi_str("hey"))), "hey")

    def test_cli_connect_and_sim(self):
        cli = str(Path(server.__file__).parent / "nstro")
        addr = "0x" + "ab" * 20
        env = dict(os.environ, NSTRO_CONFIG=str(
            Path(tempfile.mkdtemp()) / "nstro.json"))
        r = subprocess.run([sys.executable, cli, "connect", addr, self.rpc_url],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        cfg = _json.loads(Path(env["NSTRO_CONFIG"]).read_text())
        self.assertEqual(cfg["mode"], "live")
        self.assertEqual(cfg["vault"], addr)
        r = subprocess.run([sys.executable, cli, "sim"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(_json.loads(
            Path(env["NSTRO_CONFIG"]).read_text())["mode"], "sim")

    def test_cli_rejects_bad_address(self):
        cli = str(Path(server.__file__).parent / "nstro")
        r = subprocess.run([sys.executable, cli, "connect", "nonsense"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
```

Add `import os` to the test file imports.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_server.TestLive -v`
Expected: AttributeError — `rpc_call` not defined.

- [ ] **Step 3: Implement the live section in server.py**

```python
# ==== live chain ================================================

CONFIG_PATH = Path(os.environ.get("NSTRO_CONFIG") or (ROOT / "nstro.json"))
FEE_VAULT_ADDR = "0xB2FC6481A65BACc91277a3488dcc7f6b1C210813"
SEL_NAME, SEL_SYMBOL = "0x06fdde03", "0x95d89b41"
SEL_DECIMALS, SEL_TOTAL = "0x313ce567", "0x18160ddd"
SEL_PREVIEW_UNITS = "0x0d85a3ad"


class RpcError(Exception):
    pass


def load_config():
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
        if isinstance(cfg, dict) and cfg.get("mode") in ("sim", "live"):
            return cfg
    except (OSError, ValueError):
        pass
    return {"mode": "sim"}


def rpc_call(url, method, params, timeout=4):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1,
                          "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read())
    except (OSError, ValueError) as exc:
        raise RpcError("rpc unreachable: %s" % exc) from exc
    if "error" in out:
        raise RpcError(str(out["error"].get("message", out["error"])))
    return out.get("result")


def eth_call(url, to, data_hex):
    ret = rpc_call(url, "eth_call", [{"to": to, "data": data_hex}, "latest"])
    if not ret or ret == "0x":
        raise RpcError("empty return")
    return bytes.fromhex(ret[2:])


def decode_uint(ret):
    return int.from_bytes(ret[:32], "big")


def decode_abi_string(ret):
    off = int.from_bytes(ret[0:32], "big")
    ln = int.from_bytes(ret[off:off + 32], "big")
    return ret[off + 32:off + 32 + ln].decode("utf-8", "replace")


def build_live(cfg):
    url, vault = cfg.get("rpc_url") or DEFAULT_RPC, cfg.get("vault")
    try:
        chain_id = int(rpc_call(url, "eth_chainId", []), 16)
        block = int(rpc_call(url, "eth_blockNumber", []), 16)
        code = rpc_call(url, "eth_getCode", [vault, "latest"]) or "0x"
        if code == "0x":
            return {"ok": False, "error": "no contract code at %s" % vault}
        live = {"ok": True, "chain_id": chain_id, "block": block,
                "vault": vault, "code_size": (len(code) - 2) // 2}
        try:
            eth_call(url, vault, SEL_PREVIEW_UNITS + "0" * 64)
            live["kind"] = "vault"
        except RpcError:
            live["kind"] = "token"
        for key, sel, dec in (("name", SEL_NAME, decode_abi_string),
                              ("symbol", SEL_SYMBOL, decode_abi_string),
                              ("decimals", SEL_DECIMALS, decode_uint)):
            try:
                live[key] = dec(eth_call(url, vault, sel))
            except (RpcError, UnicodeDecodeError, IndexError):
                pass
        try:
            supply = decode_uint(eth_call(url, vault, SEL_TOTAL))
            live["total_supply"] = supply / 10 ** live.get("decimals", 18)
        except (RpcError, IndexError):
            pass
        return live
    except RpcError as exc:
        return {"ok": False, "error": str(exc)}


def start_live_poller(srv):
    def run():
        mtime = None
        while True:
            try:
                new_mtime = CONFIG_PATH.stat().st_mtime if CONFIG_PATH.exists() else None
                if new_mtime != mtime:
                    mtime = new_mtime
                    with srv.sim_lock:
                        srv.config = load_config()
                        srv.live_snapshot = None
                cfg = srv.config
                if cfg.get("mode") == "live" and cfg.get("vault"):
                    snap = build_live(cfg)              # network: outside the lock
                    with srv.sim_lock:
                        srv.live_snapshot = snap
            except Exception as exc:
                print("live poll error: %r" % exc, file=sys.stderr)
            time.sleep(4)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
```

Wire into `make_node` (add attributes) and `main` (start poller):

```python
    # in make_node: replace the config fallback and add the live slot —
    srv.config = config or load_config()
    srv.live_snapshot = None
    # in main, after start_ticker(srv):
    start_live_poller(srv)
```

Update the `/api/state` branch of `do_GET`:

```python
        if path == "/api/state":
            srv = self.server
            with srv.sim_lock:
                state = srv.sim.snapshot()
                state["public"] = srv.public
                cfg = srv.config
                if cfg.get("mode") == "live":
                    state["mode"] = "live"
                    state["config"] = {"rpc_url": cfg.get("rpc_url") or DEFAULT_RPC}
                    state["live"] = srv.live_snapshot
            return self._json(state)
```

(front.js/app.js in live mode still read `s.epoch`, `s.nav`, `s.treasury.runway_days` etc. before hiding sim-only elements — that is why the full sim snapshot stays underneath.)

- [ ] **Step 4: Create the nstro CLI**

Create `nstro`:

```python
#!/usr/bin/env python3
"""nstro — switch the Nostro node between sim and live modes.

  ./nstro connect <token-or-vault-address> [rpc-url]
  ./nstro sim
  ./nstro status [port]
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

CONFIG = Path(os.environ.get("NSTRO_CONFIG") or
              Path(__file__).resolve().parent / "nstro.json")
DEFAULT_RPC = "https://rpc.mainnet.chain.robinhood.com"
CHAIN_ID = 4663


def rpc(url, method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1,
                          "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=6) as r:
        out = json.loads(r.read())
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["result"]


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2))
    print("wrote %s" % CONFIG)


def cmd_connect(argv):
    if not argv:
        sys.exit("usage: ./nstro connect <0x-address> [rpc-url]")
    addr = argv[0]
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
        sys.exit("error: %r is not a 0x… address" % addr)
    url = argv[1] if len(argv) > 1 else DEFAULT_RPC
    try:
        chain = int(rpc(url, "eth_chainId", []), 16)
    except Exception as exc:
        sys.exit("error: RPC %s unreachable (%s) — pass a working rpc-url" % (url, exc))
    if chain != CHAIN_ID:
        print("warning: chain id %d, expected %d (Robinhood Chain)" % (chain, CHAIN_ID))
    save({"mode": "live", "vault": addr, "rpc_url": url})
    print("live mode on — the node picks it up within ~4s, no restart needed")


def cmd_sim():
    cfg = {"mode": "sim"}
    if CONFIG.exists():
        try:
            old = json.loads(CONFIG.read_text())
            if old.get("rpc_url"):
                cfg["rpc_url"] = old["rpc_url"]
        except ValueError:
            pass
    save(cfg)
    print("sim mode on")


def cmd_status(argv):
    port = int(argv[0]) if argv else 8000
    cfg = {"mode": "sim"}
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
        except ValueError:
            pass
    print("config: %s" % json.dumps(cfg))
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:%d/api/state" % port, timeout=3) as r:
            s = json.loads(r.read())
        print("node: %s mode, epoch %s, nav %.0f USDG"
              % (s["mode"], s["epoch"], s["nav"]))
    except Exception:
        print("node: offline (run: python3 server.py)")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("connect", "sim", "status"):
        print(__doc__.strip())
        sys.exit(2)
    if args[0] == "connect":
        cmd_connect(args[1:])
    elif args[0] == "sim":
        cmd_sim()
    else:
        cmd_status(args[1:])


if __name__ == "__main__":
    main()
```

Then: `chmod +x nstro`

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_server -v`
Expected: all PASS. The CLI tests use `NSTRO_CONFIG` env override so they never touch a real `nstro.json`; verify `server.py` reads the same env var (it does — `CONFIG_PATH`).

- [ ] **Step 6: One-shot real-chain check (network permitting)**

```bash
python3 - <<'EOF'
import server
cfg = {"mode": "live", "vault": "0xB2FC6481A65BACc91277a3488dcc7f6b1C210813",
       "rpc_url": server.DEFAULT_RPC}
print(server.build_live(cfg))
EOF
```
Expected: either `ok: True` with chain_id 4663, or `ok: False` with a clean error (offline is fine — do not fail the task on network conditions; the mock tests are authoritative).

- [ ] **Step 7: Commit**

```bash
git add server.py nstro tests/test_server.py
git commit -m "feat: live chain mode over json-rpc + nstro CLI (connect/sim/status)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: README, full suite, browser verification

**Files:**
- Create: `README.md`
- Create: `.claude/launch.json`

**Interfaces:**
- Consumes: everything.

- [ ] **Step 1: Write README.md (Russian)**

```markdown
# nostro.capital — локальный узел

Сайт Nostro Agent ($NSTRO): лендинг + консоль с полной симуляцией
экономики (эпохи, корзина, keccak-коммиты агента, MandateGuard, брейкер,
голосования) и live-режимом чтения Robinhood Chain.

## Запуск

    python3 server.py

Открыть http://localhost:8000 — лендинг, http://localhost:8000/console.html —
консоль. Python ≥ 3.9, зависимостей нет.

Флаги: `--port 8000`, `--seed N` (воспроизводимая симуляция), `--public`
(режим публичного узла — симуляция скрыта).

## Управление симуляцией

В шапке консоли: пауза, скорость эпохи (15/60/180 c), «next epoch».
Кнопки buy/sell/claim торгуют кошельком «you»; голосования — в карточке
Governance.

## Live-режим

    ./nstro connect 0x<адрес-токена> [rpc-url]   # подключить контракт
    ./nstro sim                                  # вернуть симуляцию
    ./nstro status [порт]                        # что происходит

RPC по умолчанию: https://rpc.mainnet.chain.robinhood.com (chain id 4663).
Узел подхватывает nstro.json на лету, рестарт не нужен.

## Тесты

    python3 -m unittest tests.test_server -v
```

- [ ] **Step 2: Create `.claude/launch.json`**

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "nostro",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["server.py"],
      "port": 8000
    }
  ]
}
```

- [ ] **Step 3: Run the full suite one more time**

Run: `python3 -m unittest tests.test_server -v`
Expected: every test PASS. Fix anything red before proceeding.

- [ ] **Step 4: Browser verification (preview tools, not Bash)**

1. `preview_start {name: "nostro"}` → tab opens on the landing page.
2. Wait ~5 s; `read_console_messages {onlyErrors: true}` → must be empty (no JS errors).
3. `read_page` on the landing: the data strip shows `EPOCH`, `NAV`, `SIM DATA / LOCAL NODE` (not `CONNECTING`, not `NODE OFFLINE`); the commit terminal shows a real `0x…` hash after a few epochs.
4. Navigate to `/console.html`; `read_page`: cards Basket, NAV chart, Track record, Holders (row `you`, row with `bot` tag), MandateGuard, AgentTreasury, Governance, Node log are all populated.
5. Click `next epoch →` (computer tool) twice; confirm the epoch counter in the header increments and a new track item appears.
6. Click `buy` (default 100000) then `claim` once claimable > 0; confirm wallet numbers change.
7. Change speed select to `epoch = 15s`; confirm the epoch progress bar speeds up.
8. `computer {action: "screenshot"}` of the landing and of the console → send both to the user.

Any JS error or empty card = a contract mismatch: read the relevant renderer in `front.js`/`app.js`, fix **server.py** (never the frontend), re-check.

- [ ] **Step 5: Final commit**

```bash
git add README.md .claude/launch.json
git commit -m "docs: README + launch config; browser-verified against the untouched frontend

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review Notes (already applied)

- Spec coverage: crypto (T1–2), sim economics (T3–6), API+static (T7), live+CLI (T8), README/verification (T9). `--public` flag: T7 `main`/`make_node`; snapshot honors it in `do_GET`.
- The frontend reads sim fields even in live mode (front.js `tick()` lines 322–343) — covered by keeping the full sim snapshot under live overrides (T8).
- `epochs[N].checks` describe the vector for N+1 (app.js `renderTrack`: `submitted = dnav[r.epoch - 1]`) — covered by `_agent_cycle` writing into the just-closed record (T5).
- Type consistency: `weights` are bps ints; `holders` money fields are floats; `track.hash` is `0x`+64hex; `speed` is sim-sec-per-real-sec everywhere; `/api/control speed` converts from seconds-per-epoch.
