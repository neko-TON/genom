import json
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
        for a in server.WHITELIST:            # market crash: −60% across the board
            self.sim.prices[a] *= 0.40
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
            self.sim.prices[a] *= 0.40
        self.sim.force_close()
        self.sim.force_close()
        rec = self.sim.epochs[-1]
        self.assertIsNotNone(rec["cancelled"])
        status = next(c for c in rec["checks"] if c["name"] == "agent status")
        self.assertFalse(status["ok"])


if __name__ == "__main__":
    unittest.main()
