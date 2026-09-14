"""Launch with: python window/app.py (no Python packages required)."""
import argparse
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser

from runner import RunManager
from server import create_server

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Live TRON dashboard on your local machine")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="Print URL without opening a browser")
    parser.add_argument("--skip-build", action="store_true", help="Use the existing release adapter")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be 1..65535")
    executable = ROOT / "target" / "release" / ("tron-window.exe" if sys.platform == "win32" else "tron-window")
    if not args.skip_build:
        print("Building the local Rust adapter (using cached dependencies)...", flush=True)
        try:
            subprocess.run(["cargo", "build", "--release", "--locked", "--offline",
                            "--target-dir", str(ROOT / "target")], cwd=ROOT, check=True, timeout=180)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Build failed: {exc}\nInstall Rust 1.89+ and its platform build tools.\n"
                  "For a first dependency download, run: cd window && cargo build --release --locked",
                  file=sys.stderr)
            return 1
    if not executable.is_file():
        print("Adapter missing. Run again without --skip-build.", file=sys.stderr)
        return 1
    manager = RunManager([str(executable)], ROOT / "results")
    try:
        server = create_server(manager, args.port)
    except OSError as exc:
        print(f"Cannot listen on port {args.port}: {exc}. Try --port 8766", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"TRON Window: {url}\nPress Ctrl+C here to stop the server and its worker.", flush=True)
    if not args.no_browser:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
