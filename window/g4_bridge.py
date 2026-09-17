"""One end of a byte bridge between two Reticulum instances, without any socket.

Reticulum speaks HDLC frames over this process' stdin/stdout; the two ends
exchange those bytes through append-only files. Removing the channel directory
removes the medium: bytes handed over during a cut simply do not arrive.
"""
import json
import os
from pathlib import Path
import sys
import threading
import time

POLL, CHUNK = .02, 4096


def main():
    channel, side, ledger = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    outbound = channel/f'{side}.stream'
    inbound = channel/f'{"b" if side == "a" else "a"}.stream'
    counts = {'side': side, 'pid': os.getpid(), 'sent': 0, 'received': 0,
              'cut_losses': 0, 'started': time.time()}
    lock = threading.Lock()

    def record():
        with lock:
            ledger.write_text(json.dumps(counts))

    def carry_out():
        while True:
            data = sys.stdin.buffer.read1(CHUNK)
            if not data:
                return
            try:
                with outbound.open('ab') as stream:
                    stream.write(data)
                counts['sent'] += len(data)
            except OSError:
                counts['cut_losses'] += len(data)
            record()

    record()
    threading.Thread(target=carry_out, daemon=True).start()
    offset = 0
    while True:
        try:
            with inbound.open('rb') as stream:
                stream.seek(offset)
                data = stream.read()
        except OSError:
            data = b''
        if not data:
            time.sleep(POLL)
            continue
        offset += len(data)
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        counts['received'] += len(data)
        record()


if __name__ == '__main__':
    main()
