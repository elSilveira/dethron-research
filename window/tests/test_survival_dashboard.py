import json
import tempfile
import socket
import time
import unittest
from pathlib import Path
from survival_dashboard import SurvivalManager
from test_server import ServerTests


class SurvivalApiTests(ServerTests):
    def test_storage_screen_state_and_incomplete_report_are_explicit(self):
        self.assertEqual(self.request("/survival")[0], 200)
        code, body, _ = self.request("/api/survival/state")
        self.assertEqual(code, 200)
        self.assertIn("token", json.loads(body))
        self.assertEqual(self.request("/api/survival/start", b'{"runs":0}',
                         {"X-Tron-Token": self.server.token})[0], 400)
        self.assertEqual(self.request("/api/survival/start", b'{"runs":1}')[0], 403)


class ManagerTests(unittest.TestCase):
    def test_cancellation_closes_started_service_and_preserves_partial_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = SurvivalManager(Path(tmp))
            manager.start(1)
            try:
                deadline = time.monotonic() + 25
                while not manager.snapshot()["events"] and time.monotonic() < deadline:
                    time.sleep(0.02)
                state = manager.snapshot()
                self.assertTrue(state["events"], state)
                address = state["events"][0]["data"]["node"]["address"]
                manager.stop()
            finally:
                manager.close()
            state = manager.snapshot()
            self.assertEqual(state["status"], "stopped")
            self.assertIsNone(state["report"])
            host, port = address.split(":")
            with self.assertRaises(OSError):
                socket.create_connection((host, int(port)), timeout=0.3)
            self.assertEqual(SurvivalManager(Path(tmp)).snapshot()["status"], "stopped")

    def test_interrupted_runs_remain_inspectable_but_never_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "survival-20260915-test"
            folder.mkdir()
            (folder / "status.json").write_text(json.dumps({"status": "running", "run_id": folder.name}))
            (folder / "events.jsonl").write_text('{"kind":"genesis","trial":0,"data":{}}\n')
            manager = SurvivalManager(Path(tmp))
            state = manager.snapshot()
            self.assertEqual(state["status"], "interrupted")
            self.assertIsNone(state["report"])
            self.assertEqual(len(state["events"]), 1)
            for count in (0, 11, True, "3"):
                with self.assertRaises(ValueError):
                    manager.start(count)
