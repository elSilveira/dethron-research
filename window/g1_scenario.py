"""Real LXMF G1 schedule. The observer never writes a destination mailbox."""
import base64
import hashlib
import json
import time

import RNS

from dethron_gateway.protocol import data_envelope, encode, receipt_envelope
from gateway_process import Node
from gateway_scenario import ports


def run(root):
    assigned = dict(zip("ODX", ports(3)))
    live = []

    def record(event, **values):
        value = {"event": event, "time": time.time(), **values}
        with (root / "timeline.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value) + "\n")
        print(json.dumps(value), flush=True)

    def start(name, contacts=(), generation=0):
        node = Node(root, name, assigned[name], [assigned[c] for c in contacts], generation, "g1_node.py")
        live.append(node)
        record("start", node=name, generation=generation, pid=node.process.pid)
        return node

    def stop(node):
        node.kill()
        live.remove(node)
        if node.process.returncode != 23:
            raise ValueError("crash did not exit as scheduled")
        record("crash", node=node.name, exit_code=23)

    def connect(first, second):
        first.send("trust", peer=second.info)
        second.send("trust", peer=first.info)
        time.sleep(1)
        first.send("announce")
        second.send("announce")
        time.sleep(2)

    def state(node, message_id):
        rows = node.status()["rows"]
        return next(row["state"] for row in rows if row["id"] == message_id and row["kind"] == "data")

    try:
        receiver = start("D")
        sender = start("O", "D")
        source, dest = sender.info, receiver.info
        content = hashlib.shake_256(b"dethron-g1-functional-v1").digest(65536)
        expires = int(time.time())+180
        message = data_envelope(source["destination"], dest["destination"], content, expires)
        absent_identity = RNS.Identity()
        absent = RNS.Destination.hash(absent_identity, "lxmf", "delivery").hex()
        negative_expires = int(time.time())+30
        negative = data_envelope(source["destination"], absent, b"absent", negative_expires)
        manifest = {"version": 1, "source": source, "destination": dest,
                    "message": message, "negative": negative, "limits": {"payload": 1048576,
                    "rows": 128, "logical_bytes": 8388608, "adapter_attempts": 3}}
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for obj in (message, negative):
            sender.send("submit", destination=obj["destination"], payload=obj["payload"],
                        expires=obj["expires"], id=obj["id"])
            sender.wait("queued", id=obj["id"])
        record("queued_before_crash", state=state(sender, message["id"]))
        stop(sender)
        sender = start("O", "D", 1)
        if sender.info["destination"] != source["destination"] or state(sender, message["id"]) != "queued":
            raise ValueError("outbox or identity did not survive")
        connect(sender, receiver)
        sender.send("pump")
        sender.wait("handoff", id=message["id"], timeout=45)
        received = receiver.wait("received", id=message["id"], timeout=45)
        if not received["fresh"] or state(sender, message["id"]) != "handed_off":
            raise ValueError("handoff incorrectly confirmed delivery")
        record("handoff_unconfirmed", state=state(sender, message["id"]))
        stop(receiver)
        receiver = start("D", generation=1)
        if receiver.info["destination"] != dest["destination"]:
            raise ValueError("recipient identity changed")
        # X owns a valid unrelated signing key and attempts a matching-looking receipt.
        attacker = start("X", "O")
        connect(sender, attacker)
        forged = {**receipt_envelope(message), "source": attacker.info["destination"]}
        attacker.send("inject", destination=source["destination"],
                      body=base64.b64encode(encode(forged)).decode())
        sender.wait("rejected", timeout=30)
        if state(sender, message["id"]) == "confirmed":
            raise ValueError("unrelated signer confirmed delivery")
        record("wrong_signer_rejected")
        stop(attacker)
        connect(sender, receiver)
        sender.send("pump")
        sender.wait("handoff", id=message["id"], timeout=45)
        repeated = receiver.wait("received", id=message["id"], timeout=45)
        if repeated["fresh"]:
            raise ValueError("duplicate produced a second logical delivery")
        record("duplicate_after_crash", fresh=False, rows=receiver.status()["rows"])
        receiver.send("pump")
        sender.wait("confirmed", id=message["id"], timeout=45)
        receiver.wait("handoff", id=message["id"], timeout=45)
        malformed = {**message, "payload": base64.b64encode(b"corrupted").decode()}
        sender.send("inject", destination=dest["destination"], body=base64.b64encode(encode(malformed)).decode())
        receiver.wait("rejected", timeout=30)
        record("corrupt_manifest_rejected")
        stop(sender)
        sender = start("O", generation=2)
        if state(sender, message["id"]) != "confirmed":
            raise ValueError("confirmation did not survive crash")
        while time.time() <= negative_expires:
            time.sleep(.25)
        if state(sender, negative["id"]) != "expired":
            raise ValueError("absent destination incorrectly confirmed")
        record("final", source=sender.status()["rows"], destination=receiver.status()["rows"])
        return {"verdict": "meets_g1_lab_contract", "negative": "expired_without_confirmation"}
    finally:
        for node in reversed(live):
            node.kill()
