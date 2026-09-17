"""Whole-message G0 schedule, with source removed before destination contacts."""
import json
import socket
import time

from gateway_contract import PROFILE, audit_receipt
from gateway_process import Node


def ports(count):
    sockets = [socket.socket() for _ in range(count)]
    try:
        for sock in sockets:
            sock.bind(("127.0.0.1", 0))
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def run(root):
    running = []
    timeline = []
    assigned = dict(zip("OABCD", ports(5)))

    def record(event, **values):
        row = {"event": event, "time": time.time(), **values}
        timeline.append(row)
        with (root / "timeline.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)

    def start(name, contacts=(), generation=0):
        node = Node(root, name, assigned[name], [assigned[x] for x in contacts], generation)
        running.append(node)
        record("start", node=name, generation=generation, pid=node.process.pid, contacts=list(contacts))
        return node

    def stop(node):
        node.kill()
        running.remove(node)
        record("killed", node=node.name, pid=node.process.pid, exit_code=node.process.returncode)

    try:
        destination = start("D")
        recipient = destination.info
        stop(destination)
        relays = {name: start(name) for name in "ABC"}
        origin = start("O", "ABC")
        origin.send("absent")
        absent = origin.wait("absent")
        specs = []
        for name, size in zip("ABC", PROFILE["sizes"]):
            specs.append({"id": f"message-{name}", "size": size, "relay": name,
                          "destination": recipient["destination"], "source": origin.info["destination"],
                          "public_key": origin.info["public_key"]})
        negative = {**specs[0], "id": "absent", "destination": absent["destination"]}
        frozen = {"profile": PROFILE, "ports": assigned, "messages": specs,
                  "negative": negative, "recipient": recipient, "origin": origin.info}
        (root / "manifest.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
        time.sleep(2)
        for relay in relays.values():
            relay.send("announce")
        time.sleep(3)
        for spec in specs + [negative]:
            relay = relays[spec["relay"]]
            origin.send("send", id=spec["id"], size=spec["size"],
                        recipient=absent if spec["id"] == "absent" else recipient,
                        propagation=relay.info["propagation"])
            handoff = origin.wait("handoff", timeout=180, id=spec["id"])
            record("handoff_only", id=spec["id"], at=handoff["time"])
        expected_stores = {"A": 2, "B": 1, "C": 1}
        for name, relay in relays.items():
            status = relay.status()
            # Link handoff precedes asynchronous stamp validation and durable indexing.
            storage_deadline = time.monotonic() + 60
            while status["stored"] != expected_stores[name] and time.monotonic() < storage_deadline:
                time.sleep(.5)
                status = relay.status()
            if status["stored"] != expected_stores[name]:
                raise ValueError(f"store mismatch before crash: {name}: {status}")
            record("store_before_crash", node=name, stored=status["stored"])
        source_info = origin.info
        stop(origin)
        # Archive makes accidental use of the original path fail; no claim of hostile OS isolation.
        origin.home.rename(root / "O.offline")
        for name in "ABC":
            stop(relays[name])
            relays[name] = start(name, generation=1)
            status = relays[name].status()
            if status["stored"] != expected_stores[name]:
                raise ValueError(f"store mismatch after crash: {name}: {status}")
            record("store_after_crash", node=name, stored=status["stored"])
        began = time.monotonic()
        record("distribution_complete", deadline_seconds=PROFILE["deadline_seconds"])
        verified = []
        for generation, spec in enumerate(specs, 1):
            name = spec["relay"]
            destination = start("D", [name], generation)
            if destination.info["destination"] != recipient["destination"]:
                raise ValueError("recipient identity changed across restart")
            time.sleep(2)
            relays[name].send("announce")
            time.sleep(2)
            destination.send("fetch", source=source_info, propagation=relays[name].info["propagation"])
            remaining = PROFILE["deadline_seconds"] - (time.monotonic() - began)
            received = destination.wait("received", timeout=max(.01, remaining), title=spec["id"])
            raw = (destination.home / "receipts" / received["file"]).read_bytes()
            result = audit_receipt(raw, spec)
            result["seconds_after_distribution"] = time.monotonic() - began
            if result["seconds_after_distribution"] > PROFILE["deadline_seconds"]:
                raise TimeoutError("delivery deadline exceeded")
            verified.append(result)
            record("verified_receipt", **result)
            stop(destination)
        while time.monotonic() - began < PROFILE["deadline_seconds"]:
            time.sleep(min(5, PROFILE["deadline_seconds"] - (time.monotonic() - began)))
        negative_store = relays["A"].status()["stored"]
        if negative_store < 1:
            raise ValueError("absent destination message not retained")
        record("negative_observation_complete", seconds=time.monotonic()-began,
               absent_destination_started=False, relay_A_stored=negative_store)
        return {"verdict": "meets_scoped_requirement", "receipts": verified,
                "negative": "no absent endpoint was started; message remained stored",
                "scope": "single-host TCP; whole messages; no G2 or physical mesh evidence"}
    finally:
        for node in reversed(running):
            node.kill()
