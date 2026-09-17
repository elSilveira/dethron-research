"""One G4 case: distribute over the declared path, then consume it or fail visibly."""
import base64
import hashlib
import json
import time

import RNS

from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from g4_contract import PROFILE, expected_delivery, pipe_bridge, tcp_contact, tcp_listener
from g4_lab import Lab
from gateway_scenario import ports

OBJECT_ID = 'a'*32
LINKS = {'O': 'or', 'D': 'dr'}


def interfaces(lab, scenario, role, port):
    """The relay holds one end of each link; origin and receiver hold the other."""
    if scenario == 'ip':
        return [tcp_listener(port)] if role == 'A' else [tcp_contact(0, port)]
    if role == 'A':
        return [pipe_bridge(lab.command(link, 'a'), f'Bridge{peer}') for peer, link in LINKS.items()]
    return [pipe_bridge(lab.command(LINKS[role], 'b'), 'BridgeRelay')]


def credential(lab):
    folder = lab.root/'credentials'
    folder.mkdir(exist_ok=True)
    key = folder/'destination.key'
    identity = RNS.Identity()
    identity.to_file(str(key))
    return key, {'destination': RNS.Destination.hash(identity, 'lxmf', 'delivery').hex(),
                 'public_key': identity.get_public_key().hex()}


def attempt(lab, receiver, relay, source, timeout):
    """A fetch that is allowed to fail: an unreachable relay is a result, not a crash."""
    relay.request('announce')
    time.sleep(2)
    receiver.request('fetch', source=source, propagation=relay.info['propagation'],
                     limit_kb=256, timeout=60)
    deadline, state = time.monotonic()+timeout, None
    while time.monotonic() < deadline:
        state = receiver.status()
        if state['receiver']['completed']:
            break
        time.sleep(.5)
    return lab.record('fetch_attempt', sync=state['sync'], receiver=state['receiver'],
                      completed=bool(state['receiver']['completed']))


def run_case(root, scenario):
    lab = Lab(root, scenario)
    try:
        port = ports(1)[0]
        if scenario != 'ip':
            for link in LINKS.values():
                lab.open_channel(link)
        key, destination = credential(lab)
        settings = {'limit_kb': 256}
        relay = lab.launch('A', interfaces(lab, scenario, 'A', port), settings)
        origin = lab.launch('O', interfaces(lab, scenario, 'O', port), settings)
        content = hashlib.shake_256(f'dethron-g4-v1:{scenario}'.encode()).digest(PROFILE['payload_bytes'])
        part = split(content, 1, OBJECT_ID)[0]
        expires = int(time.time())+3600
        envelope = data_envelope(origin.info['destination'], destination['destination'],
                                 encode(part), expires)
        (root/'manifest.json').write_text(json.dumps(
            {'scenario': scenario, 'source': {k: origin.info[k] for k in ('destination', 'public_key')},
             'destination': destination, 'object': part['manifest'], 'expires': expires,
             'input': envelope}, indent=2))
        time.sleep(2)
        relay.request('announce')
        time.sleep(3)
        origin.request('send', label='object', body=base64.b64encode(encode(envelope)).decode(),
                       recipient=destination, propagation=relay.info['propagation'])
        origin.wait('handoff', label='object', timeout=240)
        deadline = time.monotonic()+90
        while relay.status()['stored'] != 1:
            if time.monotonic() > deadline:
                raise TimeoutError('the relay never persisted the object')
            time.sleep(.25)
        lab.record('distributed', stored=1, path='ip' if scenario == 'ip' else 'bridge')
        source = {k: origin.info[k] for k in ('destination', 'public_key')}
        lab.stop(origin)
        if scenario in ('dark', 'cut'):
            lab.cut(LINKS['D'])
        receiver = lab.launch('D', interfaces(lab, scenario, 'D', port), {**settings, 'credential': str(key)})
        if receiver.info['destination'] != destination['destination']:
            raise ValueError('the recipient identity changed')
        isolation = lab.ip_evidence('during-delivery')
        attempts = [attempt(lab, receiver, relay, source, PROFILE['deadline_seconds'] if scenario
                            not in ('dark', 'cut') else 45)]
        if scenario == 'cut':
            lab.restore(LINKS['D'])
            attempts.append(attempt(lab, receiver, relay, source, PROFILE['deadline_seconds']))
        completed = attempts[-1]['completed']
        if completed != expected_delivery(scenario):
            raise ValueError(f'{scenario}: delivery {completed} contradicts the declared expectation')
        report = {'scenario': scenario, 'completed': completed, 'attempts': attempts,
                  'relay_stored': relay.status()['stored'], 'ledger': lab.ledger(),
                  'ip_endpoints': isolation['endpoints'], 'audited_pids':
                  {'nodes': isolation['nodes'], 'bridges': isolation['bridges']}}
        lab.record('case_finished', **{k: v for k, v in report.items() if k != 'attempts'})
        return report
    finally:
        lab.close()
