"""Native LXMF carrier driven through files, so any supervisor generation can attach."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import LXMF
import RNS

from dethron_gateway import lxmf_stamp
from g2_receiver import Receiver
from g3_process import lines

REFUSED = 24


def load_identity(home, settings, emit):
    """A declared credential is indispensable: its absence refuses service, loudly."""
    if 'credential' in settings:
        key = Path(settings['credential'])
        if not key.exists():
            emit('refused', reason='declared credential is absent', credential=str(key))
            sys.exit(REFUSED)
    else:
        key = home/'identity'
    identity = RNS.Identity.from_file(str(key)) if key.exists() else RNS.Identity()
    if identity is None:
        emit('refused', reason='declared credential is unreadable', credential=str(key))
        sys.exit(REFUSED)
    if not key.exists():
        identity.to_file(str(key))
    return identity


def main():
    home, name = Path(sys.argv[1]), sys.argv[2]
    settings = json.loads((home/'settings.json').read_text())
    events, lock = home/'events.jsonl', threading.Lock()

    def emit(event, **values):
        with lock, events.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event': event, 'time': time.time(), **values})+'\n')

    # A stamp discarded by a log line silently stops peering; install before router work.
    stamp_defect = lxmf_stamp.install()
    RNS.Reticulum(configdir=str(home/'rns'), loglevel=3, logdest=RNS.LOG_FILE)
    identity = load_identity(home, settings, emit)
    router = LXMF.LXMRouter(identity=identity, storagepath=str(home), autopeer=False,
                            propagation_limit=2048, delivery_limit=settings.get('limit_kb', 256),
                            sync_limit=8192, peering_cost=1, propagation_cost=1)
    source = router.register_delivery_identity(identity, display_name=name, stamp_cost=None)
    receiver = Receiver(home, source, 'split', emit) if name.startswith('D') else None
    if receiver:
        router.register_delivery_callback(receiver.receive)
    if name[0] in 'ABC':
        router.enable_propagation()

    def inventory():
        return sorted(hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (home/'lxmf'/'messagestore').glob('*') if p.is_file())

    def handle(command):
        action = command['action']
        if action == 'announce':
            router.announce_propagation_node()
            return {}
        if action == 'send':
            peer = RNS.Identity(create_keys=False)
            peer.load_public_key(bytes.fromhex(command['recipient']['public_key']))
            target = RNS.Destination(peer, RNS.Destination.OUT, RNS.Destination.SINGLE, 'lxmf', 'delivery')
            router.set_outbound_propagation_node(bytes.fromhex(command['propagation']))
            msg = LXMF.LXMessage(target, source, base64.b64decode(command['body'], validate=True),
                                 'dethron-g1', desired_method=LXMF.LXMessage.PROPAGATED)
            label = command['label']
            msg.register_delivery_callback(lambda m, label=label: emit('handoff', label=label, packed_bytes=len(m.packed)))
            msg.register_failed_callback(lambda m, label=label: emit('send_failed', label=label))
            router.handle_outbound(msg)
            return {'label': label}
        if action == 'peer':
            peer = command['peer']
            address = bytes.fromhex(peer['propagation'])
            RNS.Identity.remember(None, address, bytes.fromhex(peer['public_key']))
            # LXMF postpones a peer by SYNC_BACKOFF_STEP (12 minutes) when a sync is asked
            # before a path exists, and every later sync is then refused as "not yet due".
            # With autopeer off the lab drives syncing, so it must wait for the path first.
            if not RNS.Transport.has_path(address):
                RNS.Transport.request_path(address)
                deadline = time.monotonic()+command.get('path_wait', 45)
                while not RNS.Transport.has_path(address) and time.monotonic() < deadline:
                    time.sleep(.25)
            path = RNS.Transport.has_path(address)
            router.peer(address, time.time(), 2048, 8192, 1, 0, 1, None)
            native = router.peers[address]
            # The lab, not LXMF's scheduler, decides when to retry here.
            native.next_sync_attempt, native.sync_backoff = 0, 0
            for tid in list(router.propagation_entries):
                native.queue_unhandled_message(tid)
            native.process_queues()
            native.sync()
            return {'queued': len(router.propagation_entries), 'path': path}
        if action == 'fetch':
            peer = command['source']
            RNS.Identity.remember(None, bytes.fromhex(peer['destination']), bytes.fromhex(peer['public_key']))
            router.acknowledge_sync_completion(reset_state=True)
            router.delivery_per_transfer_limit = command.get('limit_kb', settings.get('limit_kb', 256))
            router.set_outbound_propagation_node(bytes.fromhex(command['propagation']))
            router.request_messages_from_propagation_node(identity)
            return {}
        if action == 'status':
            files = [p for p in (home/'lxmf'/'messagestore').glob('*') if p.is_file()]
            interfaces = [i for i in RNS.Transport.interfaces if getattr(i, 'parent_interface', None) is None]
            return {'stored': len(router.propagation_entries), 'sync': router.propagation_transfer_state,
                    'inventory': inventory(), 'store_bytes': sum(p.stat().st_size for p in files),
                    'metrics': {'tx': sum(i.txb for i in interfaces), 'rx': sum(i.rxb for i in interfaces)},
                    'receiver': receiver.status() if receiver else None}
        raise ValueError(f'unknown command: {action}')

    # A new incarnation answers only what is asked of it, never a predecessor's commands.
    commands = home/'commands.jsonl'
    seen = len(lines(commands))
    emit('ready', stamp_workaround=stamp_defect, pid=os.getpid(), destination=source.hash.hex(),
         public_key=identity.get_public_key().hex(), propagation=router.propagation_destination.hash.hex())
    while True:
        pending = lines(commands)
        for line in pending[seen:]:
            command = json.loads(line)
            if command['action'] == 'crash':
                os._exit(23)
            try:
                emit(command['action'], rid=command['rid'], **handle(command))
            except Exception as exc:
                emit('error', rid=command['rid'], action=command['action'], error=repr(exc))
        seen = len(pending)
        time.sleep(.02)


if __name__ == '__main__':
    main()
