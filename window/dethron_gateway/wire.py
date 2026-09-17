"""Verify native LXMF signatures and bind the application manifest to both endpoints."""
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import RNS
from RNS.vendor import umsgpack

from .protocol import MAX_WIRE, decode


def authenticate(raw, public_key, destination, now):
    try:
        if not 97 <= len(raw) <= MAX_WIRE+4096 or raw[:16].hex() != destination:
            raise ValueError("invalid packet bounds/destination")
        identity = RNS.Identity(create_keys=False)
        identity.load_public_key(public_key)
        if RNS.Destination.hash(identity, "lxmf", "delivery") != raw[16:32]:
            raise ValueError("source identity does not match signing key")
        fields = umsgpack.unpackb(raw[96:])
        signed = raw[:32] + umsgpack.packb(fields[:4])
        Ed25519PublicKey.from_public_bytes(public_key[32:]).verify(
            raw[32:96], signed + hashlib.sha256(signed).digest())
        if fields[1] != b"dethron-g1":
            raise ValueError("wrong application envelope")
        obj = decode(fields[2], now)
        if obj["source"] != raw[16:32].hex() or obj["destination"] != destination:
            raise ValueError("manifest endpoint mismatch")
        return obj
    except Exception as exc:
        raise ValueError(f"unauthenticated/invalid G1 packet: {exc}") from exc
