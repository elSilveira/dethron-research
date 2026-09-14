"""Explicit protocol test fixture; never used for real-model evidence."""
import json
import os
import sys
import time

print(json.dumps({"kind": "ready", "pid": os.getpid(), "test_double": True}), flush=True)
for line in sys.stdin:
    message = line.strip()
    if message == "hang":
        time.sleep(60)
    elif message == "crash":
        raise SystemExit(3)
    elif message == "oversized":
        print("x" * 65537, flush=True)
    else:
        print(json.dumps({"echo": message, "pid": os.getpid()}), flush=True)
