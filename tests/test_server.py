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


if __name__ == "__main__":
    unittest.main()
