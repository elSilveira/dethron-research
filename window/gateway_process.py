"""Bounded subprocess lifecycle and immutable event capture for G0."""
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

from gateway_contract import config_text


class Node:
    def __init__(self, root, name, port, contacts, generation=0, worker="gateway_node.py"):
        self.name = name
        self.home = root / name
        config = self.home / "rns"
        config.mkdir(parents=True, exist_ok=True)
        (config / "config").write_text(config_text(port, contacts), encoding="utf-8")
        self.events = queue.Queue()
        self.log = (root / f"{name}-{generation}.jsonl").open("x", encoding="utf-8")
        self.stderr = (root / f"{name}-{generation}.stderr").open("x", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name(worker)), str(self.home), name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
            text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.info = self.wait("ready", timeout=45)
        except Exception:
            self.kill()
            raise

    def _read(self):
        for line in self.process.stdout:
            self.log.write(line)
            self.log.flush()
            try:
                self.events.put(json.loads(line))
            except ValueError:
                self.events.put({"event": "error", "error": line})

    def send(self, action, **values):
        self.process.stdin.write(json.dumps({"action": action, **values}) + "\n")
        self.process.stdin.flush()

    def wait(self, event, timeout=120, **match):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                value = self.events.get(timeout=min(1, max(.01, deadline-time.monotonic())))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError(f"{self.name} exited {self.process.returncode}; inspect stderr")
                continue
            if value["event"] in ("error", "send_failed"):
                raise RuntimeError(f"{self.name}: {value}")
            if value["event"] == event and all(value.get(k) == v for k, v in match.items()):
                return value
        raise TimeoutError(f"{self.name}: {event} {match}")

    def status(self):
        self.send("status")
        return self.wait("status", timeout=10)

    def kill(self):
        if self.process.poll() is None:
            try:
                self.send("crash")
                self.process.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
            self.process.wait(timeout=20)
        self.reader.join(timeout=5)
        self.log.close()
        self.stderr.close()
        self.process.stdin.close()
        self.process.stdout.close()
