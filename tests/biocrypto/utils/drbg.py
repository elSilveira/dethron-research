from __future__ import annotations

import os
import secrets
import struct
import hashlib

# A minimal DRBG wrapper using SHA256 in CTR-like fashion for testing only.
# In production rely on OS CSPRNG or SP800-90A implementations.

class TestDRBG:
    def __init__(self, seed: bytes):
        self.key = hashlib.sha256(seed).digest()
        self.counter = 0

    def reseed(self, addl: bytes):
        self.key = hashlib.sha256(self.key + addl).digest()
        self.counter = 0

    def random(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            blk = hashlib.sha256(self.key + struct.pack('>Q', self.counter)).digest()
            out.extend(blk)
            self.counter += 1
        return bytes(out[:n])
