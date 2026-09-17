"""Recompute the G4 claims from configurations, OS evidence, the medium and the packets."""
import base64
import hashlib
import json

from dethron_gateway.erasure import reconstruct
from dethron_gateway.parts import validate
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate
from g4_contract import expected_delivery

RECEIVER_LEDGER = 'dr-b'


def rows(root):
    return [json.loads(line) for line in (root/'timeline.jsonl').read_text().splitlines()]


def declared_paths(timeline, scenario):
    """What the nodes were actually configured with, read back from the timeline."""
    launches = [row for row in timeline if row['event'] == 'launch']
    if len(launches) != 3:
        raise ValueError(f'expected three nodes, saw {len(launches)}')
    isolated = [row['node'] for row in launches if row['isolated']]
    if scenario == 'ip':
        if isolated:
            raise ValueError(f'the IP baseline must use the IP stack, but {isolated} did not')
    elif len(isolated) != 3:
        reachable = [row['node'] for row in launches if not row['isolated']]
        raise ValueError(f'these nodes could still reach the IP stack: {reachable}')
    return {'nodes': [row['node'] for row in launches], 'isolated': isolated}


def socket_evidence(timeline, scenario):
    samples = [row for row in timeline if row['event'] == 'ip_endpoints']
    if len(samples) != 1:
        raise ValueError(f'expected one endpoint sample, saw {len(samples)}')
    sample = samples[0]
    if not sample['nodes'] or (scenario != 'ip' and not sample['bridges']):
        raise ValueError('the isolation check inspected no process at all')
    if scenario == 'ip':
        # Without this positive control, an empty result would prove nothing.
        if not sample['endpoints']:
            raise ValueError('the IP baseline showed no endpoint; the evidence tool proves nothing')
    elif sample['endpoints']:
        raise ValueError(f'isolated processes held IP endpoints: {sample["endpoints"]}')
    return {'inspected': len(sample['nodes'])+len(sample['bridges']),
            'endpoints': len(sample['endpoints'])}


def medium(root, timeline, scenario, size):
    ledgers = {path.stem: json.loads(path.read_text()) for path in (root/'ledgers').glob('*.json')}
    cuts = [row for row in timeline if row['event'] == 'cut']
    restores = [row for row in timeline if row['event'] == 'restore']
    if scenario == 'ip':
        if ledgers:
            raise ValueError('the IP baseline carried bytes over a bridge')
        return {'bridges': 0, 'cuts': 0, 'restores': 0}
    if RECEIVER_LEDGER not in ledgers:
        raise ValueError('the receiver side of the medium left no ledger')
    carried = ledgers[RECEIVER_LEDGER]
    expected = {'dark': (1, 0), 'cut': (1, 1)}.get(scenario, (0, 0))
    if (len(cuts), len(restores)) != expected:
        raise ValueError(f'{scenario}: {len(cuts)} cuts and {len(restores)} restores were not declared')
    if scenario == 'dark':
        if carried['received'] or carried['sent']:
            raise ValueError('the removed medium still carried bytes')
        if not carried['cut_losses']:
            raise ValueError('nothing was ever offered to the removed medium')
    else:
        if carried['received'] < size:
            raise ValueError('less than the object crossed the medium')
        if scenario == 'cut' and not carried['cut_losses']:
            raise ValueError('the cut lost nothing, so it was not a cut')
    return {'bridges': len(ledgers), 'cuts': len(cuts), 'restores': len(restores),
            'received_bytes': carried['received'], 'cut_losses': carried['cut_losses']}


def delivery(root, m):
    chunks = {}
    for path in sorted((root/'D'/'packets').glob('*.lxmf')):
        obj = authenticate(path.read_bytes(), bytes.fromhex(m['source']['public_key']),
                           m['destination']['destination'], m['expires']-1)
        if obj != m['input']:
            raise ValueError('the receiver kept a packet the origin never submitted')
        manifest, index, data = validate(base64.b64decode(obj['payload'], validate=True))
        if manifest != m['object']:
            raise ValueError('unexpected object manifest')
        chunks[index] = data
    if len(chunks) != len(m['object']['lengths']):
        raise ValueError(f'missing authenticated parts: {sorted(chunks)}')
    content = reconstruct(m['object'], chunks)
    if (root/'D'/'output.bin').read_bytes() != content:
        raise ValueError('the stored output does not match the authenticated packets')
    receipt = authenticate((root/'D'/'completion.lxmf').read_bytes(),
                           bytes.fromhex(m['destination']['public_key']),
                           m['source']['destination'], m['expires']-1)
    original = data_envelope(m['source']['destination'], m['destination']['destination'],
                             content, m['expires'], m['object']['id'])
    if receipt != receipt_envelope(original):
        raise ValueError('invalid completion receipt')
    return {'completed': True, 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()}


def pending(root, timeline):
    if (root/'D'/'output.bin').exists() or (root/'D'/'completion.lxmf').exists():
        raise ValueError('the receiver completed without a medium')
    finished = [row for row in timeline if row['event'] == 'case_finished']
    if len(finished) != 1 or finished[0]['relay_stored'] != 1:
        raise ValueError('the undelivered object did not stay pending at the relay')
    return {'completed': False, 'pending_at_relay': 1}


def audit(root, scenario):
    m = json.loads((root/'manifest.json').read_text())
    timeline = rows(root)
    result = {'passed': True, 'scenario': scenario,
              'paths': declared_paths(timeline, scenario),
              'sockets': socket_evidence(timeline, scenario),
              'medium': medium(root, timeline, scenario, m['object']['size'])}
    result.update(delivery(root, m) if expected_delivery(scenario) else pending(root, timeline))
    if result['completed'] != expected_delivery(scenario):
        raise ValueError(f'{scenario}: the outcome contradicts the declared expectation')
    return result
