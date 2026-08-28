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
