"""Live, file-backed evidence for the real-model reconstruction probe."""
from datetime import datetime, timezone
import hashlib
import json
import os
import threading
import uuid
from run_neural import ROOT, DEFAULT_MODEL, hashes, invoke


def validate_events(events):
    if any(e.get("kind") == "document" for e in events):
        from document_summary import summarize
        return summarize(events)
    workers = [e["data"] for e in events if e.get("kind") == "worker"]
    rows = [e["data"] for e in events if e.get("kind") == "case"]
    if (not events or events[-1].get("kind") != "complete" or len(workers) != 1
            or not workers[0].get("handshake", {}).get("data", {}).get("checkpoint", {}).get("files")
            or [r.get("id") for r in rows] != ["intact", "lost_a", "lost_essential", "conflict"]):
        raise ValueError("Incomplete real-worker evidence")
    for row in rows:
        expected = "Amber" if row["id"] in ("intact", "lost_a") else "UNKNOWN"
        dna = row.get("dna", {})
        raw = row.get("raw_model")
        outputs = row.get("response", {}).get("data", {}).get("outputs", [])
        selected = outputs[0].get("selected") if len(outputs) == 1 else None
        guarded = raw if dna.get("state") == "accepted" and raw == dna.get("conclusion") else "UNKNOWN"
        if (row.get("dna_correct") is not True or type(row.get("model_correct")) is not bool
                or row.get("expected") != expected
                or (dna.get("conclusion") or "UNKNOWN") != expected
                or dna.get("state") != ("accepted" if expected == "Amber" else "abstained")
                or row["model_correct"] != (raw == expected)
                or raw not in ("Amber", "Violet", "UNKNOWN")
                or not isinstance(selected, str) or selected.strip() != raw
                or row.get("guarded_output") != guarded
                or row.get("response", {}).get("data", {}).get("evaluated_tokens", 0) <= 0):
            raise ValueError("Invalid reconstruction evidence")
    return {"dna_correct": sum(r["dna_correct"] for r in rows),
            "model_correct": sum(r["model_correct"] for r in rows), "cases": len(rows)}


def source_hashes():
    result = hashes()
    for path in [ROOT / "reconstruction_dashboard.py", ROOT / "server.py",
                 ROOT / "document_dataset.py", ROOT / "document_summary.py",
                 *ROOT.joinpath("static").glob("reconstruction.*")]:
        result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


class ReconstructionManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.folder = None
        self.state = {"status": "idle", "events": [], "report": None}

    def snapshot(self):
        with self.lock:
            state = dict(self.state)
            state["events"] = []
            if self.folder and (self.folder / "events.jsonl").exists():
                for line in (self.folder / "events.jsonl").read_text(encoding="utf-8").splitlines():
                    try:
                        state["events"].append(json.loads(line))
                    except json.JSONDecodeError:
                        break  # The worker may be writing its final line.
            return state

    def start(self, device, experiment="routes"):
        if experiment not in ("routes", "document"):
            raise ValueError("Choose routes or document")
        if device not in ("cpu", "cuda"):
            raise ValueError("Choose cpu or cuda")
        with self.lock:
            if self.state["status"] == "running":
                raise RuntimeError("A reconstruction run is already active")
            python = ROOT / ".venv-neural" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if not python.is_file() or not DEFAULT_MODEL.is_dir():
                raise ValueError("Local model or neural environment missing; see NEURAL_INTEGRATION.md")
            run_id = "reconstruction-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
            self.folder = ROOT / "results" / run_id
            self.folder.mkdir(parents=True, exist_ok=False)
            config = {"workers": [{"name": device, "kind": "local", "device": device,
                                    "python": str(python), "model": str(DEFAULT_MODEL)}]}
            config["experiment"] = experiment
            if experiment == "document":
                from document_dataset import dataset
                config["dataset"] = dataset()
            (self.folder / "config.json").write_text(json.dumps(config), encoding="utf-8")
            self.state = {"status": "running", "run_id": run_id, "report": None, "error": None}
            self._save()
            threading.Thread(target=self._run, args=(self.folder,), daemon=True).start()
            return self.snapshot()

    def _save(self):
        (self.folder / "status.json").write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _run(self, folder):
        try:
            sources = source_hashes()
            invoke(["cargo", "build", "--release", "--locked", "--offline", "--bin", "reconstruction_live"],
                   folder / "build.stdout.log", folder / "build.stderr.log", 180)
            binary = ROOT / "target/release" / ("reconstruction_live.exe" if os.name == "nt" else "reconstruction_live")
            manifest = {"sources_sha256": sources, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                        "config_sha256": hashlib.sha256((folder / "config.json").read_bytes()).hexdigest()}
            (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            invoke([str(binary), str(folder / "config.json")],
                   folder / "events.jsonl", folder / "worker.stderr.log", 300)
            events = self.snapshot()["events"]
            summary = validate_events(events)
            if sources != source_hashes():
                raise ValueError("Sources changed during execution; rerun")
            report = {"run_id": folder.name, "summary": summary, "events": events, "manifest": manifest,
                      "scope": "Real local model; controlled facts; see requests for ranking or generated JSON mode"}
            (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            with self.lock:
                self.state.update(status="completed", report=report)
                self._save()
        except Exception as error:
            with self.lock:
                self.state.update(status="failed", error=str(error))
                self._save()
