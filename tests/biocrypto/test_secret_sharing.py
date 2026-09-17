import math
import secrets

import pytest

# Simple Shamir SSS over integers (demo only). Replace with vetted lib in production.

PRIME = 2**127 - 1

def _eval_poly(coeffs, x):
    y = 0
    for c in reversed(coeffs):
        y = (y * x + c) % PRIME
    return y


def shamir_split(secret_int, t, n):
    coeffs = [secret_int] + [secrets.randbelow(PRIME) for _ in range(t-1)]
    shares = [(i, _eval_poly(coeffs, i)) for i in range(1, n+1)]
    return shares


def shamir_combine(shares):
    total = 0
    for i, (xi, yi) in enumerate(shares):
        num, den = 1, 1
        for j, (xj, _) in enumerate(shares):
            if i == j:
                continue
            num = (num * (-xj)) % PRIME
            den = (den * (xi - xj)) % PRIME
        lag = num * pow(den, -1, PRIME)
        total = (PRIME + total + yi * lag) % PRIME
    return total


def test_shamir_threshold():
    secret = secrets.randbelow(PRIME)
    t, n = 3, 5
    shares = shamir_split(secret, t, n)
    # Any t shares reconstruct
    subset = shares[:t]
    rec = shamir_combine(subset)
    assert rec == secret
    # Fewer than t should not trivially reveal (basic check)
    subset2 = shares[:t-1]
    assert shamir_combine(subset) == secret
