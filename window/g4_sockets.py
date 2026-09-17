"""Independent evidence that a process holds no IP endpoint at all."""
import os
import subprocess

QUIET = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


class Unavailable(RuntimeError):
    """The evidence tool fails loudly; a silent empty answer would fake the proof."""


def endpoints(pids):
    """Every TCP/UDP endpoint currently owned by these processes, as the OS reports it."""
    wanted = {int(pid) for pid in pids}
    if os.name != 'nt':
        raise Unavailable('endpoint evidence is only implemented for Windows netstat')
    probe = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, creationflags=QUIET)
    if probe.returncode != 0 or 'TCP' not in probe.stdout:
        raise Unavailable(f'netstat produced no usable output: {probe.returncode}')
    rows = []
    for line in probe.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] in ('TCP', 'UDP') and parts[-1].isdigit():
            if int(parts[-1]) in wanted:
                rows.append({'proto': parts[0], 'local': parts[1], 'remote': parts[2],
                             'pid': int(parts[-1])})
    return rows
