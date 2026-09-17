"""Re-read evidence after all candidate processes have terminated."""
import json
from pathlib import Path
import sys

from gateway_contract import audit_receipt


def check_schedule(rows):
    stops = [r for r in rows if r["event"] == "killed" and r.get("node") == "O"]
    distributions = [r for r in rows if r["event"] == "distribution_complete"]
    receipts = [r for r in rows if r["event"] == "verified_receipt"]
    if len(stops) != 1 or stops[0].get("exit_code") != 23 or len(distributions) != 1:
        raise ValueError("missing origin crash or distribution evidence")
    cutoff = stops[0]["time"]
    began = distributions[0]["time"]
    if cutoff > began or len(receipts) != 3 or any(r["time"] < began for r in receipts):
        raise ValueError("invalid delivery sequence")
    if any(r["event"] == "start" and r.get("node") == "O" and r["time"] > cutoff for r in rows):
        raise ValueError("origin restarted")
    for name in "ABC":
        before = [r["stored"] for r in rows if r["event"] == "store_before_crash" and r["node"] == name]
        after = [r["stored"] for r in rows if r["event"] == "store_after_crash" and r["node"] == name]
        if before != [2 if name == "A" else 1] or after != before:
            raise ValueError("missing relay persistence evidence")
    return True


def check_absent_store(path, destination):
    matches = [p.name for p in path.iterdir() if p.is_file() and p.read_bytes()[:16].hex() == destination]
    if len(matches) != 1:
        raise ValueError("absent destination does not have exactly one retained message")
    return matches[0]


def audit_archive(root):
    manifest = json.loads((root / "manifest.json").read_text())
    rows = [json.loads(line) for line in (root / "timeline.jsonl").read_text().splitlines()]
    check_schedule(rows)
    evidence = list((root / "D" / "receipts").glob("*.lxmf"))
    if len(evidence) != len(manifest["messages"]):
        raise ValueError("missing or unexpected receiver artifact")
    verified = []
    for spec in manifest["messages"]:
        matches = []
        for path in evidence:
            try:
                matches.append(audit_receipt(path.read_bytes(), spec))
            except ValueError:
                pass
        if len(matches) != 1:
            raise ValueError(f"no unique valid receiver artifact for {spec['id']}")
        verified.extend(matches)
    retained = check_absent_store(root / "A" / "lxmf" / "messagestore",
                                  manifest["negative"]["destination"])
    observations = [r for r in rows if r["event"] == "negative_observation_complete"]
    if len(observations) != 1 or observations[0]["seconds"] < manifest["profile"]["deadline_seconds"]:
        raise ValueError("negative observation too short")
    return {"receipts": verified, "retained_absent_message": retained,
            "audit": "passed", "trust": "local harness and its event timestamps"}


if __name__ == "__main__":
    print(json.dumps(audit_archive(Path(sys.argv[1])), indent=2))
