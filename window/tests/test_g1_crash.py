import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from dethron_gateway.mailbox import Mailbox
from dethron_gateway.protocol import data_envelope


SCRIPT = """
import json,os,sys
from dethron_gateway.mailbox import Mailbox
path,identity,mode,encoded=sys.argv[1:]
box=Mailbox(path,identity)
message=json.loads(encoded)
if mode=='queue': box.queue(message,10)
else:
    hook=(lambda db: os._exit(23)) if mode=='before_commit' else None
    box.accept_verified(message,b'wire',10,after_inbox=hook)
os._exit(23)
"""


class CrashTests(unittest.TestCase):
    def test_real_crash_before_and_after_commit(self):
        message = data_envelope("a"*32, "b"*32, b"payload", 100)
        with tempfile.TemporaryDirectory() as temp:
            for mode in ("queue", "before_commit", "after_commit"):
                with self.subTest(mode=mode):
                    path = Path(temp) / (mode + ".db")
                    identity = "a"*32 if mode == "queue" else "b"*32
                    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
                    result = subprocess.run([sys.executable, "-c", SCRIPT, str(path), identity,
                                             mode, json.dumps(message)], env=env, timeout=20)
                    self.assertEqual(result.returncode, 23)
                    reopened = Mailbox(path, identity)
                    self.assertEqual(len(reopened.snapshot()), {"queue": 1, "before_commit": 0,
                                                                "after_commit": 2}[mode])


if __name__ == "__main__":
    unittest.main()
