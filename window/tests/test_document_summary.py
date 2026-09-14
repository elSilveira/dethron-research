import copy
import unittest
from document_summary import summarize


class DocumentSummaryTests(unittest.TestCase):
    def evidence(self):
        cases = [{"id": str(i), "expected": "Mira" if i < 5 else "UNKNOWN"} for i in range(8)]
        events = [{"kind": "document", "data": {"cases": cases}},
                  {"kind": "worker", "data": {"handshake": {"data": {"simulated": False}}}}]
        for case in cases:
            modes = [{"mode": mode, "answer_correct": case["expected"] == "UNKNOWN", "seconds": 1,
                      "assessment": {"answer": "UNKNOWN", "format_ok": True, "accepted": False},
                      "response": {"data": {"evaluated_tokens": 10,
                          "outputs": [{"finish_reason": "eos"}]}}} for mode in ("full", "selected")]
            events.append({"kind": "case", "data": dict(case, dna_correct=True, modes=modes)})
        return events + [{"kind": "complete"}]

    def test_constant_abstention_does_not_inflate_supported_coverage(self):
        summary = summarize(self.evidence())
        self.assertEqual(summary["always_unknown_correct"], 3)
        self.assertEqual(summary["full"]["answer_correct"], 3)
        self.assertEqual(summary["full"]["supported_correct"], 0)
        self.assertEqual(summary["selected"]["accepted"], 0)

    def test_partial_runs_and_changed_scores_cannot_become_completed_evidence(self):
        events = self.evidence()
        with self.assertRaises(ValueError):
            summarize(events[:-1])
        changed = copy.deepcopy(events)
        changed[2]["data"]["modes"][0]["answer_correct"] = True
        with self.assertRaises(ValueError):
            summarize(changed)
