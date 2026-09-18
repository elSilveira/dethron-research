"""Real native propagation node/client for the G2 controlled experiment."""
import base64
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


def main():
    home, role = Path(sys.argv[1]), sys.argv[2]
    settings = json.loads((home/"settings.json").read_text())
    lock = threading.Lock()

    def emit(event, **values):
        with lock:
            print(json.dumps({"event": event, "time": time.time(), **values}), flush=True)

    # A stamp discarded by a log line silently stops peering; install before router work.
    stamp_defect = lxmf_stamp.install()
    RNS.Reticulum(configdir=str(home/"rns"), loglevel=3, logdest=RNS.LOG_FILE)
    key = home/"identity"
    identity = RNS.Identity.from_file(str(key)) if key.exists() else RNS.Identity()
    if identity is None:
        raise ValueError("invalid identity")
    if not key.exists():
        identity.to_file(str(key))
    router = LXMF.LXMRouter(identity=identity, storagepath=str(home), autopeer=False,
                           propagation_limit=2048, delivery_limit=settings["limit_kb"], sync_limit=8192)
    source = router.register_delivery_identity(identity, display_name=role, stamp_cost=None)
    receiver = Receiver(home, source, settings["mode"], emit) if role == "D" else None
    if receiver:
        router.register_delivery_callback(receiver.receive)
    if role in "ABC":
        router.enable_propagation()
    emit("ready", stamp_workaround=stamp_defect, destination=source.hash.hex(), public_key=identity.get_public_key().hex(),
         propagation=router.propagation_destination.hash.hex())
    for line in sys.stdin:
        try:
            command = json.loads(line)
            action = command["action"]
            if action == "crash":
                os._exit(23)
            elif action == "announce":
                router.announce_propagation_node()
            elif action == "send":
                peer = RNS.Identity(create_keys=False)
                peer.load_public_key(bytes.fromhex(command["recipient"]["public_key"]))
                target = RNS.Destination(peer, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
                router.set_outbound_propagation_node(bytes.fromhex(command["propagation"]))
                msg = LXMF.LXMessage(target, source, base64.b64decode(command["body"], validate=True),
                                     "dethron-g1", desired_method=LXMF.LXMessage.PROPAGATED)
                label = command["label"]
                msg.register_delivery_callback(lambda m, label=label: emit("handoff", label=label, packed_bytes=len(m.packed)))
                msg.register_failed_callback(lambda m, label=label: emit("send_failed", label=label))
                router.handle_outbound(msg)
            elif action == "fetch":
                peer = command["source"]
                RNS.Identity.remember(None, bytes.fromhex(peer["destination"]), bytes.fromhex(peer["public_key"]))
                router.acknowledge_sync_completion(reset_state=True)
                router.delivery_per_transfer_limit = command.get("limit_kb", settings["limit_kb"])
                router.set_outbound_propagation_node(bytes.fromhex(command["propagation"]))
                router.request_messages_from_propagation_node(identity)
            elif action == "status":
                interfaces = [i for i in RNS.Transport.interfaces if getattr(i, "parent_interface", None) is None]
                metrics = {"tx": sum(i.txb for i in interfaces), "rx": sum(i.rxb for i in interfaces)}
                files = list((home/"lxmf"/"messagestore").glob("*"))
                emit("status", stored=len(router.propagation_entries), sync=router.propagation_transfer_state,
                     store_bytes=sum(p.stat().st_size for p in files if p.is_file()), metrics=metrics,
                     receiver=receiver.status() if receiver else None)
            else:
                raise ValueError("unknown command")
            emit("ack", action=action)
        except Exception as exc:
            emit("error", error=repr(exc))


if __name__ == "__main__":
    main()
