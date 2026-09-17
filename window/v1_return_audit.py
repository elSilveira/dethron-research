"""Second half of V1: did the recipient's receipt reach an origin that never shared the network with it?"""
import json
import math

from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate
from v1_audit import entry_proofs, exit_proof, received_content, rows

EXPECTED = {'returned': {'completed': True, 'proof_via': 'C', 'missing_before': []},
            'proof_pending': {'completed': True, 'proof_via': 'A', 'missing_before': ['C']},
            'never_completed': {'completed': False, 'proof_via': None, 'missing_before': ['A', 'B', 'C']}}


def sessions(timeline, node):
    """Online intervals of a node, from its launch and stop records."""
    result = []
    for row in timeline:
        if row['event'] == 'launch' and row['node'] == node:
            result.append([row['time'], math.inf])
        elif row['event'] == 'stop' and row['node'] == node and result:
            result[-1][1] = row['time']
    return result


def disjoint(timeline):
    """Origin and recipient must never be online at the same time; otherwise the return proves nothing."""
    origin, recipient = sessions(timeline, 'O'), sessions(timeline, 'D')
    if len(origin) < 2 or not recipient:
        raise ValueError('the origin did not leave and return around the recipient session')
    for a in origin:
        for b in recipient:
            if a[0] < b[1] and b[0] < a[1]:
                raise ValueError('origin and recipient were online at the same time')
    return {'origin_sessions': len(origin), 'recipient_sessions': len(recipient)}


def receipt_at_origin(root, m, content, now):
    """The only acceptable proof of exit at the origin: the recipient's signature over the exact object."""
    files = sorted((root/'O'/'receipts').glob('*.lxmf')) if (root/'O'/'receipts').exists() else []
    if content is None:
        if files:
            raise ValueError('a receipt reached the origin although the recipient never completed')
        return None
    if len(files) != 1 or files[0].stem != m['object']['id']:
        raise ValueError(f'expected exactly one receipt for the object, saw {[p.name for p in files]}')
    obj = authenticate(files[0].read_bytes(), bytes.fromhex(m['destination']['public_key']),
                       m['source']['destination'], now)
    expected = receipt_envelope(data_envelope(m['source']['destination'], m['destination']['destination'],
                                              content, m['expires'], m['object']['id']))
    if obj != expected:
        raise ValueError('the receipt at the origin does not bind to the delivered object')
    if obj != json.loads((root/'D'/'completion.json').read_text()):
        raise ValueError('the receipt at the origin differs from the recipient\'s local receipt')
    return {'id': obj['id'], 'digest': obj['digest'], 'size': obj['size']}


def route(timeline):
    """Which relay actually carried the proof back, and which were asked first and had nothing."""
    visits = [row for row in timeline if row['event'] == 'return_visit']
    via = next((row['relay'] for row in visits if row['receipt']), None)
    missing = []
    for row in visits:
        if row['receipt']:
            break
        missing.append(row['relay'])
    return {'proof_via': via, 'missing_before': missing, 'visits': len(visits)}


def audit(root, scenario):
    m = json.loads((root/'manifest.json').read_text())
    timeline = rows(root)
    handoffs = {row['relay']: row['transient_id'] for row in timeline if row['event'] == 'handoff'}
    inventories = {row['relay']: row['inventory'] for row in timeline if row['event'] == 'handoff'}
    now = m['expires']-1
    proofs, missing = entry_proofs(root/'O', m, handoffs, inventories, now)
    if missing:
        raise ValueError(f'handoff without custody: {missing}')
    exit_ = exit_proof(root, m)
    _, content = received_content(root, m)
    result = {'passed': True, 'scenario': scenario, 'entry': len(proofs), 'exit_local': exit_,
              'completed': exit_['completed'], 'sessions': disjoint(timeline),
              'receipt_at_origin': receipt_at_origin(root, m, content, now), 'route': route(timeline)}
    if scenario == 'proof_pending':
        discards = [row for row in timeline if row['event'] == 'discard']
        if [row['relay'] for row in discards] != ['C']:
            raise ValueError('the relay that dropped its receipt copy was not recorded')
    want = EXPECTED[scenario]
    if (result['completed'], result['route']['proof_via'], result['route']['missing_before']) != \
            (want['completed'], want['proof_via'], want['missing_before']):
        raise ValueError(f'{scenario}: outcome contradicts the declared expectation')
    if result['completed'] and result['receipt_at_origin'] is None:
        raise ValueError('completed without a verified receipt at the origin')
    return result
