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
import platform
import socket
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
        self.schedule, self.plan = None, None

    def describe_host(self):
        """What this machine is, so an audit can tell two machines from two folders.

        Written once, before the window, because a claim about distinct machines that
        rests on the operator's word is not evidence.
        """
        addresses = set()
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                addresses.add(info[4][0])
        except Exception:
            hostname = None
        facts = {'hostname': hostname, 'node': platform.node(), 'system': platform.platform(),
                 'processor': platform.processor(), 'addresses': sorted(addresses)}
        (self.home/'host.json').write_text(json.dumps(facts, indent=2), encoding='utf-8')
        return facts

    def record(self, event, **values):
        row = {'event': event, 'machine': self.machine, 'wall': time.time(), **values}
        with self.evidence.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        return row

    def load(self):
        """The schedule must be exactly the one the bench declared, byte for byte."""
        if self.evidence.exists() and self.evidence.stat().st_size:
            raise ValueError(f'{self.machine}: this bench folder was already used. A bench is '
                             f'single use, because reusing one mixes the evidence of two runs '
                             f'and leaves nodes that cannot be launched again. Generate a new '
                             f'bench in a new folder and copy it across again.')
        plan = self.plan = json.loads((self.control/'plan.json').read_text(encoding='utf-8'))
        if self.machine not in plan['machines']:
            raise ValueError(f'{self.machine}: not part of this bench')
        schedule = validate(plan['machines'][self.machine])
        if digest(schedule) != plan['digests'][self.machine]:
            raise ValueError(f'{self.machine}: schedule does not match its declared digest')
        self.schedule = schedule
        self.record('loaded', digest=plan['digests'][self.machine], steps=len(schedule['steps']),
                    window_seconds=schedule['window_seconds'], host=self.describe_host())
        return schedule

    def wait_for_start(self, timeout=600):
        """Wait for the declared instant, or for a marker when no instant was declared.

        The wall time actually observed is recorded, so comparing the machines' records
        afterwards gives the combined clock offset and polling jitter as a number.
        """
        deadline = self.clock()+timeout
        declared = self.plan.get('start_wall') if self.plan else None
        if declared is not None:
            while time.time() < declared:
                if self.clock() > deadline:
                    raise TimeoutError(f'{self.machine}: rendezvous instant not reached within {timeout}s')
                time.sleep(min(.05, max(0.0, declared-time.time())))
            began, observed = self.clock(), time.time()
            self.record('started', declared_wall=declared, local_wall=observed,
                        late_seconds=round(observed-declared, 3))
            return began
        marker = self.control/'start.json'
        while not marker.exists():
            if self.clock() > deadline:
                raise TimeoutError(f'{self.machine}: no start marker within {timeout}s')
            time.sleep(.05)
        released = json.loads(marker.read_text(encoding='utf-8'))
        began = self.clock()
        self.record('started', declared_wall=released.get('wall'), local_wall=time.time(),
                    late_seconds=round(time.time()-released['wall'], 3) if 'wall' in released else None)
        return began

    def run(self, execute, timeout=600):
        """Execute each step when its own monotonic clock says so, and nothing else."""
        if self.schedule is None:
            self.load()
        # The window begins at the marker, so the seal must too: everything up to and
        # including the release is preparation, and only what follows must be silent.
        began = self.wait_for_start(timeout=timeout)
        before = seal(self.control)
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
