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
