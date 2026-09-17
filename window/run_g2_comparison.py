"""Freeze, execute and independently audit twelve paired native LXMF cases."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import traceback

from g2_compare_audit import audit
from g2_compare_case import run_case
from g2_compare_contract import PROFILE, cases


def main():
    base = Path(__file__).resolve().parent
    root = base/'results'/f'g2-comparison-{time.time_ns()}'
    root.mkdir(parents=True)
    print(f'Artifacts: {root}', flush=True)
    (root/'profile.json').write_text(json.dumps({'profile': PROFILE, 'cases': cases()}, indent=2))
    paths = list(base.glob('g2_*.py'))+list((base/'dethron_gateway').glob('*.py'))
    paths += [base/n for n in ('run_g2_comparison.py', 'gateway_process.py', 'gateway_scenario.py', 'gateway_contract.py')]
    (root/'sources.json').write_text(json.dumps({str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in paths}, indent=2))
    versions = {n: importlib.metadata.version(n) for n in ('rns', 'lxmf', 'cryptography')}
    (root/'environment.json').write_text(json.dumps({'python': sys.version, 'packages': versions}, indent=2))
    report = {'cases': []}
    try:
        if versions['rns'] != '1.5.4' or versions['lxmf'] != '1.1.1':
            raise ValueError('unexpected reference versions')
        for i, case in enumerate(cases()):
            home = root/f"{i:02d}-{case['scenario']}-{case['mode']}"
            result = run_case(home, case)
            result['audit'] = audit(home)
            report['cases'].append(result)
            (root/'progress.json').write_text(json.dumps(report, indent=2))
        report['verdict'] = 'g2_scoped_pass'
    except Exception as exc:
        report.update(verdict='inconclusive', error=repr(exc), traceback=traceback.format_exc())
    (root/'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
    return 0 if report['verdict'] == 'g2_scoped_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
