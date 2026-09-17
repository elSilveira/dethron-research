import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('RUN_GATEWAY_G2_COMPARE') == '1', 'real paired G2 campaign opt-in')
class ComparisonReferenceTests(unittest.TestCase):
    def test_paired_campaign(self):
        script = Path(__file__).resolve().parents[1]/'run_g2_comparison.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=3600)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report['verdict'], 'g2_scoped_pass')
        self.assertEqual(len(report['cases']), 12)
        self.assertTrue(all(r['audit']['passed'] and r['eligible'] for r in report['cases']))
