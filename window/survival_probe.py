"""Measured process death, persistent restart, and verified automatic repair."""
import json
import time
from survival_process import Fleet, command
from survival_supervisor import reconcile


def run_trial(folder, survivor_slot, emit, cancelled=lambda: False):
    folder.mkdir(parents=True, exist_ok=True)
    fleet = Fleet(folder, cancelled)
    serial = 0
    started = time.monotonic()
    def event(kind, data):
        if cancelled():
            raise ValueError("Probe cancelled")
        emit({"kind": kind, "data": data, "elapsed_seconds": time.monotonic() - started})

    authority = folder / "authority.private.json"
    def repair(donors, targets, owner=authority, expect_failure=False):
        nonlocal serial
        serial += 1
        config = folder / f"repair-{serial}.json"
        config.write_text(json.dumps({"authority": str(owner), "donors": donors, "targets": targets}), encoding="utf-8")
        result = command(["repair", config], folder, f"repair-{serial}")
        if expect_failure:
            return {"exit_code": result.returncode, "error": result.stderr.decode("utf-8"),
                    "stdout_empty": not result.stdout}
        if result.returncode:
            raise ValueError(result.stderr.decode("utf-8"))
        return json.loads(result.stdout)

    try:
        result = command(["genesis", folder / "genesis", authority], folder, "genesis")
        if result.returncode:
            raise ValueError(result.stderr.decode("utf-8"))
        public = json.loads(result.stdout)
        first = fleet.start(0, folder / "genesis")
        event("genesis", {**public, "node": first.hello})
        nodes = [first] + [fleet.start(slot) for slot in range(1, 20)]
        report = repair([first.address], [n.address for n in nodes])
        event("expanded", {"nodes": [n.hello for n in nodes], "repair": report})
        survivor = nodes[survivor_slot]
        previous = survivor.hello
        survivor.stop()
        survivor = fleet.start(survivor_slot, survivor.directory)
        nodes[survivor_slot] = survivor
        event("restarted", {"before": previous, "after": survivor.hello,
                            "verification": repair([survivor.address], [])})
        killed = []
        for node in nodes:
            if node is not survivor:
                node.stop()
                node.directory.rename(node.directory.with_name(node.directory.name + ".unavailable"))
                killed.append({"slot": node.slot, **node.hello, "exit_code": node.process.returncode})
        event("failure_injected", {"killed": killed, "survivor": survivor.hello})
        nodes, cycle = reconcile(nodes, fleet.start, repair)
        event("repaired", cycle)
        survivor.stop()
        remaining = [n for n in nodes if n is not survivor]
        event("survivor_removed", {"node": survivor.hello, "exit_code": survivor.process.returncode,
                                    "verification": repair([remaining[0].address], [n.address for n in remaining])})
        nodes, cycle = reconcile(nodes, fleet.start, repair)
        event("second_repair", cycle)
        before = [n.hello for n in nodes]
        for node in nodes:
            node.stop()
        nodes = [fleet.start(n.slot, n.directory) for n in nodes]
        # Each node is checked independently; no donor can hide an incomplete restart.
        checks = [repair([n.address], []) for n in nodes]
        event("restart_all", {"before": before, "after": [n.hello for n in nodes], "checks": checks})
        wrong = json.loads(authority.read_text(encoding="utf-8"))
        wrong["key"][0] ^= 1
        wrong_path = folder / "wrong-authority.private.json"
        wrong_path.write_text(json.dumps(wrong), encoding="utf-8")
        event("wrong_key", repair([nodes[0].address], [], wrong_path, True))
        lost = []
        for node in nodes:
            for path in node.directory.glob("*.unit"):
                if path.stem != public["root"]:
                    path.rename(path.with_suffix(".lost"))
                    lost.append({"node_id": node.hello["node_id"], "unit": path.stem})
        event("missing_content", {"removed": lost, **repair([n.address for n in nodes[:16]], [], expect_failure=True)})
        event("complete", {"nodes": 20, "survivors_at_failure": 1})
    finally:
        fleet.close()
