"""Run one real LXMF comparison with identical placement and explicit accounting."""
import base64
import hashlib
import json
import time

from dethron_gateway.erasure import parity_split
from dethron_gateway.parts import split
from dethron_gateway.protocol import data_envelope, encode
from g2_compare_contract import PROFILE, eligible, expected_completion
from g2_lab import Lab


def file_sizes(root):
    return {p.name: sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
            for p in root.iterdir() if p.is_dir()}


def run_case(root, case):
    lab = Lab(root, case['mode'])
    try:
        receiver = lab.start('D')
        destination = receiver.info
        lab.stop(receiver)
        relays = {n: lab.start(n) for n in 'ABC'}
        sender = lab.start('O', 'ABC')
        source = sender.info
        content = hashlib.shake_256(f"g2-expanded-v1:{case['repeat']}".encode()).digest(PROFILE['payload_bytes'])
        began = time.perf_counter()
        parts = parity_split(content, 'e'*32) if case['mode'] == 'xor2' else split(content, 3, 'e'*32)
        expires = int(time.time())+3600
        inputs = {n: data_envelope(source['destination'], destination['destination'],
                  content if case['mode'] == 'whole' else encode(parts[i]), expires,
                  'e'*32 if case['mode'] == 'whole' else None) for i, n in enumerate('ABC')}
        encode_seconds = time.perf_counter()-began
        manifest = {'case': case, 'profile': PROFILE, 'source': source, 'destination': destination,
                    'object': parts[0]['manifest'], 'expires': expires, 'inputs': inputs}
        (root/'manifest.json').write_text(json.dumps(manifest, indent=2))
        time.sleep(2)
        for relay in relays.values():
            relay.send('announce')
        time.sleep(2)
        submitted = 0
        for name in 'ABC':
            sender.send('send', label=name, body=base64.b64encode(encode(inputs[name])).decode(),
                        recipient=destination, propagation=relays[name].info['propagation'])
            submitted += sender.wait('handoff', label=name, timeout=180)['packed_bytes']
            deadline = time.monotonic()+30
            while relays[name].status()['stored'] != 1:
                if time.monotonic() > deadline:
                    raise TimeoutError('relay persistence timeout')
                time.sleep(.1)
        lab.stop(sender)
        sender.home.rename(root/'O.offline')
        tx_distribution = lab.measure()
        distribution_files = file_sizes(root)
        snapshots, storage_samples = [], [distribution_files]
        began = time.monotonic()
        for generation, name in enumerate(case['contacts'], 1):
            receiver = lab.start('D', [name], generation)
            if receiver.info['destination'] != destination['destination']:
                raise ValueError('identity changed')
            state = lab.fetch(receiver, relays[name], source, case['limit_kb'])
            packet_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (root/'D'/'packets').glob('*.lxmf')}
            lab.record('contact_evidence', relay=name, receiver=state, packets=packet_hashes)
            if state['completed'] != expected_completion(case['mode'], case['scenario'], generation):
                raise ValueError('unexpected completion')
            snapshots.append(state)
            storage_samples.append(file_sizes(root))
            lab.stop(receiver)
        elapsed = time.monotonic()-began
        if elapsed > PROFILE['deadline_seconds']:
            raise TimeoutError('contact deadline exceeded')
        tx_total = lab.measure()
        files_peak = max(sum(s.values()) for s in storage_samples)
        report = {**case, 'completed': snapshots[-1]['completed'], 'contact_seconds': elapsed,
                  'encode_seconds': encode_seconds, 'submitted_lxmf_bytes': submitted,
                  'tx_distribution': tx_distribution, 'tx_contacts': tx_total-tx_distribution,
                  'tx_total_sampled': tx_total, 'file_bytes_peak_sampled': files_peak,
                  'file_samples': storage_samples, 'eligible': eligible(tx_total, files_peak)}
        if not report['eligible']:
            raise ValueError('predeclared resource budget exceeded')
        lab.record('case_passed', **report)
        return report
    finally:
        lab.close()
