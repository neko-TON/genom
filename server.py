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
