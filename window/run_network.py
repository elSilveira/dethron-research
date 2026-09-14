"""Reproducible local/SSH worker-network experiment; no model downloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid
from run_neural import DEFAULT_MODEL, ROOT, hashes, invoke


def local_config(python, model, workers, device, repeats, cases, generation):
    return {"workers": [{"name": f"{device}-{i}", "kind": "local",
                         "python": str(python.resolve()), "model": str(model.resolve()),
                         "device": device} for i in range(workers)],
            "repeats": repeats, "cases": cases, "generation_demo": generation}


def verify_report(report):
    if report.get("preflight_passed") is not True or report.get("execution_passed") is not True:
        raise ValueError("Real-worker preflight or network execution failed")
    runs = [t["run"] for t in report.get("comparison", {}).get("trials", [])]
    runs += [t["run"] for t in report.get("accuracy", {}).get("trials", [])]
    if "accuracy" in report:
        accuracy = report["accuracy"]
        wave = accuracy["guarded_wave"]
        if (accuracy.get("execution_passed") is not True or wave["failed"]
                or wave["charged_tokens"] > wave["token_budget"]):
            raise ValueError("Accuracy harness execution failed")
    runs += [report[k] for k in ("task_run", "generation_demo") if k in report]
    if not runs:
        raise ValueError("No execution evidence")
    for run in runs:
        if (run["failed"] or run["blocked"] or run["completed"] != len(run["records"])
                or any(r["status"] != "completed" for r in run["records"])
                or run["charged_tokens"] > run["token_budget"]):
            raise ValueError("Incomplete or overbudget network run")


def source_hashes():
    sources = hashes()
    sources["run_network.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for path in (ROOT / "tests").glob("*wave*.rs"):
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    path = ROOT / "tests/test_network_launcher.py"
    sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, help="Explicit local/SSH endpoints and optional task DAG")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--workers", type=int, choices=range(1, 17), default=2)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--repeats", type=int, choices=range(1, 9), default=3)
    parser.add_argument("--cases", type=int, choices=range(2, 17), default=4)
    parser.add_argument("--generation-demo", action="store_true")
    parser.add_argument("--experiment", choices=["throughput", "accuracy"], default="throughput")
    args = parser.parse_args()
    python = ROOT / ".venv-neural" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    config = (json.loads(args.config.read_text(encoding="utf-8")) if args.config else
              local_config(python, args.model, args.workers, args.device,
                           args.repeats, args.cases, args.generation_demo))
    if not args.config:
        config["experiment"] = args.experiment
    folder = ROOT / "results" / ("network-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    config_path = folder / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    status = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
    status_path = folder / "status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    sources = source_hashes()
    print(f"Evidence: {folder}", flush=True)
    try:
        invoke(["cargo", "build", "--release", "--locked", "--offline", "--bin", "network"],
               folder / "build.stdout.log", folder / "build.stderr.log", 180)
        executable = ROOT / "target/release" / ("network.exe" if os.name == "nt" else "network")
        manifest = {"sources_sha256": sources,
                    "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                    "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    "os": platform.platform(), "logical_cpus": os.cpu_count()}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("Loading workers and running comparison; progress in worker.stderr.log", flush=True)
        invoke([str(executable), str(config_path)], folder / "report.json", folder / "worker.stderr.log", 1800)
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        verify_report(report)
        if sources != source_hashes():
            raise ValueError("Sources changed during execution")
        summary = report.get("comparison", {}).get("summaries", [])
        if "accuracy" in report:
            summary = [{"split": t["split"], "policy": t["policy"],
                        **{k: t["summary"][k] for k in ("raw_correct", "cases", "accepted_answers",
                            "accepted_wrong", "supported_coverage", "expansion_gate_passed")}}
                       for t in report["accuracy"]["trials"]]
            status["expansion_ready"] = report["accuracy"]["expansion_ready"]
        (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        status["status"] = "completed"
        print(json.dumps(summary, indent=2))
    except Exception as error:
        status.update(status="failed", error=str(error))
        raise
    finally:
        status["finished_at"] = datetime.now(timezone.utc).isoformat()
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
