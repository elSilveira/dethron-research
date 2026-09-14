import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from protocol import checked_report, decode_event


class ProtocolTests(unittest.TestCase):
    def test_malformed_event_types_are_rejected_as_protocol_errors(self):
        valid = {"schema": 1, "sequence": 0, "kind": "started", "elapsed_ms": 0, "data": {}}
        for replacement in [{"kind": []}, {"kind": {}}, {"schema": True}, {"sequence": False}]:
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                decode_event(json.dumps(dict(valid, **replacement)), 0)

    def test_failed_or_incomplete_verification_cannot_be_accepted(self):
        valid = {"correct": True, "child_recalled": True, "audit_verified": True,
                 "encoding": {"roundtrip": True}}
        for replacement in [{"correct": False}, {"child_recalled": None},
                            {"audit_verified": 1}, {"encoding": {}}, {"encoding": None}]:
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                checked_report(dict(valid, **replacement))


if __name__ == "__main__":
    unittest.main()
