"""G4 lifecycle: only the declared path exists, and the medium can really be removed."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from g3_process import Daemon, alive
from g4_contract import bridge_command, config_text, isolated
from g4_sockets import endpoints

BACKSLASH = chr(92)


def posix(path):
    return str(Path(path).resolve()).replace(BACKSLASH, '/')


class Lab:
    def __init__(self, root, scenario):
        self.root, self.scenario = Path(root), scenario
        self.nodes = {}
        self.channels, self.ledgers = self.root/'channels', self.root/'ledgers'
        for folder in (self.channels, self.ledgers):
            folder.mkdir(parents=True, exist_ok=True)
        self.python, self.bridge = posix(sys.executable), posix(Path(__file__).with_name('g4_bridge.py'))

    def record(self, event, **values):
        row = {'event': event, 'time': time.time(), 'scenario': self.scenario,
               'supervisor_pid': os.getpid(), **values}
        with (self.root/'timeline.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        print(json.dumps(row), flush=True)
        return row

    def channel(self, link):
        return self.channels/link

    def open_channel(self, link):
        """Creating the medium is a deliberate act; building a command must never do it."""
        self.channel(link).mkdir(exist_ok=True)
        return self.record('medium_opened', link=link)

    def command(self, link, side):
        return bridge_command(self.python, self.bridge, posix(self.channel(link)), side,
                              f'{posix(self.ledgers)}/{link}-{side}.json')

    def launch(self, name, interfaces, settings=None, reuse=False):
        text = config_text(interfaces)
        if self.scenario != 'ip' and not isolated(text):
            raise ValueError(f'{name}: scenario {self.scenario} may not reach the IP stack')
        node = Daemon(self.root, name)
        node.launch(0, [], settings, reuse=reuse, config=text)
        self.nodes[name] = node
        self.record('launch', node=name, pid=node.pid, interfaces=text.split('[interfaces]')[1].strip(),
                    isolated=isolated(text))
        return node

    def stop(self, node):
        node.kill()
        self.nodes.pop(node.name, None)
        self.record('stop', node=node.name, pid=node.pid)

    def cut(self, link):
        """Remove the medium itself, not a switch inside the software."""
        target = self.channels/f'{link}-removed'
        for _ in range(40):
            try:
                self.channel(link).rename(target)
                break
            except OSError:
                time.sleep(.25)
        else:
            raise OSError(f'{link}: the medium could not be removed')
        return self.record('cut', link=link)

    def restore(self, link):
        if self.channel(link).exists():
            raise ValueError(f'{link}: the medium reappeared on its own')
        (self.channels/f'{link}-removed').rename(self.channel(link))
        return self.record('restore', link=link)

    def bridge_pids(self):
        pids = []
        for path in self.ledgers.glob('*.json'):
            try:
                pids.append(json.loads(path.read_text())['pid'])
            except (OSError, ValueError, KeyError):
                continue
        return pids

    def ip_evidence(self, label):
        """Every process on the path must be shown to hold no IP endpoint at all."""
        nodes = {name: node.pid for name, node in self.nodes.items()}
        bridges = self.bridge_pids()
        rows = endpoints(list(nodes.values())+bridges)
        return self.record('ip_endpoints', label=label, nodes=nodes, bridges=bridges, endpoints=rows)

    def ledger(self):
        return {path.stem: json.loads(path.read_text()) for path in sorted(self.ledgers.glob('*.json'))}

    def close(self):
        """A node killed outright cannot reap its bridge, so the lab reaps them itself."""
        for node in list(self.nodes.values()):
            node.kill()
        self.nodes.clear()
        stopped = []
        for pid in self.bridge_pids():
            if alive(pid):
                subprocess.run(['taskkill', '/F', '/PID', str(pid)] if os.name == 'nt'
                               else ['kill', '-9', str(pid)], capture_output=True)
                stopped.append(pid)
        if stopped:
            self.record('bridges_reaped', pids=stopped)
        return stopped
