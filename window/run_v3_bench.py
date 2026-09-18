"""Prepare a V3a bench: identities, addresses, both schedules and the shared instant.

    window/.venv-gateway/Scripts/python.exe window/run_v3_bench.py <folder> <relay-host> [lead_seconds]

<relay-host> is the address the recipient machine uses to reach the relay machine, so
it is the relay machine's IP on the local network. Everything is written under
<folder>/control, which is what the other machine needs a copy of.
"""
import json
from pathlib import Path
import sys
import time

from v3_bench import PROFILE, build


def main():
    if not 3 <= len(sys.argv) <= 4:
        raise SystemExit(__doc__)
    root, relay_host = Path(sys.argv[1]).resolve(), sys.argv[2]
    lead = int(sys.argv[3]) if len(sys.argv) == 4 else PROFILE['lead_seconds']
    bench = build(root, relay_host, lead_seconds=lead)
    opens = bench['start_wall']
    print(json.dumps({'folder': str(root), 'relay_host': relay_host,
                      'machines': sorted(bench['machines']), 'digests': bench['digests'],
                      'window_seconds': bench['window_seconds'],
                      'opens_at': time.strftime('%H:%M:%S', time.localtime(opens)),
                      'opens_in_seconds': round(opens-time.time(), 1),
                      'ports': PROFILE['ports']}, indent=2), flush=True)
    print(f"\nCopy {root/'control'} to the other machine, then start both agents before "
          f"{time.strftime('%H:%M:%S', time.localtime(opens))}.", flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
