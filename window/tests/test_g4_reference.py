import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(os.environ.get('RUN_GATEWAY_G4') == '1', 'real logical independence run opt-in')
class IndependenceReferenceTests(unittest.TestCase):
    def test_delivery_without_the_ip_stack_and_its_negative_controls(self):
        script = Path(__file__).resolve().parents[1]/'run_g4_probe.py'
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=2400)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report['verdict'], 'g4_scoped_pass')
        cases = report['scenarios']
        self.assertTrue(cases['bridged']['completed'])
        self.assertFalse(cases['dark']['completed'])
        self.assertTrue(cases['cut']['completed'])
        self.assertEqual(cases['bridged']['audit']['sockets']['endpoints'], 0)
        self.assertGreater(cases['ip']['audit']['sockets']['endpoints'], 0)
