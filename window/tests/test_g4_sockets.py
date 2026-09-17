import subprocess
import sys
import time
import unittest

from g4_sockets import endpoints

LISTENER = """
import os, socket, sys, time
sock = socket.socket(); sock.bind(('127.0.0.1', 0)); sock.listen(1)
print(os.getpid(), sock.getsockname()[1], flush=True)
time.sleep(30)
"""
QUIET = """
import os, sys, time
print(os.getpid(), 0, flush=True)
time.sleep(30)
"""


class SocketEvidenceTests(unittest.TestCase):
    """If this tool could not see a real socket, the G4 isolation claim would be empty."""

    def start(self, script):
        process = subprocess.Popen([sys.executable, '-c', script], stdout=subprocess.PIPE, text=True)
        self.addCleanup(process.kill)
        pid, port = map(int, process.stdout.readline().split())
        return pid, port

    def test_a_listening_socket_is_reported(self):
        pid, port = self.start(LISTENER)
        deadline = time.monotonic()+10
        rows = []
        while time.monotonic() < deadline and not rows:
            rows = endpoints([pid])
            time.sleep(.2)
        self.assertTrue(rows, 'netstat did not report a socket that really exists')
        self.assertTrue(any(row['local'].endswith(f':{port}') for row in rows), rows)

    def test_a_process_without_sockets_reports_none(self):
        pid, _ = self.start(QUIET)
        self.assertEqual(endpoints([pid]), [])

    def test_unrelated_processes_are_not_counted(self):
        listening, _ = self.start(LISTENER)
        quiet, _ = self.start(QUIET)
        time.sleep(1)
        self.assertTrue(endpoints([listening]))
        self.assertEqual(endpoints([quiet]), [])


if __name__ == '__main__':
    unittest.main()
