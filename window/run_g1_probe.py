"""G1 laboratory runner; one unique artifact directory per attempt."""
import hashlib
from contextlib import closing
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys
import time
import traceback

from dethron_gateway.wire import authenticate
from dethron_gateway.protocol import receipt_envelope
from g1_scenario import run


def audit(root):
    manifest = json.loads((root / "manifest.json").read_text())
    expected = manifest["message"]
    with closing(sqlite3.connect(f"file:{(root/'D'/'mailbox.db').as_posix()}?mode=ro", uri=True)) as db:
        received = db.execute("SELECT body,wire FROM messages WHERE direction='in'").fetchall()
    if len(received) != 1 or json.loads(received[0][0]) != expected:
        raise ValueError("missing/duplicate/wrong destination content")
    # Verify historical signatures at a time inside the manifest lifetime; wall-clock expiry is tested live.
    verified = authenticate(received[0][1], bytes.fromhex(manifest["source"]["public_key"]),
                            manifest["destination"]["destination"], expected["expires"]-1)
    if verified != expected:
        raise ValueError("destination wire does not match manifest")
    with closing(sqlite3.connect(f"file:{(root/'O'/'mailbox.db').as_posix()}?mode=ro", uri=True)) as db:
        rows = db.execute("SELECT body,wire,state FROM messages").fetchall()
    confirmed = [r for r in rows if json.loads(r[0])["id"] == expected["id"]]
    if len(confirmed) != 1 or confirmed[0][2] != "confirmed" or json.loads(confirmed[0][0]) != expected:
        raise ValueError("no unique confirmed sender record")
    receipt = authenticate(confirmed[0][1], bytes.fromhex(manifest["destination"]["public_key"]),
                           manifest["source"]["destination"], expected["expires"]-1)
    if receipt != receipt_envelope(expected):
        raise ValueError("receipt obligation mismatch")
    negative = [r for r in rows if json.loads(r[0])["id"] == manifest["negative"]["id"]]
    if (len(negative) != 1 or negative[0][2] != "expired" or negative[0][1]
            or json.loads(negative[0][0]) != manifest["negative"]):
        raise ValueError("negative control has confirmation evidence")
    return "passed"


def main():
    base = Path(__file__).resolve().parent
    root = base / "results" / f"gateway-g1-{time.time_ns()}"
    root.mkdir(parents=True)
    print(f"Artifacts: {root}", flush=True)
    sources = list((base / "dethron_gateway").glob("*.py")) + [base/name for name in
               ("g1_node.py", "g1_scenario.py", "gateway_process.py", "run_g1_probe.py")]
    (root / "sources.json").write_text(json.dumps({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                 for p in sources}, indent=2))
    versions = {name: importlib.metadata.version(name) for name in ("rns", "lxmf", "cryptography")}
    (root / "environment.json").write_text(json.dumps({"python": sys.version, "platform": platform.platform(),
                "packages": versions, "sqlite": sqlite3.sqlite_version}, indent=2))
    try:
        if versions["rns"] != "1.5.4" or versions["lxmf"] != "1.1.1":
            raise ValueError("reference version differs from frozen profile")
        report = run(root)
        report["audit"] = audit(root)
    except Exception as exc:
        report = {"verdict": "inconclusive", "error": repr(exc), "traceback": traceback.format_exc()}
    (root / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0 if report["verdict"] == "meets_g1_lab_contract" else 1


if __name__ == "__main__":
    raise SystemExit(main())
