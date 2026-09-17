"""V1, second half: the recipient's receipt returns to an origin that was never online with it."""
import base64
import hashlib
import json
import time

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from v1_lab import Lab
from v1_scenario import OBJECT_ID, ask_custody, credential

PROFILE = {'version': 1, 'payload_bytes': 24576, 'parts': 3, 'publish_wait_seconds': 120,
           'return_wait_seconds': 30, 'scenarios': ['returned', 'proof_pending', 'never_completed']}
FETCHES = {'returned': 'ABC', 'proof_pending': 'ABC', 'never_completed': 'AB'}
VISITS = {'returned': 'C', 'proof_pending': 'CA', 'never_completed': 'ABC'}
EXPECTED = {'returned': {'completed': True, 'proof_via': 'C'},
            'proof_pending': {'completed': True, 'proof_via': 'A'},
            'never_completed': {'completed': False, 'proof_via': None}}


def publish(lab, receiver, relay, origin):
    """One relay at a time: the outbound propagation node is read when the message is processed."""
    receiver.request('publish_receipt', label=relay.name, propagation=relay.info['propagation'], origin=origin)
    published = receiver.wait('receipt_published', label=relay.name, timeout=PROFILE['publish_wait_seconds'])
    deadline = time.monotonic()+60
    while relay.status()['stored'] < 1:
        if time.monotonic() > deadline:
            raise TimeoutError(f'{relay.name}: receipt copy was not stored')
        time.sleep(.2)
    return lab.record('receipt_stored', relay=relay.name, transient_id=published['transient_id'],
                      inventory=relay.status()['inventory'])


def visit(lab, origin, relay, recipient):
    """The returning origin asks one relay; a receipt either arrives or visibly does not."""
    before = sum(1 for row in origin._read() if row['event'] == 'receipt_received')
    lab.fetch(origin, relay, recipient)
    deadline = time.monotonic()+PROFILE['return_wait_seconds']
    while time.monotonic() < deadline:
        received = [row for row in origin._read() if row['event'] == 'receipt_received']
        if len(received) > before:
            return lab.record('return_visit', relay=relay.name, receipt=True, receipt_id=received[-1]['id'])
        time.sleep(.25)
    return lab.record('return_visit', relay=relay.name, receipt=False)


def run_case(root, scenario):
    lab = Lab(root, scenario)
    try:
        key, destination = credential(root)
        relays = {name: lab.launch(name) for name in 'ABC'}
        origin = lab.launch('O', 'ABC')
        source = {k: origin.info[k] for k in ('destination', 'public_key')}
        content = hashlib.shake_256(f'dethron-v1-return:{scenario}'.encode()).digest(PROFILE['payload_bytes'])
        parts = split(content, PROFILE['parts'], OBJECT_ID)
        expires = int(time.time())+3600
        inputs = {name: data_envelope(source['destination'], destination['destination'],
                                      encode(parts[index]), expires) for index, name in enumerate('ABC')}
        (root/'manifest.json').write_text(json.dumps(
            {'scenario': scenario, 'source': source, 'destination': destination,
             'relays': {name: lab.public(node) for name, node in relays.items()},
             'placement': {name: index for index, name in enumerate('ABC')},
             'object': parts[0]['manifest'], 'expires': expires, 'inputs': inputs,
             'fetches': list(FETCHES[scenario]), 'visits': list(VISITS[scenario])}, indent=2))
        time.sleep(2)
        for node in list(relays.values())+[origin]:
            node.request('announce')
        time.sleep(4)
        handoffs = {}
        for name in 'ABC':
            origin.request('send', label=name, body=base64.b64encode(encode(inputs[name])).decode(),
                           recipient=destination, propagation=relays[name].info['propagation'])
            handoffs[name] = origin.wait('handoff', label=name, timeout=180)['transient_id']
            deadline = time.monotonic()+60
            while relays[name].status()['stored'] != 1:
                if time.monotonic() > deadline:
                    raise TimeoutError(f'{name}: message not persisted')
                time.sleep(.2)
            lab.record('handoff', relay=name, transient_id=handoffs[name], inventory=relays[name].status()['inventory'])
        for name in 'ABC':
            ask_custody(lab, origin, relays[name], handoffs[name])
        lab.stop(origin)
        receiver = lab.launch('D', 'ABC', {'credential': str(key), 'limit_kb': 256})
        if receiver.info['destination'] != destination['destination']:
            raise ValueError('recipient identity changed')
        for name in FETCHES[scenario]:
            lab.fetch(receiver, relays[name], source)
        completed = bool(receiver.status()['receiver']['completed'])
        if completed != EXPECTED[scenario]['completed']:
            raise ValueError(f'{scenario}: completion {completed} contradicts the declared expectation')
        copies = {}
        if completed:
            for name in 'ABC':
                copies[name] = publish(lab, receiver, relays[name], source)['transient_id']
            if scenario == 'proof_pending':
                relays['C'].request('discard', transient_id=copies['C'])
                lab.record('discard', relay='C', transient_id=copies['C'], stored=relays['C'].status()['stored'])
        lab.stop(receiver)
        origin = lab.launch('O', 'ABC', reuse=True)
        if origin.info['destination'] != source['destination']:
            raise ValueError('origin identity changed across its offline period')
        visits = [visit(lab, origin, relays[name], destination) for name in VISITS[scenario]]
        proof_via = next((row['relay'] for row in visits if row['receipt']), None)
        if proof_via != EXPECTED[scenario]['proof_via']:
            raise ValueError(f'{scenario}: proof via {proof_via} contradicts the declared expectation')
        report = {'scenario': scenario, 'completed': completed, 'handoffs': handoffs, 'receipt_copies': copies,
                  'proof_via': proof_via, 'visits': [(row['relay'], row['receipt']) for row in visits]}
        lab.record('case_finished', **report)
        return report
    finally:
        lab.close()
