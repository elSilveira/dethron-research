"""One machine executing its own pre-declared schedule, deaf for the whole window.

Absolute time is avoided on purpose. Wall clocks on two machines disagree, and the
obvious remedy — NTP — is an external dependency over the very stack an isolation
claim excludes. So the agent runs on its own monotonic clock, counting from a start
marker delivered before the window opens. The only cross-machine error left is the
delivery skew of that marker, which is measured and recorded rather than assumed.

Deafness is by construction: the agent never reads a command channel. It is also
checked, by sealing the control directory before the window and comparing after, so a
run where somebody steered a machine mid-window fails instead of passing quietly.
"""
import hashlib
import json
from pathlib import Path
import time

from v3_schedule import digest, validate

TOLERANCE = 5.0


def seal(folder):
    """A fingerprint of everything the control channel could have touched."""
    folder = Path(folder)
    entries = {}
    for path in sorted(folder.rglob('*')) if folder.exists() else []:
        if path.is_file():
            entries[str(path.relative_to(folder)).replace('\\', '/')] = \
                hashlib.sha256(path.read_bytes()).hexdigest()
    return entries


class Agent:
    def __init__(self, root, machine, clock=time.monotonic):
        self.root, self.machine, self.clock = Path(root), machine, clock
        self.home = self.root/machine
        self.home.mkdir(parents=True, exist_ok=True)
        self.control = self.root/'control'
        self.evidence = self.home/'evidence.jsonl'
        self.schedule = None

    def record(self, event, **values):
        row = {'event': event, 'machine': self.machine, 'wall': time.time(), **values}
        with self.evidence.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        return row

    def load(self):
        """The schedule must be exactly the one the bench declared, byte for byte."""
        plan = json.loads((self.control/'plan.json').read_text(encoding='utf-8'))
        if self.machine not in plan['machines']:
            raise ValueError(f'{self.machine}: not part of this bench')
        schedule = validate(plan['machines'][self.machine])
        if digest(schedule) != plan['digests'][self.machine]:
            raise ValueError(f'{self.machine}: schedule does not match its declared digest')
        self.schedule = schedule
        self.record('loaded', digest=plan['digests'][self.machine], steps=len(schedule['steps']),
                    window_seconds=schedule['window_seconds'])
        return schedule

    def wait_for_start(self, timeout=600):
        """The last thing the control channel does before the window; skew is recorded."""
        marker = self.control/'start.json'
        deadline = self.clock()+timeout
        while not marker.exists():
            if self.clock() > deadline:
                raise TimeoutError(f'{self.machine}: no start marker within {timeout}s')
            time.sleep(.05)
        declared = json.loads(marker.read_text(encoding='utf-8'))
        began = self.clock()
        self.record('started', marker_wall=declared.get('wall'), local_wall=time.time(),
                    skew_seconds=time.time()-declared['wall'] if 'wall' in declared else None)
        return began

    def run(self, execute, timeout=600):
        """Execute each step when its own monotonic clock says so, and nothing else."""
        if self.schedule is None:
            self.load()
        before = seal(self.control)
        began = self.wait_for_start(timeout=timeout)
        results = []
        for position, step in enumerate(self.schedule['steps']):
            due = began+step['at']
            while self.clock() < due:
                time.sleep(min(.05, due-self.clock()))
            observed = self.clock()-began
            try:
                outcome = execute(step['action'], step['args'])
                error = None
            except Exception as exc:
                outcome, error = None, repr(exc)
            results.append(self.record('step', position=position, action=step['action'],
                                       declared_at=step['at'], observed_at=round(observed, 3),
                                       drift=round(observed-step['at'], 3),
                                       outcome=outcome, error=error))
            if error is not None:
                break
        after = seal(self.control)
        self.record('finished', steps=len(results), control_unchanged=before == after,
                    control_before=len(before), control_after=len(after))
        if before != after:
            changed = sorted(set(before) ^ set(after)) or \
                [name for name in before if before[name] != after.get(name)]
            raise ValueError(f'{self.machine}: the control channel changed during the window: {changed}')
        return results
