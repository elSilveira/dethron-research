import json
import tempfile
import unittest
from pathlib import Path
from survival_probe import run_trial
from survival_audit import audit_trial


class RealProcessTests(unittest.TestCase):
    def test_twenty_real_processes_rebuild_from_one_and_reject_lost_information(self):
        with tempfile.TemporaryDirectory() as temporary:
            events = []
            run_trial(Path(temporary), 3, events.append)
            summary = audit_trial(events)
            self.assertEqual(summary["survival_fraction"], 0.05)
            self.assertEqual(summary["repaired_nodes"], 19)
            self.assertEqual(summary["restart_verified_nodes"], 20)
            self.assertEqual(summary["status"], "PASS")
            self.assertNotIn('"key":', json.dumps(events))
            broken = json.loads(json.dumps(events))
            next(e for e in broken if e["kind"] == "repaired")["data"]["repair"]["object"] = "invented"
            with self.assertRaises(ValueError):
                audit_trial(broken)
            with self.assertRaises(ValueError):
                audit_trial(events[:-1])
            duplicate = json.loads(json.dumps(events))
            targets = next(e for e in duplicate if e["kind"] == "expanded")["data"]["repair"]["targets"]
            targets[1] = targets[0]
            with self.assertRaises(ValueError):
                audit_trial(duplicate)
