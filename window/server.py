"""Loopback-only API and an explicit allowlist of dashboard assets."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit

STATIC = Path(__file__).resolve().parent / "static"
ASSETS = {"/": ("index.html", "text/html"),
          "/style.css": ("style.css", "text/css"),
          "/app.mjs": ("app.mjs", "text/javascript"),
          "/model.mjs": ("model.mjs", "text/javascript"),
          "/views.mjs": ("views.mjs", "text/javascript")}


def create_server(manager, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def local(self):
            hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            origin = self.headers.get("Origin")
            return self.headers.get("Host") in hosts and (
                origin is None or origin in {"http://" + host for host in hosts})

        def reply(self, code, data, kind="application/json", attachment=None):
            body = json.dumps(data).encode() if kind == "application/json" else data
            self.send_response(code)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'")
            if attachment:
                self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if not self.local():
                return self.reply(403, {"error": "Local requests only"})
            path = urlsplit(self.path).path
            if path == "/api/state":
                return self.reply(200, dict(manager.snapshot(), token=self.server.token))
            if path in ("/api/report", "/api/events"):
                state = manager.snapshot()
                if path == "/api/report":
                    if state["status"] != "completed" or state["report"] is None:
                        return self.reply(409, {"error": "No completed report available"})
                    return self.reply(200, state["report"], attachment="tron-report.json")
                data = "".join(json.dumps(e) + "\n" for e in state["events"])
                return self.reply(200, data.encode(), "application/x-ndjson", "tron-events.jsonl")
            if path in ASSETS:
                filename, kind = ASSETS[path]
                try:
                    return self.reply(200, (STATIC / filename).read_bytes(), kind)
                except OSError:
                    return self.reply(404, {"error": "Dashboard asset missing"})
            self.reply(404, {"error": "Not found"})

        def do_POST(self):
            token = self.headers.get("X-Tron-Token", "")
            if not self.local() or not secrets.compare_digest(token, self.server.token):
                return self.reply(403, {"error": "Reload the local dashboard to authorize controls"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1024:
                    return self.reply(413, {"error": "Request must be 1..1024 bytes"})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object")
                if self.path == "/api/start":
                    return self.reply(202, manager.start(data.get("cycles", 3), data.get("delay_ms", 250)))
                if self.path == "/api/stop":
                    return self.reply(202, manager.stop())
                self.reply(404, {"error": "Not found"})
            except (ValueError, UnicodeError) as exc:
                self.reply(400, {"error": str(exc)})
            except RuntimeError as exc:
                self.reply(409, {"error": str(exc)})
            except OSError as exc:
                self.reply(500, {"error": f"Local I/O failed: {exc}"})

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.token = secrets.token_hex(32)
    return server
