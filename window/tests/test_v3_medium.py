"""A non-IP claim is only worth what the auditor refuses to pass.

The claim of V3c is not that a serial link was configured. It is that the recipient had
no other way to reach anything, so an object that arrived crossed a link carrying no IP.
That claim dies the moment the recipient also holds an IP interface, and these tests
exist to prove the auditor notices.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v3_audit import distinct_machines, medium
from v3_executor import config_text


def bench(tmp, interfaces):
    root = Path(tmp)
    config = root/'beta'/'D'/'rns'
    config.mkdir(parents=True, exist_ok=True)
    (config/'config').write_text(interfaces, encoding='utf-8')
    return root


PLAN = {'machines': {'beta': {'steps': [{'action': 'launch', 'args': {'contacts': []}}]}}}
SERIAL = {'medium': 'serial'}


class MediumTests(unittest.TestCase):
    def test_a_serial_only_recipient_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = bench(tmp, config_text(45812, [], {'port': 'COM7', 'speed': 115200, 'only': True}))
            facts = medium(root, PLAN, SERIAL)
            self.assertEqual(facts['interfaces'], ['Serial'])
            self.assertEqual(facts['port'], 'COM7')
            self.assertFalse(facts['carries_ip'])

    def test_a_recipient_that_also_listens_on_tcp_is_refused(self):
        """The interface it never used is still a path it had."""
        with tempfile.TemporaryDirectory() as tmp:
            root = bench(tmp, config_text(45812, [], {'port': 'COM7', 'speed': 115200}))
            with self.assertRaises(ValueError) as caught:
                medium(root, PLAN, SERIAL)
            self.assertIn('could have crossed IP', str(caught.exception))

    def test_a_recipient_dialling_out_over_tcp_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = bench(tmp, config_text(45812, ['192.168.1.9:45810'], None))
            with self.assertRaises(ValueError):
                medium(root, PLAN, SERIAL)

    def test_a_schedule_that_asked_for_contacts_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = bench(tmp, config_text(45812, [], {'port': 'COM7', 'only': True}))
            plan = {'machines': {'beta': {'steps': [
                {'action': 'launch', 'args': {'contacts': ['192.168.1.9:45810']}}]}}}
            with self.assertRaises(ValueError) as caught:
                medium(root, plan, SERIAL)
            self.assertIn('IP contacts', str(caught.exception))

    def test_a_missing_configuration_proves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                medium(Path(tmp), PLAN, SERIAL)
            self.assertIn('cannot be read', str(caught.exception))

    def test_an_ip_bench_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = medium(Path(tmp), PLAN, {'medium': 'ip', 'relay_host': '192.168.1.9'})
            self.assertEqual(facts['declared'], 'ip')


class SerialDistinctnessTests(unittest.TestCase):
    """A serial bench has no relay address, so distinctness has to come from elsewhere."""

    def hosts(self, tmp, alpha, beta):
        root = Path(tmp)
        for machine, one in (('alpha', alpha), ('beta', beta)):
            (root/machine).mkdir(parents=True, exist_ok=True)
            (root/machine/'host.json').write_text(json.dumps(one), encoding='utf-8')
        return root, [{'machine': 'alpha'}, {'machine': 'beta'}]

    def test_distinct_names_and_no_shared_address_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, reports = self.hosts(tmp, {'hostname': 'ALPHA', 'addresses': ['192.168.1.9']},
                                       {'hostname': 'BETA', 'addresses': ['192.168.1.40']})
            facts = distinct_machines(root, SERIAL, reports)
            self.assertTrue(facts['evidenced'])
            self.assertIsNone(facts['relay_host'])

    def test_one_shared_address_means_one_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, reports = self.hosts(tmp, {'hostname': 'ALPHA', 'addresses': ['192.168.1.9']},
                                       {'hostname': 'BETA', 'addresses': ['192.168.1.9']})
            with self.assertRaises(ValueError) as caught:
                distinct_machines(root, SERIAL, reports)
            self.assertIn('this is one machine', str(caught.exception))

    def test_the_same_hostname_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, reports = self.hosts(tmp, {'hostname': 'SAME', 'addresses': ['192.168.1.9']},
                                       {'hostname': 'SAME', 'addresses': ['192.168.1.40']})
            with self.assertRaises(ValueError):
                distinct_machines(root, SERIAL, reports)

    def test_without_host_files_nothing_is_evidenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = distinct_machines(Path(tmp), SERIAL, [{'machine': 'alpha'}, {'machine': 'beta'}])
            self.assertFalse(facts['evidenced'])


if __name__ == '__main__':
    unittest.main()


class PreflightTests(unittest.TestCase):
    """A port that is right on one machine can be wrong on the other, and the bench that
    declared it could not have known. The machine that has to use it checks it."""

    def agent(self, tmp, port):
        from v3_agent import Agent
        from v3_bench import build
        root = Path(tmp)
        build(root, serial={'alpha': 'COM3', 'beta': port})
        return Agent(root, 'beta')

    def test_a_port_this_machine_does_not_have_is_refused_before_the_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = self.agent(tmp, 'COM_DOES_NOT_EXIST')
            with self.assertRaises(ValueError) as caught:
                agent.load()
            self.assertIn('COM_DOES_NOT_EXIST', str(caught.exception))
            self.assertIn('really has', str(caught.exception))

    def test_an_ip_bench_needs_no_serial_port(self):
        from v3_agent import Agent
        from v3_bench import build
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build(root, relay_host='192.168.1.9')
            self.assertEqual(Agent(root, 'beta').preflight(
                json.loads((root/'control'/'plan.json').read_text())['machines']['beta']), [])
