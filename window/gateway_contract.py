"""Frozen G0 inputs and receiver-side audit."""
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from RNS.vendor import umsgpack

PROFILE = {"version": 1, "reference": {"rns": "1.5.4", "lxmf": "1.1.1"},
           "sizes": [1024, 65536, 1048576], "deadline_seconds": 120,
           "propagation_limit_kb": 2048, "delivery_limit_kb": 2048,
           "autopeer": False, "transport": "loopback TCP", "unit": "whole LXMF message"}


def payload(label, size):
    return hashlib.shake_256(("dethron-g0-v1:" + label).encode()).digest(size)


def config_text(port, contacts):
    base = ("[reticulum]\n share_instance = No\n enable_transport = No\n"
            " discover_interfaces = No\n[logging]\n loglevel = 3\n[interfaces]\n"
            " [[Listener]]\n type = TCPServerInterface\n enabled = Yes\n"
            f" listen_ip = 127.0.0.1\n listen_port = {port}\n")
    for index, contact in enumerate(contacts):
        base += (f" [[Contact{index}]]\n type = TCPClientInterface\n enabled = Yes\n"
                 f" target_host = 127.0.0.1\n target_port = {contact}\n")
    return base


def audit_receipt(raw, spec):
    try:
        if len(raw) < 97:
            raise ValueError("missing receiver packet")
        if raw[:16].hex() != spec["destination"] or raw[16:32].hex() != spec["source"]:
            raise ValueError("wrong endpoint")
        fields = umsgpack.unpackb(raw[96:])
        signed = raw[:32] + umsgpack.packb(fields[:4])
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(spec["public_key"])[32:])
        key.verify(raw[32:96], signed + hashlib.sha256(signed).digest())
        expected = payload(spec["id"], spec["size"])
        if fields[1] != spec["id"].encode() or fields[2] != expected:
            raise ValueError("unexpected content")
        return {"id": spec["id"], "size": len(expected),
                "sha256": hashlib.sha256(expected).hexdigest(), "signature": "valid"}
    except Exception as exc:
        raise ValueError(f"invalid receiver evidence: {exc}") from exc
