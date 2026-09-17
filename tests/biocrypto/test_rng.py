import os
import secrets
import statistics

import pytest

# RNG health: monobit frequency and runs test (very rough). Replace with NIST STS in CI.

def _monobit_frequency(bits):
    ones = sum(bits)
    n = len(bits)
    s = abs(ones - (n - ones))
    return s / n


def _runs_test(bits):
    # Count runs in a binary sequence
    if not bits:
        return 0
    runs = 1
    for i in range(1, len(bits)):
        if bits[i] != bits[i-1]:
            runs += 1
    return runs


def test_rng_health_basic():
    data = secrets.token_bytes(16384)
    bits = [(b >> k) & 1 for b in data for k in range(8)]
    imbalance = _monobit_frequency(bits)
    runs = _runs_test(bits)
    n = len(bits)
    # Heuristic thresholds: imbalance should be < 2%
    assert imbalance < 0.02
    # For fair coin, expected runs ≈ n/2. Accept ±5% band.
    lower, upper = int(0.45 * n), int(0.55 * n)
    assert lower < runs < upper
