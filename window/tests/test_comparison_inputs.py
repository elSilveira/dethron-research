import copy
import unittest
from unittest.mock import patch

from comparison_inputs import MODES, lexical_ids, plan, sentence_text
from document_dataset import dataset


class ComparisonInputsTests(unittest.TestCase):
    def test_lexical_retrieves_question_terms_without_annotations(self):
        sections = {"S1": "Atlas uses Vega as backup repository.",
                    "S2": "Orion belongs to Maple.", "S3": "Vega stores material in Lima."}
        self.assertEqual(lexical_ids(sections, "Atlas backup repository", 1), ["S1"])
        self.assertEqual(lexical_ids(sections, "unmatched", 2), [])

    def test_lexical_ties_are_stable_and_invalid_limit_rejected(self):
        self.assertEqual(lexical_ids({"S2": "Atlas", "S1": "Atlas"}, "Atlas", 1), ["S1"])
        with self.assertRaises(ValueError):
            lexical_ids({"S1": "Atlas"}, "Atlas", 0)

    def test_sentences_keep_full_routes_and_conflict(self):
        cases = {c["id"]: c for c in dataset()["cases"]}
        text = sentence_text(cases["office"])
        for expected in ("[S1] Atlas belongs to team Cedar.", "[S2] Team Cedar is led by Mira.",
                         "[S5] Mira works at the Porto office."):
            self.assertIn(expected, text)
        self.assertIn("Team Birch is led by Nora.", sentence_text(cases["conflict"]))
        self.assertNotIn("[S2]", sentence_text(cases["lost_essential"]))
        self.assertEqual(sentence_text(cases["budget"]), "")

    def test_plan_preserves_historical_prompts_and_balances_positions(self):
        from document_oracle import inputs
        rows = plan()
        self.assertEqual(len(rows), 32)
        for i, case in enumerate(dataset()["cases"]):
            group = rows[i * 4:i * 4 + 4]
            self.assertEqual([r["mode"] for r in group], list(MODES[i % 4:] + MODES[:i % 4]))
            for row in group:
                self.assertNotIn("expected", row["request"])
                if row["mode"] in ("full", "selected"):
                    self.assertEqual(row["request"]["prompts"], inputs(case)[1][row["mode"]]["prompts"])

    def test_expected_labels_cannot_change_candidate_requests(self):
        original = plan()
        altered = copy.deepcopy(dataset())
        for case in altered["cases"]:
            case["expected"] = "POISONED_GABARITO"
        with patch("comparison_inputs.dataset", return_value=altered, create=True):
            self.assertEqual(plan(), original)
