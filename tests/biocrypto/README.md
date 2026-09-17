# Biocryptography Test Plan (BitNet)

This suite validates operational security using standard primitives plus biological orchestration.

## Test Groups
- KATs (Known Answer Tests)
- PQC interop (Kyber/Dilithium via liboqs if available)
- Secret Sharing (Shamir t-of-n)
- RNG health (DRBG seeded with conditioned biological entropy)
- Distributed sync and recovery
- Evolution response under threat

Run: bitnet cli (to be implemented) or `pytest -q tests/biocrypto`.
