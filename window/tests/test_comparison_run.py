import json
from pathlib import Path
import tempfile
import unittest

from run_comparison import experiment


class FailingModel:
    metadata = {"simulated": True, "purpose": "unit-test fixture"}

    def execute(self, request):
        if request["id"] != "warmup":
            raise RuntimeError("fixture model failure")
        return {"evaluated_tokens": 2, "seconds": 0.01}


class ComparisonRunTests(unittest.TestCase):
    def test_failed_generations_are_preserved_and_never_claim_success(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            report = experiment(folder, FailingModel())
            self.assertEqual(report["status"], "completed_with_errors")
            rows = [json.loads(line) for line in (folder / "records.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 32)
            self.assertTrue(all("error" in row for row in rows))
            self.assertEqual(report["summary"]["modes"]["full"]["execution_errors"], 8)
            self.assertTrue((folder / "plan.json").is_file())
            self.assertTrue((folder / "report.json").is_file())

    def test_existing_plan_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "plan.json").write_text("preserved")
            with self.assertRaises(FileExistsError):
                experiment(folder, FailingModel())
            self.assertEqual((folder / "plan.json").read_text(), "preserved")
