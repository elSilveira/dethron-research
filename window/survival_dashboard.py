"""Live storage survival probe with durable evidence and explicit interruption."""
import copy
from datetime import datetime, timezone
import json
import threading
import time
import uuid
from survival_process import ROOT
from survival_probe import run_trial
import survival_report as evidence


class SurvivalManager:
    def __init__(self, results=None):
        self.results = results or ROOT / "results"
        self.lock, self.cancel = threading.RLock(), threading.Event()
        self.thread, self.folder = None, None
        self.state = {"status": "idle", "events": [], "report": None}
        existing = sorted(self.results.glob("survival-*/status.json"))
        if existing:
            self.folder = existing[-1].parent
            try:
                self.state.update(json.loads(existing[-1].read_text(encoding="utf-8")))
                self.state["events"] = [json.loads(line) for line in (self.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
                if self.state["status"] == "completed":
                    saved = json.loads((self.folder / "report.json").read_text(encoding="utf-8"))
                    self.state["report"] = evidence.report(saved["run_id"], self.state["events"], saved["summary"]["runs"], saved["manifest"])
                elif self.state["status"] in ("running", "stopping"):
                    self.state.update(status="interrupted", error="Servidor anterior encerrou antes de concluir; evidências parciais preservadas.", report=None)
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.state.update(status="failed", error=str(error), report=None)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def _save(self):
        public = {k: v for k, v in self.state.items() if k not in ("report", "events")}
        temporary = self.folder / "status.tmp"
        temporary.write_text(json.dumps(public, indent=2), encoding="utf-8")
        temporary.replace(self.folder / "status.json")

    def start(self, runs=3):
        if type(runs) is not int or not 1 <= runs <= 10:
            raise ValueError("Escolha de 1 a 10 execuções")
        with self.lock:
            if self.thread and self.thread.is_alive():
                raise RuntimeError("Um probe de sobrevivência já está ativo")
            run_id = "survival-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
            self.folder = self.results / run_id
            self.folder.mkdir(parents=True, exist_ok=False)
            self.cancel = threading.Event()
            self.state = {"status": "running", "run_id": run_id, "runs": runs, "events": [], "report": None, "error": None}
            self._save()
            self.thread = threading.Thread(target=self._run, args=(self.folder, runs), daemon=True)
            self.thread.start()
            return self.snapshot()

    def stop(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                self.cancel.set()
                self.state["status"] = "stopping"
            return self.snapshot()

    def close(self):
        self.stop()
        if self.thread:
            self.thread.join(timeout=35)

    def _run(self, folder, runs):
        deadline = time.monotonic() + 600
        cancelled = lambda: self.cancel.is_set() or time.monotonic() > deadline
        try:
            source_hashes = evidence.sources()
            evidence.build(folder, cancelled)
            manifest = evidence.manifest(source_hashes)
            (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            with (folder / "events.jsonl").open("x", encoding="utf-8") as log:
                for trial in range(runs):
                    def emit(event):
                        event = dict(event, trial=trial)
                        log.write(json.dumps(event) + "\n")
                        log.flush()
                        with self.lock:
                            self.state["events"].append(event)
                    run_trial(folder / f"trial-{trial}", (trial * 7 + 3) % 20, emit, cancelled)
            if cancelled():
                raise ValueError("Probe interrompido ou prazo excedido")
            if source_hashes != evidence.sources() or manifest != evidence.manifest(source_hashes):
                raise ValueError("Código ou binário mudou durante o probe; execute novamente")
            report = evidence.report(folder.name, self.snapshot()["events"], runs, manifest)
            (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            with self.lock:
                self.state.update(status="completed", report=report)
                self._save()
        except Exception as error:
            with self.lock:
                self.state.update(status="stopped" if self.cancel.is_set() else "failed", error=str(error))
                self._save()
