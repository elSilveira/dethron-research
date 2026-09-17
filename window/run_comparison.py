"""Run and preserve a local four-mode development comparison."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

from comparison_audit import summarize
from comparison_inputs import plan
from document_dataset import dataset
from run_neural import ROOT, DEFAULT_MODEL, invoke


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def source_hashes():
    names = ("comparison_inputs.py", "comparison_audit.py", "run_comparison.py",
             "document_dataset.py", "document_oracle.py", "run_neural.py")
    paths = [ROOT / name for name in names] + sorted((ROOT / "neural_worker").glob("*.py"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def experiment(folder, runtime):
    before = source_hashes()
    started = time.perf_counter()
    requests = plan()
    preparation_seconds = time.perf_counter() - started
    write_new(folder / "plan.json", {"schema": 1, "dataset": dataset(), "requests": requests,
                                    "scope": "development_only", "sources_sha256": before})
    write_new(folder / "model.json", runtime.metadata)
    warmup = runtime.execute({"schema": 1, "id": "warmup", "op": "generate",
                              "prompts": ["Return the word ready."], "max_new_tokens": 8})
    write_new(folder / "warmup.json", warmup)
    with (folder / "records.jsonl").open("x", encoding="utf-8") as stream:
        for index, item in enumerate(requests):
            row = dict(item)
            try:
                row["response"] = runtime.execute(item["request"])
            except Exception as error:
                row["error"] = f"{type(error).__name__}: {error}"
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            print(f"{index + 1}/32 {item['case_id']} {item['mode']}", flush=True)
    # Re-read persisted raw records; never trust model-supplied assessment flags.
    records = [json.loads(line) for line in (folder / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    summary = summarize(records)
    if before != source_hashes():
        raise ValueError("Sources changed during execution")
    files = ("plan.json", "model.json", "warmup.json", "records.jsonl")
    manifest = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in files}
    report = {"status": "completed_with_errors" if any("error" in r for r in records) else "completed",
              "summary": summary, "artifacts_sha256": manifest, "sources_sha256": before,
              "input_preparation_seconds": preparation_seconds, "warmup": warmup,
              "manual_annotation_cost": None,
              "scope": "Local Python inference; supplied routes, no v2 transport or new extraction validation"}
    write_new(folder / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-folder", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()
    if args.worker_folder:
        from neural_worker.model import LocalModel
        experiment(args.worker_folder, LocalModel(DEFAULT_MODEL, args.device))
        return
    python = ROOT / ".venv-neural" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        raise RuntimeError("Existing neural environment is missing")
    folder = ROOT / "results" / ("comparison-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    print(f"Evidence: {folder}", flush=True)
    write_new(folder / "started.json", {"status": "running", "device": args.device,
                                       "sources_sha256": source_hashes()})
    try:
        invoke([str(python), str(Path(__file__).resolve()), "--worker-folder", str(folder),
                "--device", args.device], folder / "stdout.log", folder / "stderr.log", 600)
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        write_new(folder / "status.json", {"status": report["status"]})
        print(json.dumps(report["summary"]["modes"], indent=2), flush=True)
    except Exception as error:
        write_new(folder / "status.json", {"status": "failed", "error": str(error)})
        raise


if __name__ == "__main__":
    main()
