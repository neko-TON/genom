# Vercel Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Genom site on Vercel: static front + deterministic read-only serverless simulation (`/api/state`, `/api/claims`), console in the already-existing public observer mode.

**Architecture:** Task 1 adds `api/state.py` (rebuilds `Sim` from a fixed seed and canonically fast-forwards it to `now − GENESIS_TS`), `api/claims.py` (static stub, mirrors the local handler), `vercel.json`, `.vercelignore`, and a local unittest for determinism/continuity/performance. Task 2 is the coordinator's deploy (explicit user consent → `npx vercel --prod`) and production browser pass.

**Tech Stack:** Vercel Python runtime (BaseHTTPRequestHandler style), existing `server.Sim` (import side-effect-free: module has only imports/constants at top level and a `__main__` guard). No env vars, no secrets.

**Spec:** `docs/superpowers/specs/2026-08-30-vercel-deploy-design.md`.

## Global Constraints

- Existing files unchanged (server.py, front/app js/css, HTML, tests) — Task 1 only ADDS files. Local mode and the existing 46 tests keep passing.
- The serverless state is a pure function of wall-clock time: fixed `GENOM_SEED`, fixed `GENESIS_TS`, canonical epoch-by-epoch chunking (call pattern must not depend on request timing beyond the remainder of the current epoch).
- `state["public"] = True` in the serverless response (console/landing then behave as observer — existing app.js/front.js behavior).
- server.py becomes publicly fetchable as a static file on Vercel — accepted (open concept code, no secrets).
- Production deploy happens ONLY after the user's explicit "да" in chat (spec requirement).
- Commit messages end with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Serverless functions + Vercel config + determinism test

**Files:**
- Create: `api/state.py`, `api/claims.py`, `vercel.json`, `.vercelignore`
- Test: `tests/test_vercel_state.py`

**Interfaces:**
- Consumes: `server.Sim` — constructor `Sim(seed=None)`, method `advance(dt_sim)` (sim-seconds), method `snapshot()` → dict; constant `EPOCH_SIM = 86400.0` (sim-seconds per epoch); default node speed 1440.0 sim-sec per real-sec (⇒ one epoch = 60 real seconds).
- Produces: `build_state(now=None)` in `api/state.py` (Task 2 smoke-checks it in production via GET `/api/state`).

- [ ] **Step 1: Write the failing test** — create `tests/test_vercel_state.py`:

```python
"""Детерминизм и непрерывность serverless-состояния для Vercel."""
import json
import time
import unittest

from api.state import CAP_REAL, GENESIS_TS, build_state


class TestVercelState(unittest.TestCase):
    def test_deterministic(self):
        t = GENESIS_TS + 3600.0
        a = json.dumps(build_state(t), sort_keys=True)
        b = json.dumps(build_state(t), sort_keys=True)
        self.assertEqual(a, b)

    def test_epoch_advances(self):
        s1 = build_state(GENESIS_TS + 3600.0)   # 60 эпох прожито
        s2 = build_state(GENESIS_TS + 3660.0)   # +1 эпоха
        self.assertEqual(s2["epoch"], s1["epoch"] + 1)

    def test_continuity_between_polls(self):
        s1 = build_state(GENESIS_TS + 3600.0)
        s2 = build_state(GENESIS_TS + 3602.0)   # тот же мир парой секунд позже
        self.assertEqual(s2["epoch"], s1["epoch"])
        n = len(s1["epochs"])
        self.assertEqual(s2["epochs"][:n], s1["epochs"])

    def test_public_flag(self):
        self.assertTrue(build_state(GENESIS_TS + 60.0)["public"])

    def test_cap_and_speed(self):
        t0 = time.perf_counter()
        s = build_state(GENESIS_TS + CAP_REAL + 999999.0)
        dt = time.perf_counter() - t0
        self.assertLessEqual(s["epoch"], int(CAP_REAL / 60.0) + 1)
        self.assertLess(dt, 5.0, "пересчёт на капе должен укладываться в 5с (замерено: %.2fs)" % dt)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 -m unittest tests.test_vercel_state -v`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'api'`.

- [ ] **Step 3: Create `api/state.py`:**

```python
"""Vercel serverless: детерминированное публичное состояние узла Genom.

Мир пересоздаётся на каждый запрос: Sim(seed) канонично прокручивается
поэпоховыми кусками до (now − GENESIS_TS) — у всех посетителей одно и то
же состояние. Редеплой с новым GENESIS_TS перезапускает мир.
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import EPOCH_SIM, Sim  # noqa: E402

GENOM_SEED = 4663                  # chain id Robinhood Chain — фиксированный мир
GENESIS_TS = 1788048000.0          # 2026-08-30 00:00:00 UTC
SPEED = 1440.0                     # sim-сек за реальную сек (эпоха = 60с)
CAP_REAL = 20160 * 60.0            # ~2 недели жизни; дальше мир замирает


def build_state(now=None):
    if now is None:
        now = time.time()
    elapsed = max(0.0, min(now - GENESIS_TS, CAP_REAL))
    sim = Sim(seed=GENOM_SEED)
    full_epochs, remainder = divmod(elapsed * SPEED, EPOCH_SIM)
    for _ in range(int(full_epochs)):
        sim.advance(EPOCH_SIM)
    if remainder:
        sim.advance(remainder)
    state = sim.snapshot()
    state["public"] = True
    return state


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(build_state()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "public, max-age=5")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
```

- [ ] **Step 4: Create `api/claims.py`** (зеркало локального хендлера — статичная заглушка):

```python
"""Vercel serverless: /api/claims — как в локальном узле, пустая заглушка."""
import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"distributor": None, "rounds": []}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
```

- [ ] **Step 5: Create `vercel.json`:**

```json
{
  "functions": {
    "api/*.py": {
      "includeFiles": "server.py"
    }
  }
}
```

- [ ] **Step 6: Create `.vercelignore`:**

```
docs/
tests/
venv/
__pycache__/
.claude/
.superpowers/
genom.json
genom
README.md
```

- [ ] **Step 7: Run the new test to verify it passes**

Run: `python3 -m unittest tests.test_vercel_state -v`
Expected: 5 tests PASS. Note the measured cap time printed on failure only — if `test_cap_and_speed` fails on the 5s budget, report DONE_WITH_CONCERNS with the measured time instead of tuning CAP_REAL yourself.

- [ ] **Step 8: Run the full suite**

Run: `python3 -m unittest discover -s tests -v 2>&1 | tail -3`
Expected: 51 tests, OK (46 старых + 5 новых).

- [ ] **Step 9: Commit**

```bash
git add api/state.py api/claims.py vercel.json .vercelignore tests/test_vercel_state.py
git commit -m "feat: Vercel — детерминированная serverless-симуляция и конфиг деплоя

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Coordinator deploy + production pass

- [ ] Ask the user for the explicit "да" to publish this build to production (spec gate). Do not deploy without it.
- [ ] `npx vercel link --yes --project genom` then `npx vercel --prod --yes` from the repo root (CLI already authenticated by the user).
- [ ] Production checks: `GET <prod>/api/state` twice ≥10 minutes apart (public epoch = 10 min) → `epoch` advanced by ≥1 and `public` is true; `GET <prod>/api/claims` → `{"distributor": null, "rounds": []}`.
- [ ] Browser pass on the prod URL: landing shows live strip values (no eternal LINKING UP); console renders the basket as an observer (no pause/skip/trade controls — public mode); mobile width OK; zero console errors.
- [ ] Report the production URL to the user; then finishing-a-development-branch.
