"""Signed synthetic fixtures exercise the auditor, not the physical network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    import LXMF
    import RNS
except ImportError as exc:
    raise unittest.SkipTest("requires .venv-gateway") from exc

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode, receipt_envelope
from g2_audit import audit_case


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.destination()
        self.dest = self.destination()
        self.content = hashlib.shake_256(b"dethron-g2-profile-v1").digest(98304)
        self.parts = split(self.content, 3, "f"*32)
        (self.root/"D"/"packets").mkdir(parents=True)
        rows = [{"event": "crash", "node": "O", "time": 1}]
        rows += [{"event": "fetch_complete", "limit_kb": 64, "relay": n, "time": i+2}
                 for i, n in enumerate("CAB")]
        (self.root/"timeline.jsonl").write_text("\n".join(json.dumps(r) for r in rows))

    @staticmethod
    def destination():
        return RNS.Destination(RNS.Identity(), RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")

    @staticmethod
    def packet(obj, source, dest):
        message = LXMF.LXMessage(dest, source, encode(obj), "dethron-g1")
        message.pack()
        return message.packed

    def fixture(self, mode):
        timeline = self.root/"timeline.jsonl"
        rows = [json.loads(line) for line in timeline.read_text().splitlines()]
        for i, row in enumerate(rows[1:]):
            complete = mode == "split" and i == 2
            row["receiver"] = {"completed": complete, "objects": [
                {"id": "f"*32, "count": min(i+1, 2 if mode == "missing" else 3), "complete": complete}]}
        timeline.write_text("\n".join(json.dumps(r) for r in rows))
        inputs = {}
        for i in ([0, 2] if mode == "missing" else [0, 1, 2]):
            obj = data_envelope(self.source.hash.hex(), self.dest.hash.hex(), encode(self.parts[i]), 100)
            inputs[str(i)] = obj
            (self.root/"D"/"packets"/f"{i}.lxmf").write_bytes(self.packet(obj, self.source, self.dest))
        manifest = {"mode": mode, "source": {"destination": self.source.hash.hex(),
                    "public_key": self.source.identity.get_public_key().hex()},
                    "destination": {"destination": self.dest.hash.hex(), "public_key": self.dest.identity.get_public_key().hex()},
                    "expires": 100, "inputs": inputs, "object": self.parts[0]["manifest"], "profile": {"payload_bytes": 98304}}
        (self.root/"manifest.json").write_text(json.dumps(manifest))
        if mode == "split":
            (self.root/"D"/"output.bin").write_bytes(self.content)
            original = data_envelope(self.source.hash.hex(), self.dest.hash.hex(), self.content, 100, "f"*32)
            (self.root/"D"/"completion.lxmf").write_bytes(self.packet(receipt_envelope(original), self.dest, self.source))

    def test_complete_evidence_passes(self):
        self.fixture("split")
        self.assertTrue(audit_case(self.root)["completed"])

    def test_missing_part_cannot_be_hidden_by_a_fabricated_output(self):
        self.fixture("missing")
        self.assertFalse(audit_case(self.root)["completed"])
        (self.root/"D"/"output.bin").write_bytes(self.content)
        with self.assertRaises(ValueError):
            audit_case(self.root)

    def test_modified_completion_signature_is_rejected(self):
        self.fixture("split")
        path = self.root/"D"/"completion.lxmf"
        raw = bytearray(path.read_bytes())
        raw[32] ^= 1
        path.write_bytes(raw)
        with self.assertRaises(ValueError):
            audit_case(self.root)

    def test_contact_evidence_cannot_claim_early_completion(self):
        self.fixture("split")
        path = self.root/"timeline.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[1]["receiver"]["completed"] = True
        path.write_text("\n".join(json.dumps(r) for r in rows))
        with self.assertRaises(ValueError):
            audit_case(self.root)

    def test_contact_evidence_requires_expected_unique_part_counts(self):
        self.fixture("missing")
        path = self.root/"timeline.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[3]["receiver"]["objects"][0]["count"] = 3
        path.write_text("\n".join(json.dumps(r) for r in rows))
        with self.assertRaises(ValueError):
            audit_case(self.root)


if __name__ == "__main__":
    unittest.main()
