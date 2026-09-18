"""Generation lifecycle: attach to live nodes, hand over natively, retire the old ones."""
import json
import os
from pathlib import Path
import time

from g3_process import Daemon
from gateway_scenario import ports

PUBLIC = ('destination', 'public_key', 'propagation')


class Lab:
    """Every supervisor generation drives the same live nodes through public files."""

    def __init__(self, root, phase):
        self.root, self.phase = Path(root), phase
        self.nodes = {}

    def record(self, event, **values):
        row = {'event': event, 'time': time.time(), 'phase': self.phase,
               'supervisor_pid': os.getpid(), **values}
        with (self.root/'timeline.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        print(json.dumps(row), flush=True)
        return row

    def port(self, name):
        return json.loads((self.root/name/'daemon.json').read_text())['port']

    def public(self, node):
        return {key: node.info[key] for key in PUBLIC}

    def launch(self, name, contacts=(), settings=None, reuse=False):
        node = Daemon(self.root, name)
        port = ports(1)[0]
        node.launch(port, [self.port(c) for c in contacts], settings, reuse=reuse)
        self.nodes[name] = node
        self.record('launch', node=name, pid=node.pid, port=port, contacts=list(contacts),
                    reuse=reuse, info=self.public(node))
        return node

    def attach(self, name, declared=None):
        """Resume a running node; a node that does not match the checkpoint is refused."""
        node = Daemon(self.root, name)
        node.attach()
        if declared is not None and self.public(node) != {k: declared[k] for k in PUBLIC}:
            raise ValueError(f'{name}: live node does not match the declared checkpoint')
        self.nodes[name] = node
        self.record('attach', node=name, pid=node.pid, verified=declared is not None)
        return node

    def retire(self, node):
        """Stop a generation and make its directory unreachable to every successor."""
        status = node.status()
        node.kill()
        self.nodes.pop(node.name, None)
        (self.root/'retired').mkdir(exist_ok=True)
        target = self.root/'retired'/node.name
        if target.exists():
            raise ValueError(f'{node.name}: retirement target already exists')
        for _ in range(20):
            try:
                node.home.rename(target)
                break
            except OSError:
                time.sleep(.5)
        else:
            raise OSError(f'{node.name}: home is still in use after shutdown')
        self.record('retire', node=node.name, pid=node.pid, stored=status['stored'],
                    inventory=status['inventory'])
        return status

    def handover(self, old, new, inventory, timeout=300, retry=20):
        """The successor starts empty and may only receive the data over the network.

        LXMF peers sync repeatedly; autopeer is off here, so a single announce and
        sync can miss while paths are still settling. Ask again until the deadline
        instead of waiting on one attempt.
        """
        if new.status()['stored'] != 0:
            raise ValueError(f'{new.name}: successor is not empty')
        deadline, attempts, next_attempt = time.monotonic()+timeout, 0, 0.0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_attempt:
                new.request('announce')
                time.sleep(2)
                old.request('peer', peer=self.public(new), timeout=60)
                attempts += 1
                next_attempt = time.monotonic()+retry
            status = new.status()
            # The stored file appears before the router finishes indexing it; wait for both views.
            if status['inventory'] == inventory and status['stored'] == len(inventory):
                self.record('handover', old=old.name, new=new.name, stored=status['stored'],
                            inventory=inventory, attempts=attempts)
                return status
            time.sleep(.5)
        raise TimeoutError(f'{old.name}->{new.name}: declared data never arrived over the network '
                           f'after {attempts} sync attempts in {timeout}s')

    def fetch(self, receiver, relay, source, limit=256, timeout=180, retry=25):
        """A fetch that fails while paths settle is retried, not treated as a verdict."""
        deadline, attempts, failures, next_attempt = time.monotonic()+timeout, 0, 0, 0.0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_attempt:
                relay.request('announce')
                time.sleep(2)
                receiver.request('fetch', source=source, propagation=relay.info['propagation'],
                                 limit_kb=limit, timeout=60)
                attempts += 1
                next_attempt = time.monotonic()+retry
            state = receiver.status()
            if state['sync'] == 7:
                self.record('fetched', relay=relay.name, receiver=state['receiver'],
                            attempts=attempts, failures=failures)
                return state['receiver']
            if state['sync'] >= 240:
                failures += 1
                next_attempt = 0.0
            time.sleep(.25)
        raise TimeoutError(f'native fetch from {relay.name} did not complete after {attempts} '
                           f'attempts ({failures} native failures) in {timeout}s')

    def shutdown(self):
        """Only the final phase stops the survivors; a supervisor exit must not."""
        for node in list(self.nodes.values()):
            node.kill()
        self.nodes.clear()
