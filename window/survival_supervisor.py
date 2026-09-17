"""One bounded observe/repair cycle; caller owns scheduling and process cleanup."""
import time


def reconcile(nodes, spawn, repair):
    started = time.monotonic()
    observations, alive, failed = [], [], []
    for node in nodes:
        try:
            hello = node.health()
            observations.append({"slot": node.slot, "state": "alive", **hello})
            alive.append(node)
        except (OSError, ValueError) as error:
            observations.append({"slot": node.slot, "state": "unavailable", "error": str(error)})
            failed.append(node.slot)
    if not alive:
        raise ValueError("No reachable survivor; repair cannot invent lost content")
    report = None
    replacements = {slot: spawn(slot) for slot in failed}
    if replacements:
        report = repair([n.address for n in alive[:16]], [n.address for n in replacements.values()])
        if report.get("verified_targets") != len(replacements):
            raise ValueError("Replacement readback incomplete")
    return [replacements.get(n.slot, n) for n in nodes], {
        "observations": observations, "failed_slots": failed, "survivors": len(alive),
        "repair": report, "seconds": time.monotonic() - started}
