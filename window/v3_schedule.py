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
# Every address a step needs is computed before the window, from identities minted in
# advance, so no step has to discover anything while the machines are deaf.
ACTIONS = {
    'launch': {'node', 'role', 'port', 'contacts', 'credential', 'serial'},
    'announce': {'node'},
    'send': {'node', 'label', 'recipient', 'recipient_key', 'propagation', 'body'},
    'fetch': {'node', 'source', 'source_key', 'propagation', 'limit_kb'},
    'custody': {'node', 'relay', 'relay_key', 'transient_id'},
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


def plan(schedules, start_wall=None):
    """The whole bench: one schedule per machine, the digest each agent must match, and
    optionally the wall-clock instant at which every machine opens its window.

    A declared instant beats a start marker across machines: the marker would need a
    live channel to arrive at both, and that channel is what an isolated window must
    not have. Wall clocks disagree, so each agent switches to its own monotonic clock
    at the instant and records the wall time it actually saw, which makes the combined
    skew readable from the evidence instead of assumed.
    """
    if len(schedules) < 2:
        raise ValueError('a bench needs at least two machines')
    if start_wall is not None and (type(start_wall) not in (int, float) or start_wall <= 0):
        raise ValueError('invalid rendezvous instant')
    machines = [validate(one)['machine'] for one in schedules]
    if len(set(machines)) != len(machines):
        raise ValueError('duplicate machine in the bench')
    if len({one['window_seconds'] for one in schedules}) != 1:
        raise ValueError('every machine must share the same window')
    return {'version': VERSION, 'window_seconds': schedules[0]['window_seconds'],
            'start_wall': start_wall, 'machines': dict(zip(machines, schedules)),
            'digests': {machine: digest(one) for machine, one in zip(machines, schedules)}}
