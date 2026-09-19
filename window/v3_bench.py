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
# A serial link is slower than a LAN and its paths take longer to settle, so the serial
# bench gives every stage more room. The IP timings are left exactly as V3a ran them.
SERIAL = {'speed': 115200, 'window_seconds': 480, 'lead_seconds': 180}
# Over IP both machines may open at once: a listening socket exists whether or not anyone
# connects. A serial link is not symmetric. One end waits and the other dials, and the
# dialling end cannot open its port at all until the waiting end holds its own — on a
# Bluetooth port that is error 1168, which reads as a port that does not exist. So the
# relay opens first and the recipient follows, and no write crosses the link until both
# ends are on it, because a write to an unconnected serial port never returns.
TIMES = {
    'ip': {'relay': 0, 'origin': 8, 'announce_a': 20, 'announce_o': 26, 'send': 34,
           'status': 90, 'stop': 100, 'receiver': 0, 'announce_d': 30, 'fetch': (130, 170)},
    'serial': {'relay': 0, 'origin': 15, 'announce_a': 60, 'announce_o': 75, 'send': 90,
               'status': 240, 'stop': 300, 'receiver': 30, 'announce_d': 70,
               'fetch': (240, 320, 400)},
}


def mint(folder, name):
    """A lab identity, written before the window so its addresses are knowable."""
    folder.mkdir(parents=True, exist_ok=True)
    key = folder/f'{name}.key'
    identity = RNS.Identity()
    identity.to_file(str(key))
    return {'name': name, 'public_key': identity.get_public_key().hex(),
            'delivery': RNS.Destination.hash(identity, 'lxmf', 'delivery').hex(),
            'propagation': RNS.Destination.hash(identity, 'lxmf', 'propagation').hex()}


def build(root, relay_host=None, window_seconds=None, lead_seconds=None, serial=None):
    """One relay and origin on alpha, the recipient on beta.

    `serial` names the COM port on each machine and makes the link between them the only
    medium the recipient has: its node is given a serial interface and nothing else, so
    an object that arrives cannot have come over IP, because there was no IP to come
    over. Without it the machines meet over the network and `relay_host` is the relay
    machine's address.
    """
    root = Path(root)
    control = root/'control'
    if (control/'plan.json').exists():
        raise ValueError(f'{root} already holds a bench. A bench is single use: preparing a new '
                         f"one here would leave the previous run's nodes and evidence in place. "
                         f'Choose a new folder.')
    if bool(serial) == bool(relay_host):
        raise ValueError('give either a relay address, for a bench over the network, or a serial '
                         'port per machine, for a bench over a link that carries no IP')
    if serial and set(serial) != {'alpha', 'beta'}:
        raise ValueError('a serial bench needs the port on each machine: alpha and beta')
    medium = 'serial' if serial else 'ip'
    at = TIMES[medium]
    identities = control/'identities'
    window = window_seconds or (SERIAL if serial else PROFILE)['window_seconds']
    lead = lead_seconds if lead_seconds is not None else (SERIAL if serial else PROFILE)['lead_seconds']
    who = {name: mint(identities, name) for name in ('A', 'O', 'D')}
    ports = PROFILE['ports']

    content = hashlib.shake_256(b'dethron-v3a-v1').digest(PROFILE['payload_bytes'])
    part = split(content, 1, PROFILE['object_id'])[0]
    expires = int(time.time())+7200
    envelope = data_envelope(who['O']['delivery'], who['D']['delivery'], encode(part), expires)
    body = base64.b64encode(encode(envelope)).decode()

    relay_link = {'port': serial['alpha'], 'speed': SERIAL['speed']} if serial else None
    alpha = schedule('alpha', window, [
        step(at['relay'], 'launch', node='A', role='relay', port=ports['A'], contacts=[],
             credential='A', **({'serial': relay_link} if serial else {})),
        step(at['origin'], 'launch', node='O', role='origin', port=ports['O'],
             contacts=[f"127.0.0.1:{ports['A']}"], credential='O'),
        step(at['announce_a'], 'announce', node='A'),
        step(at['announce_o'], 'announce', node='O'),
        step(at['send'], 'send', node='O', label='object', body=body,
             recipient=who['D']['delivery'], recipient_key=who['D']['public_key'],
             propagation=who['A']['propagation']),
        step(at['status'], 'status', node='A'),
        step(at['stop'], 'stop', node='O'),
        step(window, 'status', node='A'),
    ])
    beta = schedule('beta', window, [
        step(at['receiver'], 'launch', node='D', role='receiver', port=ports['D'],
             contacts=[] if serial else [f"{relay_host}:{ports['A']}"], credential='D',
             **({'serial': {'port': serial['beta'], 'speed': SERIAL['speed'], 'only': True}}
                if serial else {})),
        step(at['announce_d'], 'announce', node='D'),
        *[step(when, 'fetch', node='D', source=who['O']['delivery'],
               source_key=who['O']['public_key'], propagation=who['A']['propagation'],
               limit_kb=256) for when in at['fetch']],
        step(window, 'status', node='D'),
    ])

    bench = plan([alpha, beta], start_wall=time.time()+lead)
    control.mkdir(parents=True, exist_ok=True)
    (control/'plan.json').write_text(json.dumps(bench, indent=2), encoding='utf-8')
    (control/'manifest.json').write_text(json.dumps(
        {'profile': PROFILE, 'relay_host': relay_host, 'medium': medium,
         'serial': serial, 'identities': who,
         'object': part['manifest'], 'expires': expires, 'input': envelope,
         'digest': hashlib.sha256(content).hexdigest()}, indent=2), encoding='utf-8')
    return bench
