import os
import json
import secrets
import time

import pytest

# Simulate distributed sync: produce shards and recombine after artificial delay
from tests.biocrypto.test_secret_sharing import PRIME, shamir_split, shamir_combine


def test_distributed_sync_reconstruction(tmp_path):
    secret = secrets.randbelow(PRIME)
    t, n = 3, 5
    shares = shamir_split(secret, t, n)

    # Simulate network delay and out-of-order arrival
    delayed = list(reversed(shares))
    recovered = shamir_combine(delayed[:t])
    assert recovered == secret

    # Persist and reload (simulating node restarts)
    f = tmp_path / "shares.json"
    json.dump(delayed, open(f, "w"))
    loaded = json.load(open(f))
    assert shamir_combine(loaded[:t]) == secret
