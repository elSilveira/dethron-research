import unittest
from pathlib import Path
from run_network import local_config, verify_report


class NetworkLauncherTests(unittest.TestCase):
    def test_accuracy_evidence_distinguishes_rejected_expansion_from_execution_failure(self):
        run = {"failed": 0, "blocked": 0, "completed": 1, "charged_tokens": 8,
               "token_budget": 100, "records": [{"status": "completed"}]}
        report = {"preflight_passed": True, "execution_passed": True,
                  "accuracy": {"execution_passed": True, "expansion_ready": False,
                               "trials": [{"run": run}],
                               "guarded_wave": {"failed": 0, "charged_tokens": 8, "token_budget": 100}}}
        verify_report(report)
        report["accuracy"]["guarded_wave"]["failed"] = 1
        with self.assertRaises(ValueError):
            verify_report(report)

    def test_local_config_explicitly_uses_two_cpu_replicas(self):
        config = local_config(Path("python.exe"), Path("model"), 2, "cpu", 3, 4, True)
        self.assertEqual(len(config["workers"]), 2)
        self.assertEqual(len({w["name"] for w in config["workers"]}), 2)
        self.assertTrue(all(w["device"] == "cpu" for w in config["workers"]))
        self.assertTrue(config["generation_demo"])

    def test_evidence_rejects_partial_or_overbudget_execution(self):
        for report in [{}, {"preflight_passed": True, "execution_passed": False}]:
            with self.assertRaises(ValueError):
                verify_report(report)
        report = {"preflight_passed": True, "execution_passed": True,
                  "task_run": {"failed": 0, "blocked": 0, "completed": 1,
                               "charged_tokens": 101, "token_budget": 100,
                               "records": [{"status": "completed"}]}}
        with self.assertRaises(ValueError):
            verify_report(report)
        report["task_run"]["charged_tokens"] = 99
        verify_report(report)
