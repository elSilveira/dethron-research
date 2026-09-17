import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('RUN_GATEWAY_V1') == '1', 'real custody run opt-in')
class CustodyReferenceTests(unittest.TestCase):
    def test_proof_of_entry_proof_of_exit_and_pendency(self):
        script = Path(__file__).resolve().parents[1]/'run_v1_probe.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=2400)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report['verdict'], 'v1_custody_scoped_pass')
        cases = report['scenarios']
        self.assertTrue(cases['delivered']['audit']['completed'])
        self.assertEqual(len(cases['delivered']['audit']['entry']), 3)
        self.assertFalse(cases['pending']['audit']['completed'])
        self.assertEqual(cases['pending']['audit']['pendency']['awaiting_contact'], ['A', 'B', 'C'])
        self.assertEqual(cases['discarded']['audit']['pendency']['attested_not_delivered'], ['B'])
        self.assertIn('refusal', cases['fake']['audit'])
