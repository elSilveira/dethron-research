"""Isolated node lifecycle, explicit contacts, and interface counter snapshots."""
import json
import time

from gateway_process import Node
from gateway_scenario import ports


class Lab:
    def __init__(self, root, mode):
        self.root, self.mode = root, mode
        self.ports = dict(zip("OABCD", ports(5)))
        self.live, self.retired_tx = [], 0
        root.mkdir()

    def record(self, event, **values):
        row = {"event": event, "time": time.time(), **values}
        with (self.root/"timeline.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row)+"\n")
        print(json.dumps({"case": self.mode, **row}), flush=True)

    def start(self, name, contacts=(), generation=0):
        home = self.root/name
        home.mkdir(exist_ok=True)
        (home/"settings.json").write_text(json.dumps({"mode": self.mode, "limit_kb": 64}))
        node = Node(self.root, name, self.ports[name], [self.ports[c] for c in contacts], generation, "g2_node.py")
        self.live.append(node)
        self.record("start", node=name, generation=generation, contacts=list(contacts), pid=node.process.pid)
        return node

    def stop(self, node):
        status = node.status()
        node.kill()
        self.live.remove(node)
        if node.process.returncode != 23:
            raise ValueError("unexpected crash result")
        self.retired_tx += status["metrics"]["tx"]
        self.record("crash", node=node.name, exit_code=23, status=status)

    def measure(self):
        return self.retired_tx + sum(node.status()["metrics"]["tx"] for node in self.live)

    def fetch(self, destination, relay, source, limit=64):
        time.sleep(1)
        relay.send("announce")
        time.sleep(2)
        destination.send("fetch", source=source, propagation=relay.info["propagation"], limit_kb=limit)
        destination.wait("ack", action="fetch", timeout=15)
        deadline = time.monotonic()+40
        while time.monotonic() < deadline:
            status = destination.status()
            if status["sync"] == 7:
                self.record("fetch_complete", relay=relay.name, limit_kb=limit, receiver=status["receiver"])
                return status["receiver"]
            if status["sync"] >= 240:
                raise ValueError(f"native fetch failure: {status['sync']}")
            time.sleep(.25)
        raise TimeoutError("native sync did not complete")

    def close(self):
        for node in reversed(self.live):
            node.kill()
        self.live.clear()
