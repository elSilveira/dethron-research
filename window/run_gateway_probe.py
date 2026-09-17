"""Run using .venv-gateway/Scripts/python.exe; artifacts are local and contain keys."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time
import traceback

from gateway_contract import PROFILE
from gateway_archive import audit_archive
from gateway_scenario import run


def main():
    root = Path(__file__).resolve().parent / "results" / f"gateway-g0-{time.time_ns()}"
    root.mkdir(parents=True)
    print(f"Artifacts: {root}", flush=True)
    versions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    (root / "environment.json").write_text(json.dumps({"packages": versions,
        "python": sys.version, "platform": platform.platform(), "profile": PROFILE}, indent=2))
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in Path(__file__).parent.glob("gateway_*.py")}
    source_hashes[Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root / "sources.json").write_text(json.dumps(source_hashes, indent=2))
    try:
        for name, version in PROFILE["reference"].items():
            if importlib.metadata.version(name) != version:
                raise ValueError(f"unexpected {name} version")
        report = run(root)
        report["archive_audit"] = audit_archive(root)
    except Exception as exc:
        report = {"verdict": "inconclusive", "error": repr(exc), "traceback": traceback.format_exc()}
    (root / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0 if report["verdict"] == "meets_scoped_requirement" else 1


if __name__ == "__main__":
    raise SystemExit(main())
