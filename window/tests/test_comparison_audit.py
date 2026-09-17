import copy
import unittest

from comparison_inputs import plan
from comparison_audit import summarize


def evidence():
    records = []
    for row in plan():
        records.append(dict(row, response={"outputs": [{
            "text": '{"answer":"UNKNOWN","citations":[]}',
            "finish_reason": "eos", "input_tokens": 10,
            "generated_tokens": 1, "token_ids": [1]}],
            "evaluated_tokens": 11, "seconds": 0.1}))
    return records


class ComparisonAuditTests(unittest.TestCase):
    def test_constant_abstention_does_not_count_as_supported_coverage(self):
        result = summarize(evidence())
        for totals in result["modes"].values():
            self.assertEqual(totals["answer_correct"], 3)
            self.assertEqual(totals["supported_accepted"], 0)
            self.assertEqual(totals["valid_abstention"], 3)
            self.assertEqual(totals["cases"], 8)

    def test_missing_duplicate_changed_prompt_and_costs_rejected(self):
        original = evidence()
        variants = [original[:-1], original + original[:1]]
        for key, value in (("case_id", "unknown"), ("evidence", "gabarito")):
            rows = copy.deepcopy(original)
            rows[0][key] = value
            variants.append(rows)
        rows = copy.deepcopy(original)
        rows[0]["request"]["prompts"] = ["Expected answer: Mira"]
        variants.append(rows)
        for key, value in (("evaluated_tokens", 999), ("seconds", float("nan"))):
            rows = copy.deepcopy(original)
            rows[0]["response"][key] = value
            variants.append(rows)
        for rows in variants:
            with self.subTest(rows=rows[0]["case_id"]), self.assertRaises(ValueError):
                summarize(rows)

    def test_truncated_answer_and_incomplete_citations_do_not_pass(self):
        rows = evidence()
        for row in rows:
            if row["case_id"] == "lead":
                row["response"]["outputs"][0]["text"] = '{"answer":"Mira","citations":["S2"]}'
            if row["case_id"] == "budget":
                row["response"]["outputs"][0]["finish_reason"] = "length"
        result = summarize(rows)
        for totals in result["modes"].values():
            self.assertEqual(totals["supported_accepted"], 0)
            self.assertEqual(totals["answer_correct"], 3)
            self.assertEqual(totals["valid_abstention"], 2)
            self.assertEqual(totals["truncated"], 1)

    def test_execution_error_remains_in_denominator(self):
        rows = evidence()
        rows[0].pop("response")
        rows[0]["error"] = "model failed"
        result = summarize(rows)["modes"]["full"]
        self.assertEqual(result["cases"], 8)
        self.assertEqual(result["execution_errors"], 1)
        self.assertIsNone(result["total_evaluated_tokens"])
