import unittest
from document_dataset import dataset


class DocumentDatasetTests(unittest.TestCase):
    def test_document_is_substantial_and_loss_removes_both_text_and_facts(self):
        data = dataset()
        self.assertGreater(len(data["document"].split()), 300)
        self.assertEqual(len(data["cases"]), 8)
        lost = next(c for c in data["cases"] if c["id"] == "lost_essential")
        self.assertEqual(lost["expected"], "UNKNOWN")
        self.assertNotIn("Mira", lost["document"])
        self.assertTrue(all(s["target"] != "Mira" for r in lost["routes"] for s in r["sources"]))
        for case in data["cases"]:
            for route in case["routes"]:
                for source in route["sources"]:
                    self.assertIn(source["id"], case["sections"])
