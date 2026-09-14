"""Build the real probe and preserve reports, code hashes and exploratory comparisons."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import uuid

ROOT = Path(__file__).resolve().parent


def command(args, timeout=120):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=timeout,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        raise RuntimeError(f"Command failed: {args}\n{result.stderr}")
    return result.stdout


def inventory():
    paths = list((ROOT / "src").rglob("*.rs")) + list((ROOT / "tests").glob("*.rs"))
    paths += list((ROOT.parent / "v2" / "src").glob("*.rs"))
    paths += [ROOT / "Cargo.toml", ROOT / "Cargo.lock", Path(__file__).resolve(),
              ROOT.parent / "v2" / "Cargo.toml"]
    return {os.path.relpath(path, ROOT): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def comparison(runs, control):
    paired = []
    for seed in sorted({r["seed"] for r in runs}):
        arms = {r["policy"]: r for r in runs if r["seed"] == seed}
        fixed, adaptive = arms[control], arms["Adaptive"]
        paired.append(100 * (1 - adaptive["total_ns"] / fixed["total_ns"]))
    rng = random.Random(20260914)
    samples = sorted(statistics.mean(rng.choices(paired, k=len(paired))) for _ in range(5000))
    return {"control": control, "mean_paired_time_saving_percent": statistics.mean(paired),
            "exploratory_bootstrap_95_percent_interval": [samples[125], samples[4874]],
            "paired_seed_count": len(paired)}


def main():
    sources = inventory()
    print("Building release probe from the recorded source...", flush=True)
    command(["cargo", "build", "--release", "--locked", "--offline", "--bin", "reorganization"])
    executable = ROOT / "target" / "release" / ("reorganization.exe" if os.name == "nt" else "reorganization")
    print("Checking reconstruction and running 20 paired seeds...", flush=True)
    demo = json.loads(command([str(executable), "demo"]))
    bench = json.loads(command([str(executable), "bench", "20"]))
    if inventory() != sources:
        raise RuntimeError("Sources changed during the run; rerun to obtain a consistent manifest")
    if not demo.get("mechanism_checks_passed"):
        raise RuntimeError("Mechanism checks did not pass")
    runs = bench["runs"]
    summary = {}
    for policy in ["Fixed", "Compiled", "Adaptive"]:
        group = [run for run in runs if run["policy"] == policy]
        summary[policy] = {"correct": sum(r["correct"] for r in group),
                           "attempted": sum(r["attempted"] for r in group),
                           "failures": sum(r["failures"] for r in group),
                           "work_units": sum(r["work_units"] for r in group),
                           "median_run_ms": statistics.median(r["total_ns"] for r in group) / 1e6}
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "source_sha256": sources,
                "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "rustc": command(["rustc", "--version"]).strip(),
                "cargo": command(["cargo", "--version"]).strip(),
                "python": platform.python_version(), "os": platform.platform(),
                "architecture": platform.machine(), "logical_cpus": os.cpu_count(),
                "seeds": list(range(1, 21)), "build": "release, locked, offline"}
    summary["comparisons"] = [comparison(runs, control) for control in ["Fixed", "Compiled"]]
    summary["limits"] = ("Synthetic exact arithmetic; bootstrap intervals are exploratory. "
                         "Work units are proxies. Energy and peak resident memory were not measured. "
                         "This does not complete the broader feasibility protocol.")
    folder = ROOT / "results" / ("reorganization-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
                                 + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    for name, data in [("demo", demo), ("benchmark", bench), ("summary", summary), ("manifest", manifest)]:
        with (folder / f"{name}.json").open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"Evidence: {folder}")


if __name__ == "__main__":
    main()
