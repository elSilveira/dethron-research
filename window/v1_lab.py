"""V1 lifecycle on one host over TCP: the medium is not the question here, the evidence is."""
import json
import os
from pathlib import Path
import time

from g3_process import Daemon
from gateway_scenario import ports


class Lab:
    def __init__(self, root, scenario):
        self.root, self.scenario = Path(root), scenario
        self.nodes, self.ports = {}, {}

    def record(self, event, **values):
        row = {'event': event, 'time': time.time(), 'scenario': self.scenario,
               'supervisor_pid': os.getpid(), **values}
        with (self.root/'timeline.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        print(json.dumps(row), flush=True)
        return row

    def public(self, node):
        return {key: node.info[key] for key in ('destination', 'public_key', 'propagation')}

    def launch(self, name, contacts=(), settings=None, reuse=False):
        node = Daemon(self.root, name, 'v1_node.py')
        if reuse or name not in self.ports:  # a returning node takes a fresh listener port
            self.ports[name] = ports(1)[0]
        node.launch(self.ports[name], [self.ports[c] for c in contacts], settings, reuse=reuse)
        self.nodes[name] = node
        self.record('launch', node=name, pid=node.pid, contacts=list(contacts), info=self.public(node))
        return node

    def stop(self, node):
        status = node.status()
        node.kill()
        self.nodes.pop(node.name, None)
        self.record('stop', node=node.name, pid=node.pid, stored=status['stored'])
        return status

    def retire(self, node):
        """The origin leaves; its evidence stays readable under another name."""
        status = self.stop(node)
        target = self.root/f'{node.name}.offline'
        for _ in range(20):
            try:
                node.home.rename(target)
                break
            except OSError:
                time.sleep(.5)
        else:
            raise OSError(f'{node.name}: home still in use')
        self.record('retire', node=node.name, evidence=str(target.name))
        return status

    def fetch(self, receiver, relay, source, limit=256, timeout=60):
        relay.request('announce')
        time.sleep(2)
        receiver.request('fetch', source=source, propagation=relay.info['propagation'],
                         limit_kb=limit, timeout=60)
        deadline, state = time.monotonic()+timeout, None
        while time.monotonic() < deadline:
            state = receiver.status()
            if state['sync'] == 7 or state['sync'] >= 240:
                break
            time.sleep(.25)
        return self.record('fetch', relay=relay.name, sync=state['sync'], receiver=state['receiver'])

    def close(self):
        for node in list(self.nodes.values()):
            node.kill()
        self.nodes.clear()
