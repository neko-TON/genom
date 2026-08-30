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
        s1 = build_state(GENESIS_TS + 6000.0)   # 10 эпох
        s2 = build_state(GENESIS_TS + 6600.0)   # +1 эпоха
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
        self.assertLessEqual(s["epoch"], int(CAP_REAL / 600.0) + 1)
        self.assertLess(dt, 8.0, "пересчёт на капе должен укладываться в 8с (замерено: %.2fs)" % dt)


if __name__ == "__main__":
    unittest.main()
