"""Recompute the generation claims from what every supervisor left behind."""
import base64
import hashlib
import json

from dethron_gateway.erasure import reconstruct
from dethron_gateway.parts import validate
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate
from g3_contract import load_checkpoint

PHASES = ('seed', 'generation-1', 'generation-2', 'deliver')
ORIGINALS = {'O'} | {f'{name}{generation}' for name in 'ABC' for generation in (0, 1)}


def supervisors(timeline):
    owners = {}
    for row in timeline:
        owners.setdefault(row['phase'], set()).add(row['supervisor_pid'])
    if set(owners) != set(PHASES):
        raise ValueError(f'expected one record set per phase, saw {sorted(owners)}')
    if any(len(pids) != 1 for pids in owners.values()):
        raise ValueError('a phase was recorded by more than one supervisor')
    pids = [next(iter(owners[phase])) for phase in PHASES]
    if len(set(pids)) != len(PHASES):
        raise ValueError('the supervisor was not replaced between phases')
    return dict(zip(PHASES, pids))


def carriers(timeline):
    launches = {row['node']: row for row in timeline if row['event'] == 'launch'}
    retired = {row['node'] for row in timeline if row['event'] == 'retire'}
    if not ORIGINALS <= retired:
        raise ValueError(f'originals still running: {sorted(ORIGINALS-retired)}')
    generations = {}
    for name in 'ABC':
        destinations = [launches[f'{name}{g}']['info']['destination'] for g in (0, 1, 2)]
        if len(set(destinations)) != 3:
            raise ValueError(f'{name}: a generation reused a carrier identity')
        generations[name] = destinations
    handovers = [row for row in timeline if row['event'] == 'handover']
    if len(handovers) != 6:
        raise ValueError(f'expected six native handovers, saw {len(handovers)}')
    if any(row['stored'] != 1 or len(row['inventory']) != 1 for row in handovers):
        raise ValueError('a handover did not carry exactly the declared message')
    return {'generations': generations, 'handovers': len(handovers), 'retired': sorted(retired)}


def chain(root, mode):
    states = [load_checkpoint(root, generation) for generation in (0, 1, 2)]
    if any(state['mode'] != mode for state in states):
        raise ValueError('checkpoint scenario drifted')
    fleets = {tuple(sorted(state['relays'][name]['destination'] for name in 'ABC')) for state in states}
    if len(fleets) != len(states):
        raise ValueError('checkpoints did not change carriers')
    inventories = {tuple(sorted(sum((state['relays'][name]['inventory'] for name in 'ABC'), [])))
                   for state in states}
    if len(inventories) != 1:
        raise ValueError('the carried data changed across generations')
    return {'checkpoints': len(states), 'stored_objects': len(next(iter(inventories))),
            'inventory': sorted(next(iter(inventories)))}


def delivery(root, m):
    chunks = {}
    for path in sorted((root/'D'/'packets').glob('*.lxmf')):
        obj = authenticate(path.read_bytes(), bytes.fromhex(m['source']['public_key']),
                           m['destination']['destination'], m['expires']-1)
        if obj not in m['inputs'].values():
            raise ValueError('receiver kept a packet that the origin never submitted')
        manifest, index, data = validate(base64.b64decode(obj['payload'], validate=True))
        if manifest != m['object']:
            raise ValueError('unexpected object manifest')
        chunks[index] = data
    if len(chunks) != len(m['object']['lengths']):
        raise ValueError(f'missing unique authenticated parts: {sorted(chunks)}')
    content = reconstruct(m['object'], chunks)
    if (root/'D'/'output.bin').read_bytes() != content:
        raise ValueError('stored output does not match the authenticated parts')
    receipt = authenticate((root/'D'/'completion.lxmf').read_bytes(),
                           bytes.fromhex(m['destination']['public_key']),
                           m['source']['destination'], m['expires']-1)
    original = data_envelope(m['source']['destination'], m['destination']['destination'],
                             content, m['expires'], m['object']['id'])
    if receipt != receipt_envelope(original):
        raise ValueError('invalid completion receipt')
    return {'completed': True, 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
            'parts': sorted(chunks)}


def withdrawal(root, timeline):
    if (root/'D'/'output.bin').exists() or (root/'D'/'completion.lxmf').exists():
        raise ValueError('the receiver completed without the declared credential')
    withdrawn = [row for row in timeline if row['event'] == 'withdrawn']
    refused = [row for row in timeline if row['event'] == 'refused']
    if len(withdrawn) != 1 or len(refused) != 1:
        raise ValueError('the withdrawal or its refusal is not recorded')
    if (root/'credentials'/'destination.key').exists():
        raise ValueError('the declared credential was not actually withdrawn')
    return {'completed': False, 'refused': True, 'reason': refused[0]['reason'],
            'withdrew': withdrawn[0]['resource']}


def audit(root, mode):
    m = json.loads((root/'manifest.json').read_text())
    timeline = [json.loads(line) for line in (root/'timeline.jsonl').read_text().splitlines()]
    if m['object']['digest'] != hashlib.sha256(
            hashlib.shake_256(b'dethron-g3-v1').digest(m['object']['size'])).hexdigest():
        raise ValueError('the declared object is not the frozen payload')
    result = {'passed': True, 'mode': mode, 'supervisors': supervisors(timeline),
              'carriers': carriers(timeline), 'chain': chain(root, mode)}
    result.update(delivery(root, m) if mode == 'complete' else withdrawal(root, timeline))
    return result
