"""Opt-in end-to-end check: Rust controller talks to actual local model weights."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class RustNeuralTests(unittest.TestCase):
    def test_probe_records_all_controls_and_actual_inference(self):
        executable = Path("target/release/neural.exe" if os.name == "nt" else "target/release/neural")
        result = subprocess.run([str(executable.resolve()), sys.executable,
                                 os.environ["NEURAL_MODEL_PATH"], "probe"],
                                capture_output=True, text=True, encoding="utf-8", timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report.get("runs", [])), 3)
        for run in report["runs"]:
            self.assertEqual(len(run["cases"]), 22)
            self.assertEqual(run["cases"][0]["entity"], "temporary")
            self.assertEqual(run["cases"][-2]["entity"], "temporary")
            self.assertEqual(run["cases"][0]["expected"], "A")
            self.assertEqual(run["cases"][-2]["expected"], "UNKNOWN")
            self.assertTrue(all(c["neural"]["pid"] == report["worker"]["pid"] for c in run["cases"]))
            self.assertTrue(all(c["neural"]["data"]["evaluated_tokens"] > 0 for c in run["cases"]))

    def test_rust_receives_correlated_real_model_results(self):
        executable = Path("target/release/neural.exe" if os.name == "nt" else "target/release/neural")
        result = subprocess.run([str(executable.resolve()), sys.executable,
                                 os.environ["NEURAL_MODEL_PATH"], "preflight"],
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report.get("preflight_passed"), True)
        self.assertEqual(report["worker"]["data"]["load_count"], 1)
        self.assertEqual(report["worker"]["data"]["simulated"], False)
        self.assertGreater(report["preflight"][0]["data"]["evaluated_tokens"], 0)
