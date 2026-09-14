"""Build and run real Rust/model integration, preserving success or failure evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import uuid

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT.parent / "backup/Deyveloper/deepseek_integration/models/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B/snapshots/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562"


def hashes():
    files = list((ROOT / "src").rglob("*.rs")) + list((ROOT / "neural_worker").glob("*.py"))
    files += list((ROOT / "neural_checks").glob("*.py"))
    files += [ROOT / "Cargo.toml", ROOT / "Cargo.lock", ROOT / "neural-requirements.lock.txt", Path(__file__).resolve()]
    core = ROOT.parent / "v2"
    files += list((core / "src").rglob("*.rs")) + list((core / "tests").glob("*.rs"))
    files += [core / "Cargo.toml", core / "Cargo.lock"]
    return {os.path.relpath(p, ROOT): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def invoke(args, stdout, stderr, timeout):
    with stdout.open("x", encoding="utf-8") as out, stderr.open("x", encoding="utf-8") as err:
        process = subprocess.Popen(args, cwd=ROOT, stdout=out, stderr=err,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                   start_new_session=os.name != "nt")
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError(f"Execution exceeded {timeout} seconds")
        if code:
            raise RuntimeError(f"Execution failed with code {code}; see {stderr.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--mode", choices=["preflight", "probe"], default="probe")
    args = parser.parse_args()
    python = ROOT / ".venv-neural" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise RuntimeError("Neural environment is missing; see NEURAL_INTEGRATION.md")
    folder = ROOT / "results" / ("neural-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    status = {"status": "running", "mode": args.mode, "model": str(args.model.resolve())}
    (folder / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    sources = hashes()
    try:
        print("Building Rust controller...", flush=True)
        invoke(["cargo", "build", "--release", "--locked", "--offline", "--bin", "neural"],
               folder / "build.stdout.log", folder / "build.stderr.log", 120)
        executable = ROOT / "target/release" / ("neural.exe" if os.name == "nt" else "neural")
        print("Loading local model once and executing real inference...", flush=True)
        invoke([str(executable), str(python), str(args.model.resolve()), args.mode],
               folder / "report.json", folder / "worker.stderr.log", 180)
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        if sources != hashes() or report.get("preflight_passed") is not True:
            raise RuntimeError("Source consistency or real-model preflight failed")
        summary = {"worker_pid": report["worker"]["pid"],
                   "model": report["worker"]["data"]["checkpoint"], "runs": []}
        for run in report["runs"]:
            summary["runs"].append({key: run[key] for key in
                                    ("policy", "correct", "neural_correct", "attempted", "wall_seconds", "evaluated_tokens", "spent_units")})
        manifest = {"sources_sha256": sources,
                    "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                    "os": platform.platform(), "logical_cpus": os.cpu_count(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "runtime": report["worker"]["data"]}
        for name, data in [("summary", summary), ("manifest", manifest)]:
            (folder / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        status["status"] = "completed"
        print(json.dumps(summary["runs"], indent=2))
    except Exception as error:
        status.update(status="failed", error=str(error))
        raise
    finally:
        (folder / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(f"Evidence: {folder}")


if __name__ == "__main__":
    main()
