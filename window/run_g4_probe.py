"""Frozen G4 run: one baseline on the IP stack and three scenarios that cannot reach it."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

from g3_process import QUIET, alive
from g4_audit import audit
from g4_contract import PROFILE, expected_delivery
from g4_scenario import run_case


def sweep(root):
    """Nodes and the bridges they spawned must not outlive the experiment."""
    stopped = []
    for handle in root.rglob('daemon.json'):
        stopped.append(json.loads(handle.read_text())['pid'])
    for ledger in root.rglob('ledgers/*.json'):
        try:
            stopped.append(json.loads(ledger.read_text())['pid'])
        except (OSError, ValueError, KeyError):
            continue
    killed = []
    for pid in set(stopped):
        if alive(pid):
            subprocess.run(['taskkill', '/F', '/PID', str(pid)] if os.name == 'nt'
                           else ['kill', '-9', str(pid)], capture_output=True, creationflags=QUIET)
            killed.append(pid)
    return killed


def main():
    base = Path(__file__).resolve().parent
    root = base/'results'/f'gateway-g4-{time.time_ns()}'
    root.mkdir(parents=True)
    print(f'Artifacts: {root}', flush=True)
    files = list(base.glob('g4_*.py'))+list((base/'dethron_gateway').glob('*.py'))
    files += [base/name for name in ('run_g4_probe.py', 'g3_process.py', 'g3_node.py',
                                     'g2_receiver.py', 'gateway_scenario.py')]
    (root/'sources.json').write_text(json.dumps({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                 for p in files}, indent=2))
    versions = {name: importlib.metadata.version(name) for name in ('rns', 'lxmf', 'cryptography')}
    (root/'environment.json').write_text(json.dumps({'packages': versions, 'python': sys.version,
                                                     'platform': platform.platform()}, indent=2))
    (root/'profile.json').write_text(json.dumps(PROFILE, indent=2))
    report = {'scenarios': {}}
    try:
        if versions['rns'] != '1.5.4' or versions['lxmf'] != '1.1.1':
            raise ValueError('unexpected reference versions')
        for scenario in PROFILE['scenarios']:
            home = root/scenario
            home.mkdir()
            began = time.monotonic()
            try:
                case = run_case(home, scenario)
            finally:
                swept = sweep(home)
            case.update(seconds=time.monotonic()-began, swept=swept,
                        audit=audit(home, scenario))
            if case['completed'] != expected_delivery(scenario):
                raise ValueError(f'{scenario}: outcome contradicts the declared expectation')
            report['scenarios'][scenario] = case
            (root/'progress.json').write_text(json.dumps(report, indent=2))
        delivered = {name for name, case in report['scenarios'].items() if case['completed']}
        if delivered != {'ip', 'bridged', 'cut'}:
            raise ValueError(f'unexpected set of deliveries: {sorted(delivered)}')
        report['verdict'] = 'g4_scoped_pass'
    except Exception as exc:
        report.update(verdict='inconclusive', error=repr(exc), traceback=traceback.format_exc())
    (root/'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
    return 0 if report['verdict'] == 'g4_scoped_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
