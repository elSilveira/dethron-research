"""Build the bench: mint the identities, compute every address, and fix both schedules.

Nothing here runs during the window. Its whole job is to make the window unnecessary
to steer: identities are minted in advance so their destination hashes can be computed
without starting a node, and every step therefore carries the address it needs.
"""
import base64
import hashlib
import json
from pathlib import Path
import time

import RNS

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from v3_schedule import plan, schedule, step

PROFILE = {'version': 1, 'payload_bytes': 16384, 'window_seconds': 240, 'lead_seconds': 120,
           'object_id': 'c'*32, 'ports': {'A': 45810, 'O': 45811, 'D': 45812}}


def mint(folder, name):
    """A lab identity, written before the window so its addresses are knowable."""
    folder.mkdir(parents=True, exist_ok=True)
    key = folder/f'{name}.key'
    identity = RNS.Identity()
    identity.to_file(str(key))
    return {'name': name, 'public_key': identity.get_public_key().hex(),
            'delivery': RNS.Destination.hash(identity, 'lxmf', 'delivery').hex(),
            'propagation': RNS.Destination.hash(identity, 'lxmf', 'propagation').hex()}


def build(root, relay_host, window_seconds=None, lead_seconds=None):
    """One relay and origin on alpha, the recipient on beta, across the network."""
    root = Path(root)
    control = root/'control'
    identities = control/'identities'
    window = window_seconds or PROFILE['window_seconds']
    lead = lead_seconds if lead_seconds is not None else PROFILE['lead_seconds']
    who = {name: mint(identities, name) for name in ('A', 'O', 'D')}
    ports = PROFILE['ports']

    content = hashlib.shake_256(b'dethron-v3a-v1').digest(PROFILE['payload_bytes'])
    part = split(content, 1, PROFILE['object_id'])[0]
    expires = int(time.time())+7200
    envelope = data_envelope(who['O']['delivery'], who['D']['delivery'], encode(part), expires)
    body = base64.b64encode(encode(envelope)).decode()

    alpha = schedule('alpha', window, [
        step(0, 'launch', node='A', role='relay', port=ports['A'], contacts=[], credential='A'),
        step(8, 'launch', node='O', role='origin', port=ports['O'],
             contacts=[f"127.0.0.1:{ports['A']}"], credential='O'),
        step(20, 'announce', node='A'),
        step(26, 'announce', node='O'),
        step(34, 'send', node='O', label='object', body=body,
             recipient=who['D']['delivery'], recipient_key=who['D']['public_key'],
             propagation=who['A']['propagation']),
        step(90, 'status', node='A'),
        step(100, 'stop', node='O'),
        step(window, 'status', node='A'),
    ])
    beta = schedule('beta', window, [
        step(0, 'launch', node='D', role='receiver', port=ports['D'],
             contacts=[f"{relay_host}:{ports['A']}"], credential='D'),
        step(30, 'announce', node='D'),
        step(130, 'fetch', node='D', source=who['O']['delivery'], source_key=who['O']['public_key'],
             propagation=who['A']['propagation'], limit_kb=256),
        step(170, 'fetch', node='D', source=who['O']['delivery'], source_key=who['O']['public_key'],
             propagation=who['A']['propagation'], limit_kb=256),
        step(window, 'status', node='D'),
    ])

    bench = plan([alpha, beta], start_wall=time.time()+lead)
    control.mkdir(parents=True, exist_ok=True)
    (control/'plan.json').write_text(json.dumps(bench, indent=2), encoding='utf-8')
    (control/'manifest.json').write_text(json.dumps(
        {'profile': PROFILE, 'relay_host': relay_host, 'identities': who,
         'object': part['manifest'], 'expires': expires, 'input': envelope,
         'digest': hashlib.sha256(content).hexdigest()}, indent=2), encoding='utf-8')
    return bench
