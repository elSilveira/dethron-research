"""One isolated real Reticulum/LXMF process; JSON control is not a data path."""
import json
import os
from pathlib import Path
import sys
import threading
import time

import LXMF
import RNS

from gateway_contract import payload


def main():
    home = Path(sys.argv[1])
    role = sys.argv[2]
    lock = threading.Lock()

    def emit(kind, **values):
        with lock:
            print(json.dumps({"event": kind, "time": time.time(), **values}), flush=True)

    RNS.Reticulum(configdir=str(home / "rns"), loglevel=3, logdest=RNS.LOG_FILE)
    identity_path = home / "identity"
    identity = RNS.Identity.from_file(str(identity_path)) if identity_path.exists() else RNS.Identity()
    if not identity_path.exists():
        identity.to_file(str(identity_path))
    router = LXMF.LXMRouter(identity=identity, storagepath=str(home), autopeer=False,
                           propagation_limit=2048, delivery_limit=2048, sync_limit=8192)
    dest = router.register_delivery_identity(identity, display_name=role, stamp_cost=None)
    messages = {}

    def received(message):
        # Filename derives from authenticated payload only after independent audit later.
        folder = home / "receipts"
        folder.mkdir(exist_ok=True)
        path = folder / (message.hash.hex() + ".lxmf")
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(message.packed)
        emit("received", title=message.title.decode(), file=path.name,
             signature_validated=message.signature_validated, size=len(message.content))

    router.register_delivery_callback(received)
    if role in ("A", "B", "C"):
        router.enable_propagation()
    emit("ready", public_key=identity.get_public_key().hex(), destination=dest.hash.hex(),
         propagation=router.propagation_destination.hash.hex())
    for line in sys.stdin:
        command = json.loads(line)
        try:
            action = command["action"]
            if action == "crash":
                os._exit(23)
            elif action == "announce":
                router.announce_propagation_node()
            elif action == "send":
                peer = RNS.Identity(create_keys=False)
                peer.load_public_key(bytes.fromhex(command["recipient"]["public_key"]))
                target = RNS.Destination(peer, RNS.Destination.OUT, RNS.Destination.SINGLE,
                                         "lxmf", "delivery")
                router.set_outbound_propagation_node(bytes.fromhex(command["propagation"]))
                msg = LXMF.LXMessage(target, dest, payload(command["id"], command["size"]),
                                     command["id"], desired_method=LXMF.LXMessage.PROPAGATED)
                messages[command["id"]] = msg
                msg.register_delivery_callback(lambda m: emit("handoff", id=m.title.decode()))
                msg.register_failed_callback(lambda m: emit("send_failed", id=m.title.decode()))
                router.handle_outbound(msg)
            elif action == "fetch":
                source = command["source"]
                RNS.Identity.remember(None, bytes.fromhex(source["destination"]),
                                      bytes.fromhex(source["public_key"]))
                router.set_outbound_propagation_node(bytes.fromhex(command["propagation"]))
                router.request_messages_from_propagation_node(identity)
            elif action == "status":
                emit("status", stored=len(router.propagation_entries),
                     states={key: value.state for key, value in messages.items()},
                     sync=router.propagation_transfer_state)
            elif action == "absent":
                absent = RNS.Identity()
                absent_dest = RNS.Destination(absent, RNS.Destination.OUT,
                                              RNS.Destination.SINGLE, "lxmf", "delivery")
                emit("absent", public_key=absent.get_public_key().hex(),
                     destination=absent_dest.hash.hex())
            elif action == "stop":
                break
            else:
                raise ValueError("unknown command")
            emit("ack", action=action)
        except Exception as exc:
            emit("error", action=command.get("action"), error=repr(exc))


if __name__ == "__main__":
    main()
