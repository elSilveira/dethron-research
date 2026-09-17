"""Detached node processes with a file command channel, so nodes outlive supervisors."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gateway_contract import config_text

DETACHED = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
LIVENESS_SECONDS = 2  # a liveness probe costs a subprocess; do not run one every poll


def lines(path):
    """A half-written trailing line is not a record yet."""
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    return text.split(chr(10))[:-1]


def alive(pid):
    if os.name == 'nt':
        probe = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH', '/FO', 'CSV'],
                               capture_output=True, text=True)
        return f'"{pid}"' in probe.stdout
    try:
        os.kill(pid, 0)
    except OSError as exc:
        return exc.errno != errno.ESRCH
    return True


class Daemon:
    """One long-lived node; any supervisor generation may attach through the files."""

    def __init__(self, root, name, worker='g3_node.py'):
        self.root, self.name, self.worker = Path(root), name, worker
        self.home = self.root/name
        self.commands, self.events = self.home/'commands.jsonl', self.home/'events.jsonl'
        self.handle = self.home/'daemon.json'
        self.pid, self.launcher, self.info, self.process = None, None, None, None
        self.sent, self.cursor = 0, 0

    def launch(self, port, contacts, settings=None, reuse=False, config=None):
        if self.handle.exists():
            if not reuse:
                raise ValueError('node already launched')
            if alive(json.loads(self.handle.read_text())['pid']):
                raise ValueError('previous incarnation is still running')
        (self.home/'rns').mkdir(parents=True, exist_ok=reuse)
        text = config_text(port, contacts) if config is None else config
        (self.home/'rns'/'config').write_text(text, encoding='utf-8')
        (self.home/'settings.json').write_text(json.dumps(settings or {}))
        # Keep earlier incarnations' evidence; read only what this one emits.
        for path in (self.commands, self.events):
            if not path.exists():
                path.write_text('', encoding='utf-8')
        self.sent, self.cursor = len(lines(self.commands)), len(lines(self.events))
        script = self.worker if os.path.isabs(self.worker) else str(Path(__file__).with_name(self.worker))
        with (self.home/'stdout.log').open('w', encoding='utf-8') as out, \
             (self.home/'stderr.log').open('w', encoding='utf-8') as err:
            process = subprocess.Popen([sys.executable, script, str(self.home), self.name],
                                       stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                       creationflags=DETACHED, close_fds=True,
                                       start_new_session=os.name != 'nt')
        self.process = process  # detached on purpose; hold it so finalization stays quiet
        self.pid, self.launcher = process.pid, process.pid
        try:
            self.info = self.wait('ready', timeout=60)
        except Exception:
            self.kill()
            raise
        # A venv launcher stub re-executes the interpreter, so trust the node's own pid.
        self.pid = self.info.get('pid', process.pid)
        self.handle.write_text(json.dumps({'pid': self.pid, 'launcher': self.launcher, 'name': self.name,
                                           'port': port, 'contacts': list(contacts), 'started': time.time()}))
        return self.info

    def attach(self):
        """Resume an already running node from public handle files only."""
        handle = json.loads(self.handle.read_text())
        self.pid, self.launcher = handle['pid'], handle.get('launcher')
        if not alive(self.pid):
            raise ProcessLookupError(f'{self.name}: node {self.pid} is not running')
        self.sent, self.cursor = len(lines(self.commands)), 0
        rows = self._read()
        for position in range(len(rows)-1, -1, -1):
            if rows[position]['event'] == 'ready':
                self.info, self.cursor = rows[position], len(rows)
                return self.info
        raise ValueError(f'{self.name}: node never reported ready')

    def _read(self):
        rows = []
        for line in lines(self.events)[self.cursor:]:
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({'event': 'error', 'error': line})
        return rows

    def send(self, action, **values):
        rid = f'{os.getpid()}-{self.sent}'
        self.sent += 1
        with self.commands.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'action': action, 'rid': rid, **values})+'\n')
        return rid

    def wait(self, event, timeout=120, **match):
        deadline = time.monotonic()+timeout
        checked = 0
        while True:
            for row in self._read():
                if row['event'] in ('error', 'send_failed', 'refused') and row.get('rid') in (None, match.get('rid')):
                    raise RuntimeError(f'{self.name}: {row}')
                if row['event'] == event and all(row.get(k) == v for k, v in match.items()):
                    return row
            now = time.monotonic()
            if self.pid is not None and now-checked >= LIVENESS_SECONDS:
                checked = now
                if not alive(self.pid):
                    raise ProcessLookupError(f'{self.name}: node exited; inspect {self.home}/stderr.log')
            if now > deadline:
                raise TimeoutError(f'{self.name}: {event} {match}')
            time.sleep(.05)

    def request(self, action, timeout=30, **values):
        return self.wait(action, timeout=timeout, rid=self.send(action, **values))

    def status(self, timeout=30):
        return self.request('status', timeout=timeout)

    def kill(self, timeout=20):
        if self.pid is None or not alive(self.pid):
            return
        self.send('crash')
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            if not alive(self.pid):
                return
            time.sleep(.25)
        for pid in {self.pid, self.launcher} - {None}:
            subprocess.run(['taskkill', '/F', '/PID', str(pid)] if os.name == 'nt'
                           else ['kill', '-9', str(pid)], capture_output=True)
