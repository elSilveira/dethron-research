"""What a machine is allowed to do during an isolated window, declared before it opens.

On one host the supervisor drove the nodes through files it shared with them. Across
machines that is no longer innocent: whatever carries commands during the window also
carries connectivity, and an isolation claim made over a live control channel proves
nothing. So each machine receives a schedule **before** the window, executes it from
its own disk without being told anything further, and the evidence is collected
afterwards through a channel that the audit excludes by name.

A schedule is therefore a contract, not a script: it is fixed, hashed, and every step
carries the time it is due, relative to a window start that both machines agreed on in
advance.
"""
import hashlib
import json
import re

VERSION = 1
MAX_STEPS = 64
MAX_WINDOW = 3600
ACTIONS = {
    'launch': {'node', 'role', 'contacts'},
    'announce': {'node'},
    'send': {'node', 'label', 'recipient', 'propagation', 'body'},
    'fetch': {'node', 'source', 'propagation', 'limit_kb'},
    'custody': {'node', 'relay', 'transient_id'},
    'status': {'node'},
    'stop': {'node'},
}
NODE = re.compile(r'[A-Z][0-9]?')


def digest(schedule):
    return hashlib.sha256(encode(schedule)).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')


def validate(schedule):
    """A schedule that is ambiguous, open ended or late-bound is refused outright."""
    if set(schedule) != {'version', 'machine', 'window_seconds', 'steps'}:
        raise ValueError('unexpected schedule fields')
    if schedule['version'] != VERSION or not isinstance(schedule['machine'], str) or not schedule['machine']:
        raise ValueError('unsupported schedule version or machine')
    window = schedule['window_seconds']
    if type(window) is not int or not 0 < window <= MAX_WINDOW:
        raise ValueError('invalid window length')
    steps = schedule['steps']
    if not isinstance(steps, list) or not 0 < len(steps) <= MAX_STEPS:
        raise ValueError('invalid step count')
    previous = -1
    for position, step in enumerate(steps):
        if set(step) != {'at', 'action', 'args'}:
            raise ValueError(f'step {position}: unexpected fields')
        if type(step['at']) is not int or not 0 <= step['at'] <= window:
            raise ValueError(f'step {position}: time outside the window')
        if step['at'] < previous:
            raise ValueError(f'step {position}: steps must be ordered by time')
        previous = step['at']
        action = step['action']
        if action not in ACTIONS:
            raise ValueError(f'step {position}: unknown action {action!r}')
        args = step['args']
        if not isinstance(args, dict) or set(args) - ACTIONS[action]:
            raise ValueError(f'step {position}: unexpected arguments for {action}')
        if 'node' not in args or not NODE.fullmatch(str(args['node'])):
            raise ValueError(f'step {position}: invalid node name')
    return schedule


def schedule(machine, window_seconds, steps):
    return validate({'version': VERSION, 'machine': machine,
                     'window_seconds': window_seconds, 'steps': list(steps)})


def step(at, action, **args):
    return {'at': at, 'action': action, 'args': args}


def plan(schedules):
    """The whole bench: one schedule per machine, plus the digest each agent must match."""
    if len(schedules) < 2:
        raise ValueError('a bench needs at least two machines')
    machines = [validate(one)['machine'] for one in schedules]
    if len(set(machines)) != len(machines):
        raise ValueError('duplicate machine in the bench')
    if len({one['window_seconds'] for one in schedules}) != 1:
        raise ValueError('every machine must share the same window')
    return {'version': VERSION, 'window_seconds': schedules[0]['window_seconds'],
            'machines': dict(zip(machines, schedules)),
            'digests': {machine: digest(one) for machine, one in zip(machines, schedules)}}
