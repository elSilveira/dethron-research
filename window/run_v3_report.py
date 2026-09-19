"""Turn a collected V3a bench into a verdict.

    window/.venv-gateway/Scripts/python.exe window/run_v3_report.py <bench-folder>

Run it after copying the other machine's folder back, so both are side by side under
the bench. It reads only what is on disk and writes report.json next to it.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from v3_audit import audit


def commit(root):
    try:
        quiet = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        # Git refuses a repository it thinks belongs to someone else, and that refusal
        # would be recorded here as if it were the version of the code under test.
        tree = Path(__file__).resolve().parents[1]
        result = subprocess.run(['git', '-c', f'safe.directory={tree.as_posix()}',
                                 '-C', str(tree), 'log', '--format=%H %s', '-1'],
                                capture_output=True, text=True, timeout=60, creationflags=quiet)
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()[:120]
    except Exception as exc:
        return repr(exc)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1]).resolve()
    report = {'bench': str(root), 'commit': commit(root)}
    try:
        report.update(audit(root))
    except Exception as exc:
        report.update(passed=False, verdict='inconclusive', error=repr(exc),
                      traceback=traceback.format_exc())
    (root/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)
    print(f"\nreport written to {root/'report.json'}", flush=True)
    return 0 if report.get('verdict', '').startswith('v3a') else 1


if __name__ == '__main__':
    raise SystemExit(main())
