"""Prepare a V3 bench: identities, addresses, both schedules and the shared instant.

    window/.venv-gateway/Scripts/python.exe window/run_v3_bench.py <folder> <relay-host> [lead]
    window/.venv-gateway/Scripts/python.exe window/run_v3_bench.py <folder> --serial <alpha-port> <beta-port> [lead]

The first form is V3a: the machines meet over the network, and <relay-host> is the relay
machine's address on the local network, which is what the recipient uses to reach it.

The second is V3c: the machines meet over a serial link that carries no IP, and each port
is the COM port on that machine. The recipient is then given that link and nothing else,
so an object that arrives cannot have come over IP. Prove the link carries bytes first:

    window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py bulk-listen <port>

Everything is written under <folder>/control, which is what the other machine needs a
copy of.
"""
import json
from pathlib import Path
import sys
import time

from v3_bench import PROFILE, SERIAL, build


def select(argv):
    """Either an address or a port on each machine, never both, never neither."""
    if len(argv) >= 3 and argv[2] == '--serial':
        if not 5 <= len(argv) <= 6:
            raise SystemExit(__doc__)
        return {'serial': {'alpha': argv[3], 'beta': argv[4]}}, argv[5:6]
    if not 3 <= len(argv) <= 4:
        raise SystemExit(__doc__)
    return {'relay_host': argv[2]}, argv[3:4]


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1]).resolve()
    medium, rest = select(sys.argv)
    profile = SERIAL if 'serial' in medium else PROFILE
    lead = int(rest[0]) if rest else profile['lead_seconds']
    bench = build(root, lead_seconds=lead, **medium)
    opens = bench['start_wall']
    print(json.dumps({'folder': str(root), 'medium': 'serial' if 'serial' in medium else 'ip',
                      **medium, 'machines': sorted(bench['machines']),
                      'digests': bench['digests'], 'window_seconds': bench['window_seconds'],
                      'opens_at': time.strftime('%H:%M:%S', time.localtime(opens)),
                      'opens_in_seconds': round(opens-time.time(), 1),
                      'ports': PROFILE['ports']}, indent=2), flush=True)
    print(f"\nCopy {root/'control'} to the other machine, then start both agents before "
          f"{time.strftime('%H:%M:%S', time.localtime(opens))}.", flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
