"""Lab CLI for the reusable G1 adapter; stdin schedules actions, never delivers payloads to peers."""
import base64
import json
import os
from pathlib import Path
import sys
import threading
import time

import LXMF
import RNS

from dethron_gateway.adapter import Adapter
from dethron_gateway.mailbox import Mailbox
from dethron_gateway.protocol import data_envelope


def main():
    home, role = Path(sys.argv[1]), sys.argv[2]
    lock = threading.Lock()

    def emit(event, **values):
        with lock:
            print(json.dumps({"event": event, "time": time.time(), **values}), flush=True)

    RNS.Reticulum(configdir=str(home / "rns"), loglevel=3, logdest=RNS.LOG_FILE)
    key = home / "identity"
    if (home / "mailbox.db").exists() and not key.exists():
        raise ValueError("missing identity for existing mailbox; refusing new identity")
    identity = RNS.Identity.from_file(str(key)) if key.exists() else RNS.Identity()
    if identity is None:
        raise ValueError("unreadable identity")
    if not key.exists():
        identity.to_file(str(key))
    router = LXMF.LXMRouter(identity=identity, storagepath=str(home), autopeer=False,
                           delivery_limit=2048)
    source = router.register_delivery_identity(identity, display_name=role, stamp_cost=None)
    mailbox = Mailbox(home / "mailbox.db", source.hash.hex())
    adapter = Adapter(router, source, mailbox, emit)
    emit("ready", destination=source.hash.hex(), public_key=identity.get_public_key().hex())
    for line in sys.stdin:
        try:
            obj = json.loads(line)
            action = obj["action"]
            if action == "crash":
                os._exit(23)
            elif action == "trust":
                peer = obj["peer"]
                RNS.Identity.remember(None, bytes.fromhex(peer["destination"]), bytes.fromhex(peer["public_key"]))
            elif action == "announce":
                router.announce(source.hash)
            elif action == "submit":
                envelope = data_envelope(source.hash.hex(), obj["destination"],
                                         base64.b64decode(obj["payload"], validate=True),
                                         obj["expires"], obj.get("id"))
                mailbox.queue(envelope, time.time())
                emit("queued", id=envelope["id"], digest=envelope["digest"])
            elif action == "pump":
                adapter.pump()
            elif action == "status":
                mailbox.pending(time.time())
                emit("status", rows=mailbox.snapshot())
            elif action == "inject":
                # Explicit test input, still transmitted/signed by native LXMF.
                if not adapter.transmit(obj["destination"], base64.b64decode(obj["body"], validate=True)):
                    raise ValueError("test injection has no native path")
            else:
                raise ValueError("unknown command")
            emit("ack", action=action)
        except Exception as exc:
            emit("error", error=repr(exc))


if __name__ == "__main__":
    main()
