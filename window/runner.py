"""Own one real worker process and retain its public event stream."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import threading
import uuid

from protocol import decode_event, checked_report


class RunManager:
    def __init__(self, command, results, timeout=300):
        self.command, self.results, self.timeout = list(command), Path(results), timeout
        self.lock = threading.RLock()
        self.process = self.thread = None
        self.cancel = threading.Event()
        self.state = {"status": "idle", "events": [], "report": None,
                      "error": None, "run_id": None}

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def start(self, cycles, delay_ms):
        if type(cycles) is not int or not 1 <= cycles <= 100:
            raise ValueError("Cycles must be an integer from 1 to 100")
        if type(delay_ms) is not int or not 0 <= delay_ms <= 2000:
            raise ValueError("Step delay must be an integer from 0 to 2000 ms")
        with self.lock:
            if self.state["status"] in ("running", "stopping"):
                raise RuntimeError("A run is already active")
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
            folder = self.results / run_id
            folder.mkdir(parents=True, exist_ok=False)
            self.cancel = threading.Event()
            self.state = {"status": "running", "events": [], "report": None,
                          "error": None, "run_id": run_id,
                          "cycles": cycles, "delay_ms": delay_ms}
            self.thread = threading.Thread(target=self._run, args=(folder, cycles, delay_ms), daemon=True)
            self.thread.start()
            return self.snapshot()

    def stop(self):
        with self.lock:
            if self.state["status"] in ("running", "stopping"):
                self.cancel.set()
                self.state["status"] = "stopping"
                if self.process and self.process.poll() is None:
                    self.process.kill()
            return self.snapshot()

    def close(self):
        self.stop()
        if self.thread:
            self.thread.join(timeout=5)

    def _run(self, folder, cycles, delay_ms):
        expired = threading.Event()
        timer = None
        process = None
        report, error = None, None

        def deadline():
            with self.lock:
                if process and process.poll() is None:
                    expired.set()
                    process.kill()

        try:
            with (folder / "stderr.log").open("w", encoding="utf-8") as stderr:
                with self.lock:
                    process = subprocess.Popen(
                        self.command + [str(cycles), str(delay_ms)],
                        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=stderr,
                        text=True, encoding="utf-8", bufsize=1,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    self.process = process
                    if self.cancel.is_set():
                        process.kill()
                timer = threading.Timer(self.timeout, deadline)
                timer.daemon = True
                timer.start()
                count = 0
                with (folder / "events.jsonl").open("x", encoding="utf-8") as log:
                    for line in process.stdout:
                        if report is not None:
                            raise ValueError("Unexpected event after completion")
                        event = decode_event(line, count)
                        count += 1
                        log.write(json.dumps(event) + "\n")
                        log.flush()
                        with self.lock:
                            self.state["events"].append(event)
                        if event["kind"] == "completed":
                            report = checked_report(event["data"])
                code = process.wait()
                if code != 0:
                    raise RuntimeError(f"Worker exited with code {code}; see stderr.log")
                if report is None:
                    raise RuntimeError("Worker exited without a completed report")
        except Exception as exc:
            # This thread owns the run's terminal state; unexpected errors must fail it too.
            error = str(exc)
        finally:
            if timer:
                timer.cancel()
            if process:
                if process.poll() is None:
                    process.kill()
                process.wait()
                process.stdout.close()
            with self.lock:
                self.process = None
                status = "completed"
                if self.cancel.is_set():
                    status, error = "stopped", None
                elif expired.is_set():
                    status, error = "failed", "Worker exceeded its execution deadline"
                elif error or report is None:
                    status = "failed"
                    error = error or "Worker did not produce a verified report"
                if status != "completed":
                    report = None
                try:
                    if report is not None:
                        (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                    metadata = {"run_id": self.state["run_id"], "status": status,
                                "error": error, "cycles": cycles, "delay_ms": delay_ms,
                                "finished_at": datetime.now(timezone.utc).isoformat()}
                    (folder / "status.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                except OSError as exc:
                    status, error, report = "failed", f"Cannot save evidence: {exc}", None
                self.state.update(status=status, error=error, report=report)
