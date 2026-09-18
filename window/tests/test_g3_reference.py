import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('RUN_GATEWAY_G3') == '1', 'real generations campaign opt-in')
class GenerationReferenceTests(unittest.TestCase):
    def test_all_originals_and_supervisors_replaced_and_loss_control(self):
        script = Path(__file__).resolve().parents[1]/'run_g3_probe.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=7200)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report['verdict'], 'g3_scoped_pass')
        self.assertTrue(report['complete']['completed'])
        self.assertFalse(report['missing']['completed'])
        self.assertTrue(report['missing_checkpoint_rejected'])
