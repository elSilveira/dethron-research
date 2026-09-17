"""Owned real processes and bounded loopback requests for the storage probe."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parent
BINARY = ROOT.parent / "v2/target/release" / ("dna_node.exe" if os.name == "nt" else "dna_node")


def command(args, folder, name, timeout=30):
    result = subprocess.run([str(BINARY), *map(str, args)], capture_output=True,
                            timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (folder / f"{name}.stdout.json").write_bytes(result.stdout)
    (folder / f"{name}.stderr.log").write_bytes(result.stderr)
    return result


class Node:
    def __init__(self, slot, directory, ready):
        self.slot, self.directory = slot, directory
        self.log = ready.with_suffix(".log").open("wb")
        self.process = subprocess.Popen([str(BINARY), "serve", str(directory), str(ready)],
            stdin=subprocess.DEVNULL, stdout=self.log, stderr=self.log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise ValueError("Storage process exited during startup")
                try:
                    self.hello = json.loads(ready.read_text(encoding="utf-8"))
                    self.address = self.hello["address"]
                    if self.hello["pid"] != self.process.pid or self.health() != self.hello:
                        raise ValueError("Node handshake identity mismatch")
                    return
                except (FileNotFoundError, json.JSONDecodeError):
                    time.sleep(0.02)
            raise TimeoutError("Storage process startup timed out")
        except BaseException:
            self.stop()
            raise

    def health(self):
        host, port = self.address.split(":")
        with socket.create_connection((host, int(port)), timeout=0.3) as connection:
            connection.sendall(b'{"op":"health"}\n')
            with connection.makefile("rb") as reader:
                response = json.loads(reader.readline(4096))
        if response.get("ok") is not True or response["data"] != self.hello:
            raise ValueError("Node health identity changed")
        return response["data"]

    def stop(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        self.log.close()


class Fleet:
    def __init__(self, folder, cancelled=lambda: False):
        self.folder, self.cancelled, self.nodes, self.serial = folder, cancelled, [], 0

    def start(self, slot, directory=None):
        if self.cancelled():
            raise ValueError("Probe cancelled")
        self.serial += 1
        directory = directory or self.folder / f"node-{slot}-generation-{self.serial}"
        node = Node(slot, directory, self.folder / f"ready-{self.serial}.json")
        self.nodes.append(node)
        return node

    def close(self):
        for node in self.nodes:
            node.stop()
