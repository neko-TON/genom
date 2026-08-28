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
        self.treasury_usdg = 2400.0
        self.epoch_cost = 120.0
        self.protocol_fund = 0.0
        self.freeze_epoch = 0
        # __init__ additions (Task 5)
        self._pending_commit = None      # {"epoch","weights","thesis","nonce","hash","committed_at"}
        self._force_bad_next = False
        self._bad_cadence = self.rng.randrange(8, 13)
        self.last_rebalance_epoch = 0
        self.hold_mode = False
        self._shadow_positions = None    # dict like self.positions, set at phase 1 entry
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

    def force_close(self):
        self._close_epoch()

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

    def _integrate(self, dt):
        self.t += dt
        dt_days = dt / EPOCH_SIM
        for a in WHITELIST:
            g = self.rng.gauss(0.0, 1.0)
            mu, sg = self._drift[a], self._sigma[a]
            self.prices[a] *= math.exp((mu - 0.5 * sg * sg) * dt_days
                                       + sg * math.sqrt(dt_days) * g)
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
        self._reveal_pending()
        if self.phase >= 1 or self.epoch >= 2:   # first proposal at close of epoch 2
            self._agent_cycle()
        self._update_shadow()
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
            "pending_quote": self.pending_quote(),
            "volume_epoch": self.volume_epoch,
            "epochs": list(self.epochs), "track": list(self.track),
            "holders": [{k: h[k] for k in ("id", "name", "kind", "balance",
                                           "last_share", "claimable_value",
                                           "claimed_value")}
                        for h in self.holders],
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
            "gov_queue": list(self.gov_queue), "log": list(self.log_items),
        }


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
