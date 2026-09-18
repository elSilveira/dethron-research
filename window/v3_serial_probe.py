"""Does a serial link actually carry bytes between these two machines?

Answer this before building anything on top of it. A Bluetooth SPP pair, a USB-TTL
pair and a null-modem cable all present the same thing to Reticulum — a COM port — and
all three can present a port that opens cleanly and then carries nothing.

    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py list
    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py listen COM5
    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py send   COM4

Run `listen` on one machine first, then `send` on the other. The sender writes marked
lines and echoes back whatever returns; the listener answers each one. Both print what
actually crossed, so a link that opens but stays silent is visible immediately.
"""
import sys
import time

import serial
from serial.tools import list_ports

SPEED = 9600
MARK = b'dethron-serial-probe'


def show():
    ports = list(list_ports.comports())
    print(f'{len(ports)} serial ports')
    for port in ports:
        print(f'  {port.device:<8} {port.description}')
    if not ports:
        print('  none: pair the machines and add the serial port service first')
    return 0


def listen(name, seconds=120):
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


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == 'list':
        return show()
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    if mode == 'listen':
        return listen(sys.argv[2])
    if mode == 'send':
        return send(sys.argv[2])
    raise SystemExit(__doc__)


if __name__ == '__main__':
    raise SystemExit(main())
