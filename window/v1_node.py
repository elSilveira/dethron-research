"""Native LXMF node with custody and receipt return; proof handling lives in v1_handlers."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

import LXMF
import RNS

from dethron_gateway import custody
from dethron_gateway import lxmf_stamp
from g2_receiver import Receiver
from g3_process import lines
import v1_handlers as handlers

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
    relay = name[0] in 'ABC'
    receiver = Receiver(home, source, 'split', emit) if name.startswith('D') else None
    if relay:
        router.enable_propagation()
    ctx = SimpleNamespace(home=home, name=name, emit=emit, router=router, source=source, identity=identity,
                          expected={}, recipients=handlers.load_recipients(home),
                          custody=home/'custody', receipts=home/'receipts')
    for folder in (ctx.custody, ctx.receipts):
        folder.mkdir(exist_ok=True)

    def on_delivery(message):
        if receiver:
            return receiver.receive(message)
        try:
            kind = custody.peek(message.packed, time.time())['kind']
            if kind == 'custody_request':
                threading.Thread(target=handlers.guarded, args=(ctx, handlers.answer_custody, message),
                                 daemon=True).start()
            elif kind in ('custody', 'custody_refusal'):
                handlers.collect_custody(ctx, message, kind)
            elif kind == 'receipt':
                handlers.collect_receipt(ctx, message)
            else:
                raise ValueError(f'unexpected message kind: {kind}')
        except Exception as exc:
            emit('rejected', error=repr(exc))

    router.register_delivery_callback(on_delivery)

    def handle(command):
        action = command['action']
        if action == 'announce':
            if relay:
                router.announce_propagation_node()
            router.announce(source.hash)
            return {}
        if action == 'send':
            recipient = command['recipient']
            handlers.remember_recipient(ctx, recipient['destination'], recipient['public_key'])
            router.set_outbound_propagation_node(bytes.fromhex(command['propagation']))
            msg = LXMF.LXMessage(handlers.target_for(recipient['public_key'], recipient['destination']), source,
                                 base64.b64decode(command['body'], validate=True), 'dethron-g1',
                                 desired_method=LXMF.LXMessage.PROPAGATED)
            label = command['label']
            msg.register_delivery_callback(lambda m, label=label: emit(
                'handoff', label=label, packed_bytes=len(m.packed), transient_id=m.transient_id.hex()))
            msg.register_failed_callback(lambda m, label=label: emit('send_failed', label=label))
            router.handle_outbound(msg)
            return {'label': label}
        if action == 'custody':
            return handlers.request_custody(ctx, command)
        if action == 'publish_receipt':
            return handlers.publish_receipt(ctx, command)
        if action == 'discard':
            entry = router.propagation_entries.pop(bytes.fromhex(command['transient_id']), None)
            if entry is None:
                raise ValueError('transient id not in store')
            os.remove(entry[1])
            return {'discarded': command['transient_id']}
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
                    'inventory': sorted(hashlib.sha256(p.read_bytes()).hexdigest() for p in files),
                    'custody': sorted(p.name for p in ctx.custody.glob('*')),
                    'receipts': sorted(p.name for p in ctx.receipts.glob('*')),
                    'metrics': {'tx': sum(i.txb for i in interfaces), 'rx': sum(i.rxb for i in interfaces)},
                    'receiver': receiver.status() if receiver else None}
        raise ValueError(f'unknown command: {action}')

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
