"""Frozen V1 return run: the recipient's receipt reaches an origin that was never online with it."""
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

from g3_process import alive
from v1_return_audit import EXPECTED, audit
from v1_return_scenario import PROFILE, run_case


def sweep(root):
    killed = []
    for handle in root.rglob('daemon.json'):
        pid = json.loads(handle.read_text())['pid']
        if alive(pid):
            subprocess.run(['taskkill', '/F', '/PID', str(pid)] if os.name == 'nt'
                           else ['kill', '-9', str(pid)], capture_output=True)
            killed.append(pid)
    return killed


def main():
    base = Path(__file__).resolve().parent
    root = base/'results'/f'gateway-v1-return-{time.time_ns()}'
    root.mkdir(parents=True)
    print(f'Artifacts: {root}', flush=True)
    files = list(base.glob('v1_*.py'))+list((base/'dethron_gateway').glob('*.py'))
    files += [base/name for name in ('run_v1_return_probe.py', 'g3_process.py', 'g2_receiver.py',
                                     'gateway_contract.py', 'gateway_scenario.py')]
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
            case.update(seconds=time.monotonic()-began, swept=swept, audit=audit(home, scenario))
            if case['audit']['route']['proof_via'] != EXPECTED[scenario]['proof_via']:
                raise ValueError(f'{scenario}: proof route contradicts the declared expectation')
            report['scenarios'][scenario] = case
            (root/'progress.json').write_text(json.dumps(report, indent=2))
        report['verdict'] = 'v1_return_scoped_pass'
    except Exception as exc:
        report.update(verdict='inconclusive', error=repr(exc), traceback=traceback.format_exc())
    (root/'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
    return 0 if report['verdict'] == 'v1_return_scoped_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
