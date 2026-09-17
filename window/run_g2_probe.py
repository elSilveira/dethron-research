"""Frozen G2 comparison; all incomplete/error attempts remain in results."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time
import traceback

from g2_audit import audit_case
from g2_scenario import PROFILE, run_case


def main():
    base = Path(__file__).resolve().parent
    root = base/"results"/f"gateway-g2-{time.time_ns()}"
    root.mkdir(parents=True)
    print(f"Artifacts: {root}", flush=True)
    (root/"profile.json").write_text(json.dumps(PROFILE, indent=2))
    files = list(base.glob("g2_*.py"))+list((base/"dethron_gateway").glob("*.py"))
    files += [base/name for name in ("run_g2_probe.py", "gateway_process.py", "gateway_contract.py", "gateway_scenario.py")]
    (root/"sources.json").write_text(json.dumps({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in files}, indent=2))
    versions = {name: importlib.metadata.version(name) for name in ("rns", "lxmf", "cryptography")}
    (root/"environment.json").write_text(json.dumps({"packages": versions, "python": sys.version,
                                                   "platform": platform.platform()}, indent=2))
    report = {}
    try:
        if versions["rns"] != "1.5.4" or versions["lxmf"] != "1.1.1":
            raise ValueError("unexpected reference version")
        for mode in PROFILE["cases"]:
            report[mode] = run_case(root/mode, mode)
            report[mode]["audit"] = audit_case(root/mode)
            (root/"progress.json").write_text(json.dumps(report, indent=2))
        report["verdict"] = "meets_g2_scoped_contract"
        report["interpretation"] = "exact-part composition works under this native fetch cap; no general performance or novelty claim"
    except Exception as exc:
        report.update(verdict="inconclusive", error=repr(exc), traceback=traceback.format_exc())
    (root/"report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0 if report["verdict"] == "meets_g2_scoped_contract" else 1


if __name__ == "__main__":
    raise SystemExit(main())
