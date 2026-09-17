import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('RUN_GATEWAY_V1_RETURN') == '1', 'real receipt return run opt-in')
class ReceiptReturnReferenceTests(unittest.TestCase):
    def test_receipt_returns_without_origin_and_recipient_ever_being_online_together(self):
        script = Path(__file__).resolve().parents[1]/'run_v1_return_probe.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=2400)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report['verdict'], 'v1_return_scoped_pass')
        cases = report['scenarios']
        self.assertEqual(cases['returned']['audit']['route']['proof_via'], 'C')
        self.assertEqual(cases['proof_pending']['audit']['route'], {'proof_via': 'A', 'missing_before': ['C'], 'visits': 2})
        self.assertIsNone(cases['never_completed']['audit']['receipt_at_origin'])
        for case in cases.values():
            self.assertEqual(case['audit']['sessions']['origin_sessions'], 2)
