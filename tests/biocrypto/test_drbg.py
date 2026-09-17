import secrets
import hashlib

from tests.biocrypto.utils.drbg import TestDRBG


def test_drbg_reseed_changes_stream():
    seed = secrets.token_bytes(32)
    drbg = TestDRBG(seed)
    a = drbg.random(64)
    drbg.reseed(b"more-entropy")
    b = drbg.random(64)
    assert a != b


def test_drbg_repeatability_with_same_seed():
    seed = b"fixed-seed"
    d1 = TestDRBG(seed)
    d2 = TestDRBG(seed)
    assert d1.random(128) == d2.random(128)
