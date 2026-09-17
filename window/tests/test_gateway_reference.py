"""Opt-in real five-process reference experiment (several minutes)."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get("RUN_GATEWAY_G0") == "1", "real reference opt-in")
class GatewayReferenceTests(unittest.TestCase):
    def test_offline_delivery_after_origin_exit_and_relay_crash(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root / "run_gateway_probe.py")],
                                cwd=root, timeout=900, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"verdict": "meets_scoped_requirement"', result.stdout)


if __name__ == "__main__":
    unittest.main()
