"""Collect everything needed to diagnose a failed V2 reproduction, into one text file.

Read-only over the artifacts. Re-runs only the fast suite, to name the failures.

    window/.venv-gateway/Scripts/python.exe window/v2_diagnose.py [--no-suite]

--no-suite skips re-running the test suite, when only the failed experiment matters.
Writes window/results/v2-diagnosis-<timestamp>.txt and prints its path.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
QUIET = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def section(out, title):
    out.append('')
    out.append('='*70)
    out.append(title)
    out.append('='*70)


def tool(*command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, creationflags=QUIET)
        return (result.stdout+result.stderr).strip().splitlines()[:3]
    except Exception as exc:
        return [f'not available: {exc!r}']


def latest(pattern):
    folders = sorted((BASE/'results').glob(pattern), key=lambda p: p.stat().st_mtime)
    return folders[-1] if folders else None


def environment(out):
    section(out, 'ENVIRONMENT')
    out.append(f'python: {platform.python_version()} ({sys.executable})')
    out.append(f'platform: {platform.platform()}')
    out.append(f'processor: {platform.processor()}')
    out.append(f'cpu count: {os.cpu_count()}')
    out.append(f'repository: {ROOT} ({len(str(ROOT))} characters)')
    try:
        out.append('packages: '+json.dumps({n: importlib.metadata.version(n)
                                            for n in ('rns', 'lxmf', 'cryptography')}))
    except Exception as exc:
        out.append(f'packages: unreadable {exc!r}')
    out.append('cargo: '+'; '.join(tool('cargo', '--version')))
    out.append('git HEAD: '+'; '.join(tool('git', '-C', str(ROOT), 'log', '--oneline', '-1')))
    if os.name == 'nt':
        out.append('memory/cpu: '+'; '.join(tool('wmic', 'computersystem', 'get', 'TotalPhysicalMemory')))


def fast_suite(out):
    section(out, 'FAST SUITE (re-run now, to name the failures)')
    env = {**os.environ, 'PYTHONPATH': 'window'}
    began = time.monotonic()
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'window/tests'],
                            cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    text = result.stdout+result.stderr
    out.append(f'seconds: {round(time.monotonic()-began, 1)}')
    out.append(text.strip().splitlines()[-1] if text.strip() else '(no output)')
    blocks = re.split(r'\n(?=(?:FAIL|ERROR): )', text)
    named = [b for b in blocks if b.startswith(('FAIL: ', 'ERROR: '))]
    out.append(f'failing tests: {len(named)}')
    for block in named:
        out.append('-'*70)
        out.extend(block.strip().splitlines()[:30])


def node_evidence(out, folder):
    """Per node: what it reported, what it refused, and what Reticulum logged."""
    homes = sorted(p for p in folder.rglob('events.jsonl'))
    out.append('')
    out.append(f'node homes with events: {len(homes)}')
    for events in homes[:12]:
        home = events.parent
        rows = []
        for line in events.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
        kinds = {}
        for row in rows:
            kinds[row.get('event')] = kinds.get(row.get('event'), 0)+1
        out.append('-'*70)
        out.append(f'{home.relative_to(folder)}: {kinds}')
        for row in rows:
            if row.get('event') in ('error', 'rejected', 'refused', 'send_failed', 'direct_failed'):
                out.append('  ! '+json.dumps(row)[:200])
        logfile = home/'rns'/'logfile'
        if logfile.exists():
            lines = logfile.read_text(encoding='utf-8', errors='replace').splitlines()
            notable = [l for l in lines if any(k in l for k in ('Error', 'error', 'Warning', 'failed', 'timeout',
                                                                'Timeout', 'closed', 'No path', 'unreachable'))]
            out.append(f'  rns logfile: {len(lines)} lines, {len(notable)} notable')
            for line in notable[-8:]:
                out.append('    '+line[:190])
        stderr = home/'stderr.log'
        if stderr.exists() and stderr.stat().st_size:
            out.append('  stderr:')
            for line in stderr.read_text(encoding='utf-8', errors='replace').strip().splitlines()[-6:]:
                out.append('    '+line[:190])


def milestone(out, pattern, title):
    section(out, title)
    folder = latest(pattern)
    if folder is None:
        out.append(f'no artifact matching {pattern}')
        return
    out.append(f'artifact: {folder.name}')
    report = folder/'report.json'
    if not report.exists():
        out.append('no report.json (run did not finish)')
        return
    data = json.loads(report.read_text())
    out.append(f"verdict: {data.get('verdict')}")
    if data.get('error'):
        out.append(f"error: {data['error']}")
    if data.get('traceback'):
        out.append('traceback:')
        out.extend(data['traceback'].strip().splitlines()[-25:])
    for key, value in data.items():
        if isinstance(value, dict) and 'phases' in value:
            phases = [p.get('phase') for p in value['phases']]
            out.append(f"{key}: phases completed {phases}, seconds {round(value.get('seconds', 0), 1)}")
        elif isinstance(value, dict) and 'audit' in value:
            out.append(f"{key}: completed={value.get('completed')} seconds={round(value.get('seconds', 0), 1)}")
    node_evidence(out, folder)
    for log in sorted(folder.rglob('phase-*.log'))[:6]:
        lines = log.read_text(encoding='utf-8', errors='replace').strip().splitlines()
        out.append('-'*70)
        out.append(f'{log.relative_to(folder)} (last 12 lines of {len(lines)})')
        out.extend(lines[-12:])
    timeline = folder.rglob('timeline.jsonl')
    for path in list(timeline)[:2]:
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        kinds = {}
        for row in rows:
            kinds[row['event']] = kinds.get(row['event'], 0)+1
        out.append('-'*70)
        out.append(f'{path.relative_to(folder)}: {kinds}')


def main():
    out = []
    out.append(f'V2 diagnosis generated {time.strftime("%Y-%m-%d %H:%M:%S")}')
    environment(out)
    summary = latest('v2-*')
    section(out, 'LAST V2 SUMMARY')
    out.append(str(summary/'summary.json') if summary else 'none found')
    milestone(out, 'gateway-g3-*', 'G3 ARTIFACT (the path that failed)')
    if '--no-suite' not in sys.argv:
        fast_suite(out)
    target = BASE/'results'/f'v2-diagnosis-{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}.txt'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out[:40]))
    print()
    print('FULL DIAGNOSIS WRITTEN TO:')
    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
