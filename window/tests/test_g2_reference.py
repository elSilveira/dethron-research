import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get("RUN_GATEWAY_G2") == "1", "real G2 campaign opt-in")
class G2ReferenceTests(unittest.TestCase):
    def test_complementary_contacts_and_matched_native_transfer_limit(self):
        script = Path(__file__).resolve().parents[1] / "run_g2_probe.py"
        result = subprocess.run([sys.executable, str(script)], timeout=1200,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report["verdict"], "meets_g2_scoped_contract")
        self.assertTrue(report["split"]["completed"])
        self.assertFalse(report["missing"]["completed"])
        self.assertFalse(report["whole"]["constrained_completed"])
        self.assertTrue(report["whole"]["relaxed_completed"])


if __name__ == "__main__":
    unittest.main()
