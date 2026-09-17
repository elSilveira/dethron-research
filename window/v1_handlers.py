"""Custody and receipt handlers for v1_node: everything that signs, verifies or keeps proof."""
import json
from pathlib import Path
import time

import LXMF
import RNS

from dethron_gateway import custody
from dethron_gateway.protocol import encode
from dethron_gateway.wire import authenticate

STORE_WAIT = 10


def guarded(ctx, function, *args):
    try:
        function(ctx, *args)
    except Exception as exc:
        ctx.emit('rejected', error=repr(exc))


def target_for(public_key, destination):
    RNS.Identity.remember(None, bytes.fromhex(destination), bytes.fromhex(public_key))
    peer = RNS.Identity(create_keys=False)
    peer.load_public_key(bytes.fromhex(public_key))
    return RNS.Destination(peer, RNS.Destination.OUT, RNS.Destination.SINGLE, 'lxmf', 'delivery')


def direct(ctx, public_key, destination, obj, label):
    msg = LXMF.LXMessage(target_for(public_key, destination), ctx.source, encode(obj), 'dethron-g1',
                         desired_method=LXMF.LXMessage.DIRECT)
    msg.register_delivery_callback(lambda m: ctx.emit('direct_delivered', label=label))
    msg.register_failed_callback(lambda m: ctx.emit('direct_failed', label=label))
    ctx.router.handle_outbound(msg)


def request_custody(ctx, command):
    info, tid = command['relay'], command['transient_id']
    req = custody.request(ctx.source.hash.hex(), info['destination'], tid, ctx.identity.get_public_key().hex())
    ctx.expected[req['id']] = {'relay': info['name'], 'public_key': info['public_key'], 'transient_id': tid}
    direct(ctx, info['public_key'], info['destination'], req, f'request:{tid[:8]}')
    return {'request': req['id'], 'transient_id': tid}


def answer_custody(ctx, message):
    """Relay side: attest only what is really in the store; otherwise refuse explicitly."""
    known = RNS.Identity.recall(message.source_hash)
    req, key = custody.accept_request(message.packed, ctx.source.hash.hex(), time.time(),
                                      known.get_public_key() if known else None)
    tid, deadline = bytes.fromhex(req['transient_id']), time.monotonic()+STORE_WAIT
    while tid not in ctx.router.propagation_entries and time.monotonic() < deadline:
        time.sleep(.2)
    entry = ctx.router.propagation_entries.get(tid)
    if entry:
        reply = custody.attest(req, ctx.source.hash.hex(), entry[0].hex(), Path(entry[1]).read_bytes(), entry[2])
    else:
        reply = custody.refuse(req, ctx.source.hash.hex(), 'transient id not in store')
    (ctx.custody/f"{req['transient_id']}.issued.json").write_text(json.dumps(reply))
    ctx.emit('custody_answered', kind=reply['kind'], transient_id=req['transient_id'], requester=req['source'])
    direct(ctx, key.hex(), req['source'], reply, f"answer:{req['transient_id'][:8]}")


def collect_custody(ctx, message, kind):
    """Origin side: verify against the key of the relay we asked, then keep the packet."""
    asked = ctx.expected.get(custody.peek(message.packed, time.time()).get('id'))
    if asked is None:
        raise ValueError('unsolicited custody reply')
    key, tid = bytes.fromhex(asked['public_key']), asked['transient_id']
    if kind == 'custody':
        verified = custody.verify(message.packed, key, ctx.source.hash.hex(), tid, time.time())
        path = ctx.custody/f'{tid}.lxmf'
    else:
        verified = custody.verify_refusal(message.packed, key, ctx.source.hash.hex(), tid, time.time())
        path = ctx.custody/f'{tid}.refused.lxmf'
    path.write_bytes(message.packed)
    # Distinct from the 'custody' command ack, which is also an event and also carries the id.
    ctx.emit('custody_received' if kind == 'custody' else 'custody_refused', relay=asked['relay'],
             **{k: v for k, v in verified.items() if k not in ('version', 'kind')})


def publish_receipt(ctx, command):
    """Recipient side: the local receipt travels back as a propagated message via one relay."""
    envelope = json.loads((ctx.home/'completion.json').read_text())
    origin, label = command['origin'], command['label']
    ctx.router.set_outbound_propagation_node(bytes.fromhex(command['propagation']))
    msg = LXMF.LXMessage(target_for(origin['public_key'], origin['destination']), ctx.source, encode(envelope),
                         'dethron-g1', desired_method=LXMF.LXMessage.PROPAGATED)
    msg.register_delivery_callback(lambda m: ctx.emit('receipt_published', label=label,
                                                      transient_id=m.transient_id.hex(), packed_bytes=len(m.packed)))
    msg.register_failed_callback(lambda m: ctx.emit('send_failed', label=label))
    ctx.router.handle_outbound(msg)
    return {'label': label, 'receipt_id': envelope['id']}


def remember_recipient(ctx, destination, public_key):
    """Whom the origin sent to must outlive the origin's process, or it cannot recognize its own proof."""
    ctx.recipients[destination] = public_key
    (ctx.home/'recipients.json').write_text(json.dumps(ctx.recipients))


def load_recipients(home):
    path = home/'recipients.json'
    return json.loads(path.read_text()) if path.exists() else {}


def collect_receipt(ctx, message):
    """Origin side: a receipt is only kept if signed by a recipient we actually sent to."""
    key = ctx.recipients.get(message.source_hash.hex())
    if key is None:
        raise ValueError('receipt from an unknown recipient')
    obj = authenticate(message.packed, bytes.fromhex(key), ctx.source.hash.hex(), time.time())
    if obj['kind'] != 'receipt':
        raise ValueError(f"expected a receipt: {obj['kind']}")
    (ctx.receipts/f"{obj['id']}.lxmf").write_bytes(message.packed)
    ctx.emit('receipt_received', **{k: v for k, v in obj.items() if k not in ('version', 'kind')})
