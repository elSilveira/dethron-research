"""Does a serial link actually carry bytes between these two machines?

Answer this before building anything on top of it. A Bluetooth SPP pair, a USB-TTL
pair and a null-modem cable all present the same thing to Reticulum — a COM port — and
all three can present a port that opens cleanly and then carries nothing.

    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py list
    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py listen COM5 600
    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py send   COM4

Run `listen` on one machine first, then `send` on the other. The sender writes marked
lines and echoes back whatever returns; the listener answers each one, so both ends print
what actually crossed and a link that opens but stays silent is visible immediately. The
listener holds the port for the seconds given — give it enough to walk to the other
machine, and start only one, because a second listener on the same port is refused by
Windows with an access error that says nothing about the link itself.

A few short lines prove the link is alive, not that it can carry anything. `bulk` moves a
V3-sized object and reports what actually crossed and how fast, which is what decides
whether a medium is worth building a bench on:

    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py bulk-listen COM5
    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py bulk-send   COM4
"""
import hashlib
import sys
import time

import serial
from serial.tools import list_ports

SPEED = 9600
MARK = b'dethron-serial-probe'
BULK = hashlib.shake_256(b'dethron-serial-bulk').digest(16384)
DIGEST = hashlib.sha256(BULK).hexdigest()


def show():
    ports = list(list_ports.comports())
    print(f'{len(ports)} serial ports')
    for port in ports:
        print(f'  {port.device:<8} {port.description}')
    if not ports:
        print('  none: pair the machines and add the serial port service first')
    return 0


def listen(name, seconds=600):
    print(f'listening on {name} at {SPEED} baud for {seconds}s', flush=True)
    with serial.Serial(name, SPEED, timeout=1) as link:
        deadline, heard = time.monotonic()+seconds, 0
        while time.monotonic() < deadline:
            line = link.readline()
            if not line:
                continue
            heard += 1
            print(f'  received: {line.strip()!r}', flush=True)
            link.write(b'ack:'+line.strip()+b'\n')
            link.flush()
    print(f'heard {heard} lines', flush=True)
    return 0 if heard else 1


def send(name, count=5):
    print(f'sending on {name} at {SPEED} baud', flush=True)
    with serial.Serial(name, SPEED, timeout=5) as link:
        answered = 0
        for index in range(count):
            link.write(MARK+f' {index}\n'.encode())
            link.flush()
            reply = link.readline()
            print(f'  sent {index}, reply: {reply.strip()!r}', flush=True)
            if reply.strip().startswith(b'ack:'):
                answered += 1
            time.sleep(.5)
    print(f'{answered} of {count} answered', flush=True)
    return 0 if answered == count else 1


def describe(size, elapsed):
    """A rate, or why there is none. A link fast enough to finish inside one clock tick
    is a good link, and must not read as a dead one — nor divide by the zero it leaves."""
    if not size:
        return 'no data'
    if elapsed <= 0:
        return 'faster than the clock can measure'
    return f'{size/elapsed/1024:.1f} KiB/s'


def bulk_listen(name, seconds=600):
    """Receive a V3-sized object and report what crossed, not what was expected."""
    print(f'waiting for {len(BULK)} bytes on {name} for {seconds}s', flush=True)
    with serial.Serial(name, SPEED, timeout=5) as link:
        deadline, buffer, started = time.monotonic()+seconds, b'', None
        while len(buffer) < len(BULK) and time.monotonic() < deadline:
            chunk = link.read(max(1, min(4096, len(BULK)-len(buffer))))
            if chunk and started is None:
                started = time.monotonic()
            buffer += chunk
        elapsed = (time.monotonic()-started) if started else 0
        got = hashlib.sha256(buffer).hexdigest()
        link.write(got.encode()+b'\n')
        link.flush()
    intact = len(buffer) == len(BULK) and got == DIGEST
    rate = describe(len(buffer), elapsed)
    print(f'received {len(buffer)} of {len(BULK)} bytes in {elapsed:.1f}s ({rate})', flush=True)
    print(f'  sha256 {got}\n  {"intact" if intact else "CORRUPT OR INCOMPLETE"}', flush=True)
    return 0 if intact else 1


def bulk_send(name):
    """Send the same object and check the digest the far side computed."""
    print(f'sending {len(BULK)} bytes on {name}', flush=True)
    with serial.Serial(name, SPEED, timeout=120) as link:
        started = time.monotonic()
        link.write(BULK)
        link.flush()
        written = time.monotonic()-started
        reply = link.readline().strip().decode(errors='replace')
    print(f'wrote in {written:.1f}s ({describe(len(BULK), written)})', flush=True)
    if reply != DIGEST:
        print(f'  far side computed {reply or "nothing"}\n  expected {DIGEST}\n  LINK LOSES DATA', flush=True)
        return 1
    print(f'  far side computed the same digest: the link carried {len(BULK)} bytes intact', flush=True)
    return 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == 'list':
        return show()
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    if mode == 'listen':
        return listen(sys.argv[2], *[int(one) for one in sys.argv[3:4]])
    if mode == 'send':
        return send(sys.argv[2])
    if mode == 'bulk-listen':
        return bulk_listen(sys.argv[2], *[int(one) for one in sys.argv[3:4]])
    if mode == 'bulk-send':
        return bulk_send(sys.argv[2])
    raise SystemExit(__doc__)


if __name__ == '__main__':
    raise SystemExit(main())
