"""One V1 case: parts to three relays, custody from each, then delivery or a visible failure."""
import base64
import hashlib
import json
import time

import RNS

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from v1_lab import Lab

PROFILE = {'version': 1, 'payload_bytes': 24576, 'parts': 3, 'deadline_seconds': 120,
           'custody_wait_seconds': 60, 'scenarios': ['delivered', 'pending', 'discarded', 'fake']}
OBJECT_ID = 'b'*32
FAKE = hashlib.sha256(b'never submitted').hexdigest()
EXPECTED = {'delivered': True, 'pending': False, 'discarded': False, 'fake': True}


def credential(root):
    folder = root/'credentials'
    folder.mkdir(exist_ok=True)
    key = folder/'destination.key'
    identity = RNS.Identity()
    identity.to_file(str(key))
    return key, {'destination': RNS.Destination.hash(identity, 'lxmf', 'delivery').hex(),
                 'public_key': identity.get_public_key().hex()}


def ask_custody(lab, origin, relay, transient_id):
    """A request is answered by a signed attestation or an explicit refusal, never silence."""
    origin.request('custody', relay={'name': relay.name, **lab.public(relay)}, transient_id=transient_id)
    deadline = time.monotonic()+PROFILE['custody_wait_seconds']
    while time.monotonic() < deadline:
        for row in origin._read():
            # The 'custody' command ack shares the id; only the verified reply events count here.
            if row['event'] in ('custody_received', 'custody_refused') and row.get('transient_id') == transient_id:
                kind = 'custody' if row['event'] == 'custody_received' else 'custody_refusal'
                return lab.record('custody_result', relay=relay.name, kind=kind,
                                  transient_id=transient_id, stored_digest=row.get('stored_digest'),
                                  reason=row.get('reason'))
            if row['event'] == 'rejected' or row['event'] == 'direct_failed':
                raise RuntimeError(f'custody exchange failed: {row}')
        time.sleep(.2)
    raise TimeoutError(f'{relay.name}: no custody answer for {transient_id[:8]}')


def run_case(root, scenario):
    lab = Lab(root, scenario)
    try:
        key, destination = credential(root)
        relays = {name: lab.launch(name) for name in 'ABC'}
        origin = lab.launch('O', 'ABC')
        source = {k: origin.info[k] for k in ('destination', 'public_key')}
        content = hashlib.shake_256(f'dethron-v1:{scenario}'.encode()).digest(PROFILE['payload_bytes'])
        parts = split(content, PROFILE['parts'], OBJECT_ID)
        expires = int(time.time())+3600
        inputs = {name: data_envelope(source['destination'], destination['destination'],
                                      encode(parts[index]), expires) for index, name in enumerate('ABC')}
        (root/'manifest.json').write_text(json.dumps(
            {'scenario': scenario, 'source': source, 'destination': destination,
             'relays': {name: lab.public(node) for name, node in relays.items()},
             'placement': {name: index for index, name in enumerate('ABC')},
             'object': parts[0]['manifest'], 'expires': expires, 'inputs': inputs,
             'fake_transient_id': FAKE if scenario == 'fake' else None}, indent=2))
        time.sleep(2)
        for node in list(relays.values())+[origin]:
            node.request('announce')
        time.sleep(4)
        handoffs, inventories = {}, {}
        for name in 'ABC':
            origin.request('send', label=name, body=base64.b64encode(encode(inputs[name])).decode(),
                           recipient=destination, propagation=relays[name].info['propagation'])
            handoff = origin.wait('handoff', label=name, timeout=180)
            handoffs[name] = handoff['transient_id']
            deadline = time.monotonic()+60
            while relays[name].status()['stored'] != 1:
                if time.monotonic() > deadline:
                    raise TimeoutError(f'{name}: message not persisted')
                time.sleep(.2)
            inventories[name] = relays[name].status()['inventory']
            lab.record('handoff', relay=name, transient_id=handoffs[name], inventory=inventories[name])
        custody = {name: ask_custody(lab, origin, relays[name], handoffs[name]) for name in 'ABC'}
        if scenario == 'fake':
            custody['fake'] = ask_custody(lab, origin, relays['A'], FAKE)
        lab.retire(origin)
        if scenario == 'discarded':
            relays['B'].request('discard', transient_id=handoffs['B'])
            lab.record('discard', relay='B', transient_id=handoffs['B'], stored=relays['B'].status()['stored'])
        fetches = []
        if scenario != 'pending':
            receiver = lab.launch('D', 'ABC', {'credential': str(key), 'limit_kb': 256})
            if receiver.info['destination'] != destination['destination']:
                raise ValueError('recipient identity changed')
            for name in 'ABC':
                fetches.append(lab.fetch(receiver, relays[name], source))
        completed = bool(fetches and fetches[-1]['receiver']['completed'])
        if completed != EXPECTED[scenario]:
            raise ValueError(f'{scenario}: completion {completed} contradicts the declared expectation')
        report = {'scenario': scenario, 'completed': completed, 'handoffs': handoffs,
                  'custody': {name: row['kind'] for name, row in custody.items()},
                  'relay_stored': {name: node.status()['stored'] for name, node in relays.items()},
                  'fetches': len(fetches)}
        lab.record('case_finished', **report)
        return report
    finally:
        lab.close()
