import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import RunManager


SUCCESS = {"correct": True, "child_recalled": True, "audit_verified": True,
           "encoding": {"roundtrip": True}}


def event(sequence, kind, data=None):
    return json.dumps({"schema": 1, "sequence": sequence, "kind": kind,
                       "elapsed_ms": sequence, "data": data or {}})


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def manager(self, script, timeout=5):
        fixture = Path(self.temp.name) / "worker.py"
        fixture.write_text(script, encoding="utf-8")
        manager = RunManager([sys.executable, "-u", str(fixture)],
                             Path(self.temp.name) / "results", timeout=timeout)
        self.addCleanup(manager.close)
        return manager

    def wait_for(self, manager, predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = manager.snapshot()
            if predicate(state):
                return state
            time.sleep(0.01)
        self.fail(f"State did not arrive: {manager.snapshot()}")

    def test_progress_arrives_while_worker_runs_and_can_be_stopped(self):
        manager = self.manager(f"import time\nprint({event(0, 'started')!r}, flush=True)\ntime.sleep(30)")
        manager.start(3, 250)
        self.assertEqual(manager.snapshot()["status"], "running")
        self.wait_for(manager, lambda s: len(s["events"]) == 1)
        with self.assertRaises(RuntimeError):
            manager.start(3, 250)
        manager.stop()
        state = self.wait_for(manager, lambda s: s["status"] == "stopped")
        self.assertIsNone(state["report"])

    def test_success_is_saved_only_after_clean_process_exit(self):
        lines = [event(0, "started"), event(1, "completed", SUCCESS)]
        manager = self.manager("\n".join(f"print({line!r})" for line in lines))
        manager.start(1, 0)
        self.assertNotEqual(manager.snapshot()["status"], "idle")
        state = self.wait_for(manager, lambda s: s["status"] == "completed")
        folder = Path(self.temp.name) / "results" / state["run_id"]
        self.assertEqual(json.loads((folder / "report.json").read_text()), SUCCESS)
        self.assertEqual(len((folder / "events.jsonl").read_text().splitlines()), 2)
        manager.start(1, 0)
        next_state = self.wait_for(manager, lambda s: s["status"] == "completed")
        self.assertNotEqual(next_state["run_id"], state["run_id"])
        self.assertTrue((folder / "report.json").is_file())

    def test_invalid_controls_are_rejected(self):
        manager = self.manager("")
        for cycles, delay in [(0, 0), (101, 0), (True, 0), (1, -1), (1, 2001), (1, "2")]:
            with self.subTest(cycles=cycles, delay=delay), self.assertRaises(ValueError):
                manager.start(cycles, delay)

    def test_crash_or_missing_result_never_becomes_success(self):
        for script in ["raise SystemExit(2)", "", "print('not json')",
                       f"print({event(0, [])!r})",
                       f"print({event(0, 'completed', SUCCESS)!r})\nraise SystemExit(2)",
                       f"print({event(0, 'started')!r})\nprint({event(3, 'completed', SUCCESS)!r})"]:
            with self.subTest(script=script):
                manager = self.manager(script)
                manager.start(1, 0)
                self.assertNotEqual(manager.snapshot()["status"], "idle")
                state = self.wait_for(manager, lambda s: s["status"] == "failed")
                self.assertTrue(state["error"])
                self.assertIsNone(state["report"])
                manager.close()

    def test_stalled_worker_fails_by_deadline(self):
        manager = self.manager("import time\ntime.sleep(30)", timeout=0.15)
        manager.start(1, 0)
        self.assertEqual(manager.snapshot()["status"], "running")
        state = self.wait_for(manager, lambda s: s["status"] == "failed")
        self.assertIn("deadline", state["error"].lower())


if __name__ == "__main__":
    unittest.main()
