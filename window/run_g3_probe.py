"""Frozen G3 generations run: every phase is a separate supervisor process."""
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

from g3_audit import audit
from g3_process import QUIET, alive

PHASES = ('seed', '1', '2', 'deliver')


def supervise(base, root, phase, mode, timeout=1800):
    result = subprocess.run([sys.executable, str(base/'g3_supervisor.py'), str(root), phase, mode],
                            capture_output=True, text=True, timeout=timeout,
                            env={**os.environ, 'PYTHONPATH': str(base)})
    (root/f'phase-{phase}.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    if result.returncode != 0:
        raise ValueError(f'phase {phase} failed ({result.returncode}): {result.stderr.strip()[-400:]}')
    return json.loads(result.stdout.splitlines()[-1])


def sweep(root):
    """No node may outlive the experiment, however a phase ended."""
    stopped = []
    for handle in root.rglob('daemon.json'):
        pid = json.loads(handle.read_text())['pid']
        if alive(pid):
            subprocess.run(['taskkill', '/F', '/PID', str(pid)] if os.name == 'nt'
                           else ['kill', '-9', str(pid)], capture_output=True, creationflags=QUIET)
            stopped.append(pid)
    return stopped


def checkpoint_rejected(base, root):
    """A successor without a declared checkpoint must refuse, not improvise."""
    empty = root/'no-checkpoint'
    empty.mkdir()
    result = subprocess.run([sys.executable, str(base/'g3_supervisor.py'), str(empty), '1', 'complete'],
                            capture_output=True, text=True, timeout=180,
                            env={**os.environ, 'PYTHONPATH': str(base)})
    (root/'no-checkpoint.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    return result.returncode != 0 and 'checkpoint-0.json' in result.stderr


def main():
    base = Path(__file__).resolve().parent
    root = base/'results'/f'gateway-g3-{time.time_ns()}'
    root.mkdir(parents=True)
    print(f'Artifacts: {root}', flush=True)
    files = list(base.glob('g3_*.py'))+list((base/'dethron_gateway').glob('*.py'))
    files += [base/name for name in ('run_g3_probe.py', 'gateway_contract.py', 'gateway_scenario.py', 'g2_receiver.py')]
    (root/'sources.json').write_text(json.dumps({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                 for p in files}, indent=2))
    versions = {name: importlib.metadata.version(name) for name in ('rns', 'lxmf', 'cryptography')}
    (root/'environment.json').write_text(json.dumps({'packages': versions, 'python': sys.version,
                                                     'platform': platform.platform()}, indent=2))
    report = {}
    try:
        if versions['rns'] != '1.5.4' or versions['lxmf'] != '1.1.1':
            raise ValueError('unexpected reference versions')
        for mode in ('complete', 'missing'):
            home = root/mode
            home.mkdir()
            phases = []
            began = time.monotonic()
            try:
                for phase in PHASES:
                    phases.append(supervise(base, home, phase, mode))
                    (root/'progress.json').write_text(json.dumps({**report, mode: phases}, indent=2))
            finally:
                report[mode] = {'phases': phases, 'seconds': time.monotonic()-began, 'swept': sweep(home)}
            if any(row['phase'] != 'seed' and row['guard'] is not True for row in phases):
                raise ValueError('a supervisor could still reach a retired generation')
            if len({row['supervisor_pid'] for row in phases}) != len(PHASES):
                raise ValueError('a phase reused a supervisor process')
            result = audit(home, mode)
            report[mode].update(audit=result, completed=result['completed'])
        report['missing_checkpoint_rejected'] = checkpoint_rejected(base, root)
        if not report['missing_checkpoint_rejected']:
            raise ValueError('a successor accepted a missing checkpoint')
        report['verdict'] = 'g3_scoped_pass'
    except Exception as exc:
        report.update(verdict='inconclusive', error=repr(exc), traceback=traceback.format_exc())
    (root/'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
    return 0 if report['verdict'] == 'g3_scoped_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
