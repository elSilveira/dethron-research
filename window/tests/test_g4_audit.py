import json
from pathlib import Path
import tempfile
import unittest

try:
    from g4_audit import declared_paths, medium, socket_evidence
except ImportError as exc:  # dethron_gateway.wire needs the pinned RNS/LXMF environment
    raise unittest.SkipTest('requires .venv-gateway') from exc


def launches(scenario, isolated=None):
    flags = [scenario != 'ip']*3 if isolated is None else isolated
    return [{'event': 'launch', 'node': node, 'isolated': flag} for node, flag in zip('AOD', flags)]


def sample(endpoints=(), nodes=None, bridges=(3, 4)):
    return {'event': 'ip_endpoints', 'nodes': {'A': 1, 'D': 2} if nodes is None else nodes,
            'bridges': list(bridges), 'endpoints': list(endpoints)}


class PathTests(unittest.TestCase):
    def test_an_isolated_scenario_refuses_a_node_that_can_still_reach_ip(self):
        self.assertEqual(declared_paths(launches('bridged'), 'bridged')['isolated'], ['A', 'O', 'D'])
        with self.assertRaises(ValueError):
            declared_paths(launches('bridged', [True, True, False]), 'bridged')

    def test_the_ip_baseline_must_really_use_ip(self):
        self.assertEqual(declared_paths(launches('ip'), 'ip')['isolated'], [])
        with self.assertRaises(ValueError):
            declared_paths(launches('ip', [True, True, True]), 'ip')


class SocketEvidenceTests(unittest.TestCase):
    def test_an_endpoint_in_an_isolated_scenario_fails_the_audit(self):
        self.assertEqual(socket_evidence([sample()], 'bridged')['endpoints'], 0)
        with self.assertRaises(ValueError):
            socket_evidence([sample(endpoints=[{'proto': 'TCP'}])], 'bridged')

    def test_an_ip_baseline_without_endpoints_fails_the_audit(self):
        """A tool that sees nothing anywhere would make the isolation claim vacuous."""
        with self.assertRaises(ValueError):
            socket_evidence([sample()], 'ip')
        self.assertEqual(socket_evidence([sample(endpoints=[{'proto': 'TCP'}])], 'ip')['endpoints'], 1)

    def test_inspecting_no_process_is_not_evidence(self):
        with self.assertRaises(ValueError):
            socket_evidence([sample(nodes={})], 'bridged')
        with self.assertRaises(ValueError):
            socket_evidence([sample(bridges=())], 'bridged')

    def test_exactly_one_sample_is_required(self):
        for rows in ([], [sample(), sample()]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                socket_evidence(rows, 'bridged')


class MediumTests(unittest.TestCase):
    def build(self, ledger):
        root = Path(self.temp.name)
        (root/'ledgers').mkdir(exist_ok=True)
        (root/'ledgers'/'dr-b.json').write_text(json.dumps(ledger))
        return root

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_a_removed_medium_may_not_have_carried_anything(self):
        root = self.build({'sent': 0, 'received': 0, 'cut_losses': 53})
        rows = [{'event': 'cut', 'link': 'dr'}]
        self.assertEqual(medium(root, rows, 'dark', 16384)['received_bytes'], 0)
        carried = self.build({'sent': 0, 'received': 10, 'cut_losses': 53})
        with self.assertRaises(ValueError):
            medium(carried, rows, 'dark', 16384)

    def test_a_cut_that_lost_nothing_was_not_a_cut(self):
        root = self.build({'sent': 0, 'received': 32787, 'cut_losses': 0})
        rows = [{'event': 'cut', 'link': 'dr'}, {'event': 'restore', 'link': 'dr'}]
        with self.assertRaises(ValueError):
            medium(root, rows, 'cut', 16384)

    def test_the_object_must_actually_cross_the_medium(self):
        root = self.build({'sent': 0, 'received': 12, 'cut_losses': 0})
        with self.assertRaises(ValueError):
            medium(root, [], 'bridged', 16384)

    def test_undeclared_cuts_are_refused(self):
        root = self.build({'sent': 0, 'received': 32787, 'cut_losses': 0})
        with self.assertRaises(ValueError):
            medium(root, [{'event': 'cut', 'link': 'dr'}], 'bridged', 16384)


if __name__ == '__main__':
    unittest.main()
