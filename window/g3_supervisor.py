"""One generation of supervision: a fresh process resuming only from public files."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import RNS

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from g3_access import install, probe
from g3_contract import load_checkpoint, write_checkpoint
from g3_lab import Lab

PAYLOAD_BYTES = 24576
OBJECT_ID = 'f'*32
LIFETIME = 3600


def endpoint(info):
    return {'destination': info['destination'], 'public_key': info['public_key']}


def seed(root, mode):
    """Provision the declared credential, distribute exact parts, then retire the origin."""
    lab = Lab(root, 'seed')
    (root/'credentials').mkdir(parents=True, exist_ok=True)
    key = root/'credentials'/'destination.key'
    identity = RNS.Identity()
    identity.to_file(str(key))
    destination = {'destination': RNS.Destination.hash(identity, 'lxmf', 'delivery').hex(),
                   'public_key': identity.get_public_key().hex()}
    lab.record('provisioned', credential=str(key), destination=destination['destination'])
    relays = {name: lab.launch(f'{name}0') for name in 'ABC'}
    origin = lab.launch('O', [f'{name}0' for name in 'ABC'])
    source = endpoint(origin.info)
    content = hashlib.shake_256(b'dethron-g3-v1').digest(PAYLOAD_BYTES)
    parts = split(content, 3, OBJECT_ID)
    expires = int(time.time())+LIFETIME
    inputs = {name: data_envelope(source['destination'], destination['destination'],
                                  encode(parts[index]), expires) for index, name in enumerate('ABC')}
    (root/'manifest.json').write_text(json.dumps(
        {'mode': mode, 'source': source, 'destination': destination, 'object': parts[0]['manifest'],
         'expires': expires, 'inputs': inputs}, indent=2))
    time.sleep(2)
    for relay in relays.values():
        relay.request('announce')
    time.sleep(2)
    for name in 'ABC':
        origin.request('send', label=name, body=base64.b64encode(encode(inputs[name])).decode(),
                       recipient=destination, propagation=relays[name].info['propagation'])
        origin.wait('handoff', label=name, timeout=180)
        deadline = time.monotonic()+60
        while relays[name].status()['stored'] != 1:
            if time.monotonic() > deadline:
                raise TimeoutError(f'{name}0: message was not persisted before the origin left')
            time.sleep(.2)
    lab.retire(origin)
    state = {'version': 1, 'generation': 0, 'mode': mode, 'source': source, 'destination': destination,
             'object': {'id': OBJECT_ID, 'size': PAYLOAD_BYTES, 'digest': parts[0]['manifest']['digest']},
             'expires': expires,
             'relays': {name: {**lab.public(relays[name]), 'inventory': relays[name].status()['inventory']}
                        for name in 'ABC'}}
    write_checkpoint(root, state)
    return {'origin_retired': True, 'object': state['object'],
            'relays': {name: state['relays'][name]['destination'] for name in 'ABC'}}


def generation(root, number, mode):
    """Replace every carrier of the previous generation over the network, then retire it."""
    previous = load_checkpoint(root, number-1)
    if previous['mode'] != mode:
        raise ValueError('checkpoint scenario does not match this run')
    lab = Lab(root, f'generation-{number}')
    old = {name: lab.attach(f'{name}{number-1}', previous['relays'][name]) for name in 'ABC'}
    new = {}
    for name in 'ABC':
        new[name] = lab.launch(f'{name}{number}', [f'{name}{number-1}'])
        lab.handover(old[name], new[name], previous['relays'][name]['inventory'])
    for name in 'ABC':
        lab.retire(old[name])
    state = {**previous, 'generation': number,
             'relays': {name: {**lab.public(new[name]), 'inventory': new[name].status()['inventory']}
                        for name in 'ABC'}}
    write_checkpoint(root, state)
    return {'generation': number, 'retired': [f'{name}{number-1}' for name in 'ABC'],
            'relays': {name: state['relays'][name]['destination'] for name in 'ABC'}}


def deliver(root, mode):
    """Consume the service from the last generation, or refuse without the declared credential."""
    state = load_checkpoint(root, 2)
    lab = Lab(root, 'deliver')
    relays = {name: lab.attach(f'{name}2', state['relays'][name]) for name in 'ABC'}
    credential = root/'credentials'/'destination.key'
    settings = {'credential': str(credential), 'limit_kb': 256}
    try:
        if mode == 'missing':
            credential.unlink()
            lab.record('withdrawn', resource=str(credential), declared='recipient credential')
            try:
                lab.launch('D', ['A2'], settings)
            except Exception as exc:
                rows = [json.loads(s) for s in (root/'D'/'events.jsonl').read_text().splitlines()]
                refusals = [row for row in rows if row['event'] == 'refused']
                if not refusals:
                    raise
                lab.record('refused', reason=refusals[-1]['reason'],
                           credential=refusals[-1]['credential'], node='D')
                return {'completed': False, 'refused': True, 'reason': refusals[-1]['reason'],
                        'error': repr(exc)}
            raise ValueError('service continued after the declared credential was withdrawn')
        contacts = []
        for index, name in enumerate('ABC'):
            receiver = lab.launch('D', [f'{name}2'], settings, reuse=index > 0)
            if receiver.info['destination'] != state['destination']['destination']:
                raise ValueError('recipient identity changed across generations')
            contacts.append(lab.fetch(receiver, relays[name], state['source']))
            receiver.kill()
        lab.record('delivered', receiver=contacts[-1])
        return {'completed': bool(contacts[-1]['completed']), 'refused': False,
                'sha256': contacts[-1]['sha256'], 'contacts': contacts}
    finally:
        lab.shutdown()


def main():
    root, phase, mode = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    install(root)
    if probe(root, 'O/identity') is False:
        raise PermissionError('a retired generation is still reachable from this supervisor')
    if phase == 'seed':
        result = seed(root, mode)
    elif phase == 'deliver':
        result = deliver(root, mode)
    else:
        result = generation(root, int(phase), mode)
    print(json.dumps({'phase': phase, 'mode': mode, 'supervisor_pid': os.getpid(),
                      'guard': probe(root, 'O/identity'), **result}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
