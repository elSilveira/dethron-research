"""V2 — reproduction by a stranger: one command that checks the environment, runs the fast
suite, runs every declared real reproduction path and compares each verdict with the one
this repository claims. Every opt-in flag is read from the test file itself.

Usage, from the repository root with the pinned environment. Works the same in
PowerShell and in cmd.exe, because it sets the opt-in variables itself:
    window/.venv-gateway/Scripts/python.exe window/run_v2_reproduction.py
    ... --fast-only        only the test suite, no real runs
    ... --only g3          only that milestone's real run
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
PINNED = {'rns': '1.5.4', 'lxmf': '1.1.1', 'cryptography': '50.0.1'}
# Measured on the committed tree: the whole suite, and the Rust-free subset by pattern.
FAST_EXPECTED = {'full': (176, 8), 'subset': (107, 8)}
EXPECTED = {
    'test_gateway_reference.py': 'meets_scoped_requirement',
    'test_g1_reference.py': 'meets_g1_lab_contract',
    'test_g2_reference.py': 'meets_g2_scoped_contract',
    'test_g2_comparison_reference.py': 'g2_scoped_pass',
    'test_g3_reference.py': 'g3_scoped_pass',
    'test_g4_reference.py': 'g4_scoped_pass',
    'test_v1_reference.py': 'v1_custody_scoped_pass',
    'test_v1_return_reference.py': 'v1_return_scoped_pass',
}
# Longest artifact path the probes create below the repository root (V1 return, 64-hex resource).
ARTIFACT_SUFFIX = len(r'\window\results\gateway-v1-return-0000000000000000000\proof_pending\D\rns\storage\resources')+1+64
WINDOWS_MAX_PATH = 260
REFERENCE_SECONDS = {'test_gateway_reference.py': 208, 'test_g1_reference.py': 31, 'test_g2_reference.py': 185,
                     'test_g2_comparison_reference.py': 754, 'test_g3_reference.py': 432,
                     'test_g4_reference.py': 167, 'test_v1_reference.py': 213, 'test_v1_return_reference.py': 332}


def select(argv):
    """--only g3 picks test_g3_reference.py; an unknown name is refused, not guessed."""
    if '--only' not in argv:
        return dict(EXPECTED)
    wanted = argv[argv.index('--only')+1] if len(argv) > argv.index('--only')+1 else ''
    chosen = {test: verdict for test, verdict in EXPECTED.items() if wanted and wanted in test}
    if not chosen:
        names = sorted(test.replace('test_', '').replace('_reference.py', '') for test in EXPECTED)
        raise SystemExit(f'--only {wanted!r} matches nothing; available: {", ".join(names)}')
    return chosen


def cargo_available():
    """The survival tests build a Rust binary; without cargo they fail confusingly."""
    try:
        quiet = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        return subprocess.run(['cargo', '--version'], capture_output=True,
                              timeout=60, creationflags=quiet).returncode == 0
    except Exception:
        return False


def flag_of(test):
    source = (BASE/'tests'/test).read_text(encoding='utf-8')
    flags = re.findall(r"""os\.environ\.get\(["'](RUN_[A-Z0-9_]+)["']\)""", source)
    if len(flags) != 1:
        raise SystemExit(f'{test}: expected exactly one opt-in flag, found {flags}')
    return flags[0]


def long_paths_enabled():
    """Windows only lifts the 260-character limit when this registry value is 1."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\FileSystem') as key:
            return winreg.QueryValueEx(key, 'LongPathsEnabled')[0] == 1
    except Exception:
        return False


def path_problems(root, long_paths=None):
    """A clone in a long path fails every real run with FileNotFoundError inside rns/storage."""
    problems = []
    if any(ch.isspace() or ch in '"\'' for ch in str(root)):
        problems.append(f'repository path must have no spaces or quotes: {root}')
    longest = len(str(root))+ARTIFACT_SUFFIX
    enabled = long_paths_enabled() if long_paths is None else long_paths
    if os.name == 'nt' and longest >= WINDOWS_MAX_PATH and not enabled:
        problems.append(f'repository path too long: artifacts would reach {longest} characters, '
                        f'Windows allows {WINDOWS_MAX_PATH-1}; clone into a short path such as C:\\dethron')
    return problems


def environment(root=ROOT):
    versions = {name: importlib.metadata.version(name) for name in PINNED}
    problems = path_problems(root)
    if versions != PINNED:
        problems.append(f'pinned packages differ: {versions}')
    if sys.version_info[:2] != (3, 10):
        problems.append(f'python {platform.python_version()} is not 3.10.x (the only version exercised)')
    if os.name != 'nt':
        problems.append('G4 endpoint evidence requires Windows netstat; other systems are untested')
    return {'python': platform.python_version(), 'platform': platform.platform(), 'packages': versions,
            'root': str(root), 'root_length': len(str(root)), 'longest_artifact_path': len(str(root))+ARTIFACT_SUFFIX,
            'problems': problems}


def unittest_run(pattern=None, env=None, timeout=3600):
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'window/tests']
    if pattern:
        command += ['-p', pattern]
    began = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env, timeout=timeout)
    output = result.stdout+result.stderr
    ran = re.search(r'Ran (\d+) tests?', output)
    skipped = re.search(r'skipped=(\d+)', output)
    return {'returncode': result.returncode, 'seconds': round(time.monotonic()-began, 1),
            'ran': int(ran.group(1)) if ran else None, 'skipped': int(skipped.group(1)) if skipped else 0,
            'ok': result.returncode == 0, 'tail': output.strip().splitlines()[-3:]}


def fast_suite(no_survival):
    env = {**os.environ, 'PYTHONPATH': 'window'}
    if not no_survival:
        row = unittest_run(env=env)
        want = FAST_EXPECTED['full']
        row['expected'] = {'ran': want[0], 'skipped': want[1]}
        row['pass'] = row['ok'] and (row['ran'], row['skipped']) == want
        return {'full': row}
    rows = {}
    for pattern in ('test_gateway_*.py', 'test_g1_*.py', 'test_g2_*.py', 'test_g3_*.py', 'test_g4_*.py', 'test_v1_*.py'):
        rows[pattern] = unittest_run(pattern, env=env)
        rows[pattern]['pass'] = rows[pattern]['ok']
    total = (sum(r['ran'] or 0 for r in rows.values()), sum(r['skipped'] for r in rows.values()))
    rows['subset total'] = {'ran': total[0], 'skipped': total[1], 'seconds': round(sum(r['seconds'] for r in rows.values()), 1),
                            'ok': all(r['ok'] for r in rows.values()), 'expected': dict(zip(('ran', 'skipped'), FAST_EXPECTED['subset'])),
                            'pass': all(r['ok'] for r in rows.values()) and total == FAST_EXPECTED['subset'], 'tail': []}
    return rows


def reference(test, expected):
    before = {p.name for p in (BASE/'results').iterdir()} if (BASE/'results').exists() else set()
    env = {**os.environ, 'PYTHONPATH': 'window', flag_of(test): '1'}
    row = unittest_run(test, env=env)
    created = sorted({p.name for p in (BASE/'results').iterdir()}-before)
    verdicts = {}
    for folder in created:
        report = BASE/'results'/folder/'report.json'
        if report.exists():
            verdicts[folder] = json.loads(report.read_text()).get('verdict')
    row.update(flag=flag_of(test), artifacts=created, verdicts=verdicts, expected=expected,
               reference_seconds=REFERENCE_SECONDS[test],
               pass_=row['ok'] and list(verdicts.values()) == [expected])
    row['pass'] = row.pop('pass_')
    return row


def main(argv):
    chosen = select(argv)
    fast_only = '--fast-only' in argv
    only = len(chosen) < len(EXPECTED)
    cargo = cargo_available()
    no_survival = '--no-survival' in argv or not cargo
    if not cargo:
        print('note: cargo not found, so the 15 survival tests that build a Rust binary are '
              'excluded; everything else runs normally', flush=True)
    out = BASE/'results'/f'v2-{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}'
    out.mkdir(parents=True)
    summary = {'environment': {**environment(), 'cargo': cargo, 'survival_excluded': no_survival},
               'fast': None, 'references': {}, 'started': time.time()}
    print('environment:', json.dumps(summary['environment']), flush=True)
    if summary['environment']['problems']:
        # Running would only produce eight timeouts; stop while the cause is still readable.
        (out/'summary.json').write_text(json.dumps({**summary, 'verdict': 'v2_fail'}, indent=2))
        for problem in summary['environment']['problems']:
            print('PROBLEM:', problem, flush=True)
        print(f"V2 FAIL - environment not acceptable; summary: {out/'summary.json'}", flush=True)
        return 1
    summary['fast'] = {} if only else fast_suite(no_survival)
    if only:
        print(f'running only: {", ".join(chosen)}', flush=True)
    for name, row in summary['fast'].items():
        print(f"fast {name:22} ran={row['ran']} skipped={row['skipped']} {'PASS' if row['pass'] else 'FAIL'} {row['seconds']}s", flush=True)
    (out/'summary.json').write_text(json.dumps(summary, indent=2))
    if not fast_only:
        for test, expected in chosen.items():
            row = reference(test, expected)
            summary['references'][test] = row
            (out/'summary.json').write_text(json.dumps(summary, indent=2))
            print(f"{test:34} {'PASS' if row['pass'] else 'FAIL'} verdict={list(row['verdicts'].values())} "
                  f"{row['seconds']}s (reference {row['reference_seconds']}s)", flush=True)
    passed = all(r['pass'] for r in summary['fast'].values()) and \
        all(r['pass'] for r in summary['references'].values()) and not summary['environment']['problems'] \
        and (summary['fast'] or summary['references'])
    summary['verdict'] = 'v2_pass' if passed else 'v2_fail'
    summary['finished'] = time.time()
    (out/'summary.json').write_text(json.dumps(summary, indent=2))
    print(f"V2 {'PASS' if passed else 'FAIL'} - summary: {out/'summary.json'}", flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
