"""Recompute the V3a claims from what the two machines left behind.

The claim is narrow and easy to overstate, so it is split into parts that are checked
separately: that neither machine was steered while its window was open, that both
windows opened together, that the schedules executed were the ones declared, that the
object really arrived, and — the one that decides whether any of this means more than
the single-host milestones — that the two machines were actually distinct.
"""
import base64
import hashlib
import json
from pathlib import Path

from dethron_gateway.erasure import reconstruct
from dethron_gateway.parts import validate as validate_part
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate
from v3_schedule import digest, validate

LOOPBACK = ('127.0.0.1', 'localhost', '::1')
MAX_SKEW = 5.0


def rows(root, machine):
    path = root/machine/'evidence.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def obedience(root, plan, machine):
    """The schedule executed must be the declared one, and the window must be silent."""
    evidence = rows(root, machine)
    loaded = [row for row in evidence if row['event'] == 'loaded']
    started = [row for row in evidence if row['event'] == 'started']
    finished = [row for row in evidence if row['event'] == 'finished']
    if len(loaded) != 1 or len(started) != 1 or len(finished) != 1:
        raise ValueError(f'{machine}: expected exactly one load, start and finish')
    declared = validate(plan['machines'][machine])
    if loaded[0]['digest'] != digest(declared) != plan['digests'][machine]:
        raise ValueError(f'{machine}: executed a schedule that is not the declared one')
    if not finished[0]['control_unchanged']:
        raise ValueError(f'{machine}: the control channel changed while the window was open')
    steps = [row for row in evidence if row['event'] == 'step']
    if len(steps) != len(declared['steps']):
        raise ValueError(f'{machine}: ran {len(steps)} of {len(declared["steps"])} declared steps')
    for position, (row, want) in enumerate(zip(steps, declared['steps'])):
        if row['position'] != position or row['action'] != want['action'] or row['declared_at'] != want['at']:
            raise ValueError(f'{machine}: step {position} is not the declared one')
        if row['error']:
            raise ValueError(f'{machine}: step {position} failed: {row["error"]}')
    return {'machine': machine, 'steps': len(steps), 'control_unchanged': True,
            'opened_wall': started[0]['local_wall'], 'late_seconds': started[0]['late_seconds'],
            'max_drift': max(abs(row['drift']) for row in steps)}


def rendezvous(reports, plan):
    """Both windows must open at the declared instant, and the gap is the usable skew."""
    opened = sorted(report['opened_wall'] for report in reports)
    skew = opened[-1]-opened[0]
    if plan.get('start_wall') and any(report['opened_wall'] < plan['start_wall'] for report in reports):
        raise ValueError('a machine opened its window before the declared instant')
    if skew > MAX_SKEW:
        raise ValueError(f'the machines opened their windows {round(skew, 3)}s apart')
    return {'skew_seconds': round(skew, 3), 'max_late_seconds': max(r['late_seconds'] for r in reports)}


def distinct_machines(root, manifest, reports):
    """Whether this run says anything the single-host milestones did not.

    Two agents on one host execute the same schedules just as happily, so a V3a claim
    that does not establish distinct machines is worth no more than G1. What the
    evidence can carry is checked here; what it cannot is reported as not evidenced,
    never assumed.
    """
    host = str(manifest.get('relay_host', ''))
    facts = {'relay_host': host, 'loopback': host in LOOPBACK}
    hosts = {}
    for report in reports:
        path = root/report['machine']/'host.json'
        if path.exists():
            hosts[report['machine']] = json.loads(path.read_text(encoding='utf-8'))
    facts['reported_hosts'] = hosts
    if facts['loopback']:
        raise ValueError('the recipient reached the relay over loopback: this is a single host')
    if len(hosts) != len(reports):
        facts['evidenced'] = False
        facts['reason'] = ('the agents did not record their host identity, so distinctness rests '
                           'on the non-loopback address and on the operator, not on this evidence')
        return facts
    names = {one.get('hostname') for one in hosts.values()}
    if len(names) != len(reports):
        raise ValueError(f'the machines report the same host identity: {sorted(names)}')
    # The relay address must belong to the relay machine and to no other, which is what
    # separates two machines from two folders on one.
    owners = sorted(name for name, one in hosts.items() if host in (one.get('addresses') or []))
    if owners != ['alpha']:
        raise ValueError(f'the relay address {host} belongs to {owners or "no machine that reported"}')
    facts.update(evidenced=True, hostnames=sorted(names), relay_owner='alpha')
    return facts


def delivery(root, manifest, machine='beta', node='D'):
    """The same cryptographic audit as the single-host milestones, on what arrived."""
    home = root/machine/node
    packets = sorted((home/'packets').glob('*.lxmf')) if (home/'packets').exists() else []
    chunks = {}
    for path in packets:
        obj = authenticate(path.read_bytes(), bytes.fromhex(manifest['identities']['O']['public_key']),
                           manifest['identities']['D']['delivery'], manifest['expires']-1)
        if obj != manifest['input']:
            raise ValueError('the recipient kept a packet the origin never submitted')
        part, index, data = validate_part(base64.b64decode(obj['payload'], validate=True))
        if part != manifest['object']:
            raise ValueError('unexpected object manifest')
        chunks[index] = data
    if len(chunks) != len(manifest['object']['lengths']):
        raise ValueError(f'missing authenticated parts: {sorted(chunks)}')
    content = reconstruct(manifest['object'], chunks)
    if hashlib.sha256(content).hexdigest() != manifest['digest']:
        raise ValueError('the delivered object is not the declared payload')
    if (home/'output.bin').read_bytes() != content:
        raise ValueError('stored output does not match the authenticated packets')
    receipt = authenticate((home/'completion.lxmf').read_bytes(),
                           bytes.fromhex(manifest['identities']['D']['public_key']),
                           manifest['identities']['O']['delivery'], manifest['expires']-1)
    expected = receipt_envelope(data_envelope(manifest['identities']['O']['delivery'],
                                              manifest['identities']['D']['delivery'],
                                              content, manifest['expires'], manifest['object']['id']))
    if receipt != expected:
        raise ValueError('invalid completion receipt')
    return {'completed': True, 'size': len(content), 'sha256': manifest['digest'],
            'packets': len(packets)}


def audit(root):
    root = Path(root)
    plan = json.loads((root/'control'/'plan.json').read_text(encoding='utf-8'))
    manifest = json.loads((root/'control'/'manifest.json').read_text(encoding='utf-8'))
    reports = [obedience(root, plan, machine) for machine in sorted(plan['machines'])]
    result = {'passed': True, 'machines': reports, 'rendezvous': rendezvous(reports, plan),
              'delivery': delivery(root, manifest)}
    result['distinct_machines'] = distinct_machines(root, manifest, reports)
    result['verdict'] = ('v3a_scoped_pass' if result['distinct_machines']['evidenced']
                         else 'v3a_pass_without_machine_evidence')
    return result
