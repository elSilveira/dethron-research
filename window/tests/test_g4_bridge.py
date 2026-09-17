import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest

BRIDGE = str(Path(__file__).resolve().parents[1]/'g4_bridge.py')


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.channel = self.root/'channel'
        self.channel.mkdir()
        self.ends = {side: self.start(side) for side in ('a', 'b')}

    def start(self, side):
        process = subprocess.Popen([sys.executable, BRIDGE, str(self.channel), side,
                                    str(self.root/f'{side}.ledger')],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.addCleanup(self.stop, process)
        received = queue.Queue()
        threading.Thread(target=lambda: [received.put(process.stdout.read1(4096)) for _ in iter(int, 1)],
                         daemon=True).start()
        return process, received

    def stop(self, process):
        process.kill()
        process.wait(timeout=10)

    def read(self, side, timeout=5):
        _, received = self.ends[side]
        deadline, data = time.monotonic()+timeout, b''
        while time.monotonic() < deadline:
            try:
                data += received.get(timeout=.1)
            except queue.Empty:
                if data:
                    return data
        return data

    def write(self, side, payload):
        process, _ = self.ends[side]
        process.stdin.write(payload)
        process.stdin.flush()

    def test_bytes_cross_in_both_directions(self):
        self.write('a', b'from-a')
        self.assertEqual(self.read('b'), b'from-a')
        self.write('b', b'from-b')
        self.assertEqual(self.read('a'), b'from-b')

    def test_removing_the_channel_stops_delivery_and_restoring_resumes_it(self):
        self.write('a', b'before')
        self.assertEqual(self.read('b'), b'before')
        moved = self.root/'channel-removed'
        for _ in range(20):
            try:
                self.channel.rename(moved)
                break
            except OSError:
                time.sleep(.2)
        else:
            self.fail('could not remove the medium')
        self.write('a', b'during-cut')
        self.assertEqual(self.read('b', timeout=2), b'')
        moved.rename(self.channel)
        self.write('a', b'after')
        self.assertEqual(self.read('b'), b'after')

    def test_the_ledger_counts_what_the_medium_carried(self):
        self.write('a', b'x'*1024)
        self.assertEqual(self.read('b'), b'x'*1024)
        time.sleep(.5)
        sent = json.loads((self.root/'a.ledger').read_text())
        got = json.loads((self.root/'b.ledger').read_text())
        self.assertEqual(sent['sent'], 1024)
        self.assertEqual(got['received'], 1024)
        self.assertEqual(sent['cut_losses'], 0)


if __name__ == '__main__':
    unittest.main()
