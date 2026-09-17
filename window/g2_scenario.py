"""Identical 3-contact calendar and native 64 kB fetch limit for each policy."""
import base64
import hashlib
import json
import time

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from g2_lab import Lab

PROFILE = {"version": 1, "payload_bytes": 98304, "parts": 3, "fetch_limit_kb": 64,
           "contacts": ["C", "A", "B"], "fetches_per_contact": 1, "deadline_seconds": 120,
           "relaxed_control_limit_kb": 256, "cases": ["whole", "split", "missing"]}


def run_case(root, mode):
    lab = Lab(root, mode)
    try:
        receiver = lab.start("D")
        recipient = receiver.info
        lab.stop(receiver)
        relays = {name: lab.start(name) for name in "ABC"}
        sender = lab.start("O", "ABC")
        source = sender.info
        content = hashlib.shake_256(b"dethron-g2-profile-v1").digest(PROFILE["payload_bytes"])
        object_id, expires = "f"*32, int(time.time())+1200
        parts = split(content, 3, object_id)
        mapping = {"A": 0, "B": 0 if mode == "missing" else 1, "C": 2}
        inputs = {}
        for name in "ABC":
            body = content if mode == "whole" else encode(parts[mapping[name]])
            inputs[name] = data_envelope(source["destination"], recipient["destination"], body, expires,
                                         object_id if mode == "whole" else None)
        manifest = {"profile": PROFILE, "mode": mode, "source": source, "destination": recipient,
                    "object": parts[0]["manifest"], "expires": expires, "inputs": inputs,
                    "placement": mapping if mode != "whole" else {n: "whole" for n in "ABC"}}
        (root/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        time.sleep(2)
        for relay in relays.values():
            relay.send("announce")
        time.sleep(2)
        packed_bytes = 0
        for name in "ABC":
            sender.send("send", label=name, body=base64.b64encode(encode(inputs[name])).decode(),
                        recipient=recipient, propagation=relays[name].info["propagation"])
            handoff = sender.wait("handoff", label=name, timeout=180)
            packed_bytes += handoff["packed_bytes"]
            lab.record("handoff_only", node=name, packed_bytes=handoff["packed_bytes"])
        before = {}
        for name, relay in relays.items():
            deadline = time.monotonic()+60
            status = relay.status()
            while status["stored"] != 1 and time.monotonic() < deadline:
                time.sleep(.25)
                status = relay.status()
            if status["stored"] != 1:
                raise ValueError("relay did not persist its assigned message")
            before[name] = status["store_bytes"]
        lab.stop(sender)
        sender.home.rename(root/"O.offline")
        for name in "ABC":
            lab.stop(relays[name])
            relays[name] = lab.start(name, generation=1)
            status = relays[name].status()
            if status["stored"] != 1 or status["store_bytes"] != before[name]:
                raise ValueError("relay did not retain bytes across crash")
        lab.record("distribution_complete", relay_bytes=before)
        began = time.monotonic()
        snapshots = []
        for generation, name in enumerate(PROFILE["contacts"], 1):
            receiver = lab.start("D", [name], generation)
            if receiver.info["destination"] != recipient["destination"]:
                raise ValueError("destination identity changed")
            snapshot = lab.fetch(receiver, relays[name], source)
            snapshots.append(snapshot)
            if generation != 3:
                lab.stop(receiver)
        elapsed = time.monotonic()-began
        if elapsed > PROFILE["deadline_seconds"]:
            raise TimeoutError("contact campaign exceeded frozen deadline")
        completed = snapshots[-1]["completed"]
        if completed != (mode == "split"):
            raise ValueError(f"unexpected constrained outcome: {mode} {completed}")
        if mode != "whole":
            expected_counts = [1, 2, 2 if mode == "missing" else 3]
            if [s["objects"][0]["count"] for s in snapshots] != expected_counts:
                raise ValueError("unique part counts do not match contact schedule")
            if any(s["completed"] for s in snapshots[:-1]):
                raise ValueError("assembled before enough information")
        report = {"completed": completed, "contact_seconds": elapsed, "snapshots": snapshots,
                  "relay_store_bytes": sum(before.values()), "submitted_lxmf_bytes": packed_bytes,
                  "interface_tx_bytes_constrained": lab.measure()}
        if mode == "whole":
            report["constrained_completed"] = completed
            lab.record("relaxed_control_begin", limit_kb=256)
            relaxed = lab.fetch(receiver, relays["B"], source, 256)
            if not relaxed["completed"]:
                raise ValueError("whole-object positive control failed")
            report["relaxed_completed"] = True
        lab.record("case_passed", **report)
        return report
    finally:
        lab.close()
