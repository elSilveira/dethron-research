"""Run with the pinned gateway environment; real crypto, no network mocks."""
import hashlib
import unittest

try:
    import LXMF
    import RNS
except ImportError as exc:
    raise unittest.SkipTest("requires .venv-gateway") from exc

from gateway_contract import audit_receipt, config_text, payload


class GatewayContractTests(unittest.TestCase):
    def setUp(self):
        self.sender = RNS.Identity()
        receiver = RNS.Identity()
        source = RNS.Destination(self.sender, RNS.Destination.OUT,
                                 RNS.Destination.SINGLE, "lxmf", "delivery")
        dest = RNS.Destination(receiver, RNS.Destination.OUT,
                               RNS.Destination.SINGLE, "lxmf", "delivery")
        self.spec = {"id": "small", "size": 1024, "destination": dest.hash.hex(),
                     "source": source.hash.hex(), "public_key": self.sender.get_public_key().hex()}
        msg = LXMF.LXMessage(dest, source, payload("small", 1024), "small")
        msg.pack()
        self.raw = msg.packed

    def test_exact_authenticated_receipt(self):
        result = audit_receipt(self.raw, self.spec)
        self.assertEqual(result["sha256"], hashlib.sha256(payload("small", 1024)).hexdigest())

    def test_payload_signature_and_destination_corruption_are_rejected(self):
        for offset in (0, 32, len(self.raw)-2):
            changed = bytearray(self.raw)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                audit_receipt(bytes(changed), self.spec)

    def test_wrong_expected_content_is_rejected(self):
        with self.assertRaises(ValueError):
            audit_receipt(self.raw, {**self.spec, "id": "another"})

    def test_sender_status_cannot_be_a_receipt(self):
        with self.assertRaises(ValueError):
            audit_receipt(b'{"state":"sent"}', self.spec)

    def test_config_has_only_declared_loopback_contacts(self):
        value = config_text(9000, [9001, 9002])
        self.assertIn("share_instance = No", value)
        self.assertIn("enable_transport = No", value)
        self.assertEqual(value.count("target_host = 127.0.0.1"), 2)
        self.assertNotIn("AutoInterface", value)


if __name__ == "__main__":
    unittest.main()
