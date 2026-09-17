"""Reproducible source inventory, cancellable build, and audited public report."""
import hashlib
import json
import os
import platform
import subprocess
import time
from survival_audit import audit_trial
from survival_process import ROOT, BINARY


def sources():
    core = ROOT.parent / "v2"
    files = [*core.joinpath("src").rglob("*.rs"), core / "Cargo.toml", core / "Cargo.lock",
             *ROOT.glob("survival_*.py"), ROOT / "run_survival.py", ROOT / "server.py",
             *ROOT.joinpath("static").glob("survival.*")]
    return {os.path.relpath(p, ROOT): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def build(folder, cancelled):
    args = ["cargo", "build", "--release", "--locked", "--offline", "--bin", "dna_node"]
    with (folder / "build.stdout.log").open("wb") as out, (folder / "build.stderr.log").open("wb") as err:
        process = subprocess.Popen(args, cwd=ROOT.parent / "v2", stdout=out, stderr=err,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        deadline = time.monotonic() + 180
        try:
            while process.poll() is None:
                if cancelled() or time.monotonic() > deadline:
                    raise ValueError("Build cancelled or timed out")
                time.sleep(0.1)
            if process.returncode:
                raise ValueError("Node build failed; see build.stderr.log")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()


def report(run_id, events, runs, manifest):
    trials = [audit_trial([e for e in events if e["trial"] == i]) for i in range(runs)]
    return {"run_id": run_id, "summary": {"passed": len(trials), "runs": runs, "trials": trials},
            "events": events, "manifest": manifest,
            "scope": "20 independent local processes, loopback TCP, full ciphertext replication; external owner key/root and supervisor. No remote machines or neural inference."}


def manifest(source_hashes):
    return {"sources_sha256": source_hashes, "binary_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            "platform": platform.platform(), "transport": "loopback TCP", "nodes_per_trial": 20}
