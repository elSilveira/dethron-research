import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from g3_process import Daemon, alive
except ImportError as exc:  # gateway_contract needs the pinned RNS/LXMF environment
    raise unittest.SkipTest('requires .venv-gateway') from exc

WORKER = str(Path(__file__).resolve().parent/'fixtures'/'g3_echo_daemon.py')
LAUNCH = """
import sys
from pathlib import Path
from g3_process import Daemon
root, worker = Path(sys.argv[1]), sys.argv[2]
node = Daemon(root, 'A', worker)
node.launch(0, [])
print(node.pid)
"""


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        try:
            node = Daemon(self.root, 'A', WORKER)
            if node.handle.exists():
                node.attach()
                node.kill()
        except Exception:
            pass
        self.temp.cleanup()

    def launch_from_a_separate_supervisor(self):
        env = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])}
        result = subprocess.run([sys.executable, '-c', LAUNCH, str(self.root), WORKER],
                                capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        return int(result.stdout.strip().splitlines()[-1])

    def test_node_outlives_the_supervisor_that_started_it(self):
        pid = self.launch_from_a_separate_supervisor()
        self.assertTrue(alive(pid), 'node died with its supervisor')
        successor = Daemon(self.root, 'A', WORKER)
        self.assertEqual(successor.attach()['event'], 'ready')
        self.assertEqual(successor.pid, pid)
        reply = successor.request('status', value='carried')
        self.assertEqual(reply['echo'], 'carried')
        self.assertEqual(reply['pid'], pid)
        successor.kill()
        self.assertFalse(alive(pid))

    def test_attaching_to_a_dead_node_fails_instead_of_pretending(self):
        pid = self.launch_from_a_separate_supervisor()
        Daemon(self.root, 'A', WORKER).attach().get('event')
        node = Daemon(self.root, 'A', WORKER)
        node.attach()
        node.kill()
        with self.assertRaises(ProcessLookupError):
            Daemon(self.root, 'A', WORKER).attach()
        self.assertFalse(alive(pid))

    def test_requests_are_matched_to_their_own_reply(self):
        self.launch_from_a_separate_supervisor()
        node = Daemon(self.root, 'A', WORKER)
        node.attach()
        first = node.request('status', value='one')
        second = node.request('status', value='two')
        self.assertNotEqual(first['rid'], second['rid'])
        self.assertEqual([first['echo'], second['echo']], ['one', 'two'])
        rows = [json.loads(s) for s in node.events.read_text().splitlines()]
        self.assertEqual(rows[0]['event'], 'ready')
        node.kill()


    def test_a_relaunched_node_does_not_replay_old_commands(self):
        self.launch_from_a_separate_supervisor()
        node = Daemon(self.root, 'A', WORKER)
        node.attach()
        node.request('status', value='before')
        node.kill()
        again = Daemon(self.root, 'A', WORKER)
        again.launch(0, [], reuse=True)
        self.assertTrue(alive(again.pid), 'the replayed crash command killed the new incarnation')
        self.assertEqual(again.request('status', value='after')['echo'], 'after')
        rows = [json.loads(s) for s in again.events.read_text().splitlines()]
        self.assertEqual([r.get('echo') for r in rows if r['event'] == 'status'], ['before', 'after'])
        again.kill()


if __name__ == '__main__':
    unittest.main()
