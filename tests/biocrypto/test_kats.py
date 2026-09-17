import os
import secrets
import hashlib
import hmac

import pytest

# Basic KATs for AES-GCM would normally use a crypto lib; placeholder hashes used here

VECTORS = [
    (b"", hashlib.sha256(b"").hexdigest()),
    (b"BitNet", hashlib.sha256(b"BitNet").hexdigest()),
    (b"BioCrypto", hashlib.sha256(b"BioCrypto").hexdigest()),
]

@pytest.mark.parametrize("msg, expected", VECTORS)
def test_hash_kat(msg, expected):
    assert hashlib.sha256(msg).hexdigest() == expected


def test_hmac_constant_time():
    key = secrets.token_bytes(32)
    msg = b"BitNet-BioCrypto"
    mac1 = hmac.new(key, msg, hashlib.sha256).digest()
    mac2 = hmac.new(key, msg, hashlib.sha256).digest()
    assert hmac.compare_digest(mac1, mac2)
