import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import create_server


class Manager:
    def snapshot(self):
        return {"status": "idle", "events": [], "report": None}

    def start(self, cycles, delay_ms):
        if cycles == 0:
            raise ValueError("Invalid cycles")
        if cycles == 100:
            raise RuntimeError("A run is already active")
        return {"status": "running", "cycles": cycles, "delay_ms": delay_ms}

    def stop(self):
        return {"status": "stopping"}


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(Manager(), 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, data=None, headers=None):
        request = Request(self.base + path, data=data, headers=headers or {})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.read(), response.headers

    def post(self, data, token=True, origin=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Tron-Token"] = self.server.token
        if origin:
            headers["Origin"] = origin
        return self.request("/api/start", json.dumps(data).encode(), headers)

    def test_state_can_be_read_and_valid_controls_start_a_run(self):
        code, body, _ = self.request("/api/state")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["status"], "idle")
        self.assertEqual(json.loads(body)["token"], self.server.token)
        code, body, _ = self.post({"cycles": 3, "delay_ms": 250})
        self.assertEqual(code, 202)
        self.assertEqual(json.loads(body)["status"], "running")

    def test_external_pages_cannot_start_a_process(self):
        self.assertEqual(self.post({"cycles": 3}, token=False)[0], 403)
        self.assertEqual(self.post({"cycles": 3}, origin="https://example.com")[0], 403)

    def test_bad_input_conflicts_and_incomplete_downloads_are_explicit(self):
        self.assertEqual(self.post([])[0], 400)
        self.assertEqual(self.post({"cycles": 0})[0], 400)
        self.assertEqual(self.post({"cycles": 100})[0], 409)
        self.assertEqual(self.request("/api/report")[0], 409)
        code, _, _ = self.request("/api/stop", b"{}", {"X-Tron-Token": self.server.token})
        self.assertEqual(code, 202)

    def test_only_public_static_files_are_served(self):
        for path in ["/../v2/Cargo.toml", "/runner.py", "/results/private.json", "/%2e%2e/runner.py"]:
            self.assertEqual(self.request(path)[0], 404)


if __name__ == "__main__":
    unittest.main()
