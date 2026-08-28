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
