import unittest
import copy
from reconstruction_dashboard import validate_events


class EvidenceTests(unittest.TestCase):
    def test_partial_and_fabricated_completion_fail(self):
        for events in ([], [{"kind": "complete"}],
                       [{"kind": "case", "data": {}}] * 4 + [{"kind": "complete"}]):
            with self.assertRaises(ValueError):
                validate_events(events)

    def test_model_mistakes_are_results_not_execution_failures(self):
        events = [{"kind": "worker", "data": {"handshake": {"data": {
            "checkpoint": {"files": {"weights": "hash"}}}}}}]
        for name in ("intact", "lost_a", "lost_essential", "conflict"):
            expected = "Amber" if name in ("intact", "lost_a") else "UNKNOWN"
            events.append({"kind": "case", "data": {"id": name, "dna_correct": True,
                "expected": expected, "model_correct": expected == "UNKNOWN",
                "raw_model": "UNKNOWN", "guarded_output": "UNKNOWN",
                "dna": {"state": "accepted" if expected == "Amber" else "abstained",
                        "conclusion": expected if expected == "Amber" else None},
                "response": {"data": {"evaluated_tokens": 10, "outputs": [{"selected": " UNKNOWN"}]}}}})
        events.append({"kind": "complete"})
        self.assertEqual(validate_events(events)["model_correct"], 2)
        self.assertEqual(validate_events(events)["dna_correct"], 4)
        for field, value in (("model_correct", True), ("expected", "UNKNOWN"),
                             ("raw_model", "Amber"), ("guarded_output", "Amber")):
            changed = copy.deepcopy(events)
            changed[1]["data"][field] = value
            with self.assertRaises(ValueError):
                validate_events(changed)
