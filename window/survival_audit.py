"""Independent checks against public raw process and reconstruction evidence."""
import hashlib

KINDS = ["genesis", "expanded", "restarted", "failure_injected", "repaired",
         "survivor_removed", "second_repair", "restart_all", "wrong_key", "missing_content", "complete"]


def audit_trial(events):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require([e.get("kind") for e in events] == KINDS, "Incomplete or reordered survival evidence")
    data = {e["kind"]: e["data"] for e in events}
    expected = data["genesis"]["expected_hash"]
    def object_check(report, count):
        text = report.get("object")
        require(isinstance(text, str) and hashlib.sha256(text.encode()).hexdigest() == expected,
                "Reconstructed object does not match independent genesis hash")
        require(report.get("object_hash") == expected and report.get("verified_steps") == 3,
                "Recipe verification mismatch")
        require(report.get("verified_targets") == count and len(report.get("targets", [])) == count,
                "Incomplete target readback")
        require(all(t.get("object_hash") == expected for t in report["targets"]), "Target hash mismatch")
        require(len({t["address"] for t in report["targets"]}) == count
                and len({t["node"]["node_id"] for t in report["targets"]}) == count,
                "Duplicate target evidence cannot represent independent nodes")
    def restarted(before, after):
        require(before["node_id"] == after["node_id"] and before["session"] != after["session"],
                "Persistent identity or fresh process session missing")
    expanded = data["expanded"]
    require(len(expanded["nodes"]) == 20 and len({n["pid"] for n in expanded["nodes"]}) == 20,
            "Expected 20 independent live processes")
    object_check(expanded["repair"], 20)
    restarted(data["restarted"]["before"], data["restarted"]["after"])
    object_check(data["restarted"]["verification"], 0)
    killed = data["failure_injected"]["killed"]
    require(len(killed) == 19 and len({n["slot"] for n in killed}) == 19
            and all(type(n["exit_code"]) is int for n in killed), "Process death not confirmed")
    cycle = data["repaired"]
    require(cycle["survivors"] == 1 and sorted(cycle["failed_slots"]) == sorted(n["slot"] for n in killed),
            "Supervisor detection does not match injected failures")
    object_check(cycle["repair"], 19)
    require(type(data["survivor_removed"]["exit_code"]) is int, "Original survivor still running")
    object_check(data["survivor_removed"]["verification"], 19)
    object_check(data["second_repair"]["repair"], 1)
    restart = data["restart_all"]
    require(len(restart["before"]) == len(restart["after"]) == len(restart["checks"]) == 20,
            "Missing restart evidence")
    for before, after, check in zip(restart["before"], restart["after"], restart["checks"]):
        restarted(before, after)
        object_check(check, 0)
    for kind in ("wrong_key", "missing_content"):
        failure = data[kind]
        require(type(failure["exit_code"]) is int and failure["exit_code"] != 0
                and failure["stdout_empty"] is True and "Missing or invalid recovery unit" in failure["error"],
                "Expected authenticated recovery rejection missing")
    require(len(data["missing_content"]["removed"]) == 20, "Missing content loss evidence")
    return {"status": "PASS", "survival_fraction": 1 / 20, "repaired_nodes": 19,
            "restart_verified_nodes": 20, "object_hash": expected,
            "repair_seconds": cycle["seconds"], "milestones": len(KINDS)}
