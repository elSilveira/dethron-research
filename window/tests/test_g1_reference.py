import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get("RUN_GATEWAY_G1") == "1", "real G1 integration opt-in")
class ReferenceTests(unittest.TestCase):
    def test_durable_delivery_requires_authenticated_destination_receipt(self):
        script = Path(__file__).resolve().parents[1] / "run_g1_probe.py"
        result = subprocess.run([sys.executable, str(script)], timeout=300,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report["verdict"], "meets_g1_lab_contract")
        self.assertEqual(report["audit"], "passed")
        self.assertEqual(report["negative"], "expired_without_confirmation")


if __name__ == "__main__":
    unittest.main()
