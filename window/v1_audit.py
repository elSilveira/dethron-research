"""Recompute proof of entry, proof of exit and pendency from what the nodes left behind.

A handoff event is not custody. Custody is not delivery. Every claim below is
derived from a signed packet or from its verified absence.
"""
import base64
import hashlib
import json

from dethron_gateway.custody import verify, verify_refusal
from dethron_gateway.erasure import reconstruct
from dethron_gateway.parts import validate
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate

EXPECTED = {'delivered': True, 'pending': False, 'discarded': False, 'fake': True}


def rows(root):
    return [json.loads(line) for line in (root/'timeline.jsonl').read_text().splitlines()]


def entry_proofs(origin, m, handoffs, inventories, now):
    """Only a verified custody packet counts; a handoff without one is recorded as missing."""
    proofs, missing = {}, []
    for relay, tid in handoffs.items():
        path = origin/'custody'/f'{tid}.lxmf'
        if not path.exists():
            missing.append(relay)
            continue
        obj = verify(path.read_bytes(), bytes.fromhex(m['relays'][relay]['public_key']),
                     m['source']['destination'], tid, now)
        if obj['recipient'] != m['destination']['destination']:
            raise ValueError(f'{relay}: custody names another recipient')
        if obj['stored_digest'] not in inventories.get(relay, []):
            raise ValueError(f'{relay}: custody digest is not what the relay stored')
        proofs[relay] = {'transient_id': tid, 'stored_size': obj['stored_size'], 'received': obj['received']}
    return proofs, missing


def refusal(origin, m, tid, now):
    if (origin/'custody'/f'{tid}.lxmf').exists():
        raise ValueError('a relay attested custody of a message that was never submitted')
    raw = (origin/'custody'/f'{tid}.refused.lxmf').read_bytes()
    obj = verify_refusal(raw, bytes.fromhex(m['relays']['A']['public_key']), m['source']['destination'], tid, now)
    return {'transient_id': tid, 'reason': obj['reason']}


def received_content(root, m):
    """Authenticated parts kept by the recipient, and the object if they suffice."""
    home, received = root/'D', {}
    packets = sorted((home/'packets').glob('*.lxmf')) if (home/'packets').exists() else []
    for path in packets:
        obj = authenticate(path.read_bytes(), bytes.fromhex(m['source']['public_key']),
                           m['destination']['destination'], m['expires']-1)
        if obj not in m['inputs'].values():
            raise ValueError('the receiver kept a packet the origin never submitted')
        manifest, index, data = validate(base64.b64decode(obj['payload'], validate=True))
        if manifest != m['object']:
            raise ValueError('unexpected object manifest')
        received[index] = data
    content = reconstruct(m['object'], received) if len(received) >= len(m['object']['lengths']) else None
    return received, content


def exit_proof(root, m):
    """Proof of exit is the recipient's own signed receipt over the exact bytes; nothing else."""
    received, content = received_content(root, m)
    output, receipt = root/'D'/'output.bin', root/'D'/'completion.lxmf'
    if content is None:
        if output.exists() or receipt.exists():
            raise ValueError('output or receipt exists without enough authenticated parts')
        return {'completed': False, 'parts': sorted(received)}
    if output.read_bytes() != content:
        raise ValueError('stored output does not match the authenticated parts')
    obj = authenticate(receipt.read_bytes(), bytes.fromhex(m['destination']['public_key']),
                       m['source']['destination'], m['expires']-1)
    original = data_envelope(m['source']['destination'], m['destination']['destination'],
                             content, m['expires'], m['object']['id'])
    if obj != receipt_envelope(original):
        raise ValueError('invalid completion receipt')
    return {'completed': True, 'parts': sorted(received), 'sha256': hashlib.sha256(content).hexdigest()}


def pendency(m, proofs, parts, fetched):
    """Where the object is stuck, derived from custody and from what actually arrived."""
    awaiting, attested_not_delivered = [], []
    for relay, index in m['placement'].items():
        if relay not in proofs or index in parts:
            continue
        (attested_not_delivered if relay in fetched else awaiting).append(relay)
    return {'awaiting_contact': sorted(awaiting), 'attested_not_delivered': sorted(attested_not_delivered)}


def audit(root, scenario):
    m = json.loads((root/'manifest.json').read_text())
    timeline = rows(root)
    handoffs = {row['relay']: row['transient_id'] for row in timeline if row['event'] == 'handoff'}
    inventories = {row['relay']: row['inventory'] for row in timeline if row['event'] == 'handoff'}
    if set(handoffs) != set('ABC'):
        raise ValueError('expected one handoff per relay')
    now = m['expires']-1
    proofs, missing = entry_proofs(root/'O.offline', m, handoffs, inventories, now)
    if missing:
        raise ValueError(f'handoff without custody: {missing}')
    exit_ = exit_proof(root, m)
    fetched = {row['relay'] for row in timeline if row['event'] == 'fetch'}
    result = {'passed': True, 'scenario': scenario, 'entry': proofs, 'missing_entry': missing,
              'exit': exit_, 'completed': exit_['completed'],
              'pendency': pendency(m, proofs, set(exit_['parts']), fetched)}
    if scenario == 'fake':
        result['refusal'] = refusal(root/'O.offline', m, m['fake_transient_id'], now)
    if scenario == 'discarded':
        discards = [row for row in timeline if row['event'] == 'discard']
        if len(discards) != 1 or result['pendency']['attested_not_delivered'] != [discards[0]['relay']]:
            raise ValueError('the relay that attested and discarded was not identified')
    if scenario == 'pending' and result['pendency']['awaiting_contact'] != ['A', 'B', 'C']:
        raise ValueError('pending object was not localized at all three relays')
    if result['completed'] != EXPECTED[scenario]:
        raise ValueError(f'{scenario}: outcome contradicts the declared expectation')
    return result
