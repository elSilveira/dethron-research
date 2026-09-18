"""Turning a scheduled step into a real Reticulum node action, on this machine only.

The executor knows nothing about the bench, the other machine or the clock. It receives
one step at a time from its own agent and performs it, which is what keeps the window
deaf: there is no path here through which anything outside could ask for something the
schedule did not already declare.
"""
import base64
import json
from pathlib import Path

from g3_process import Daemon

BASE = ('[reticulum]\n share_instance = No\n enable_transport = No\n'
        ' discover_interfaces = No\n[logging]\n loglevel = 3\n[interfaces]\n')


def config_text(port, contacts):
    """Contacts are host:port, because the peer is usually on the other machine."""
    text = BASE+(' [[Listener]]\n type = TCPServerInterface\n enabled = Yes\n'
                 f' listen_ip = 0.0.0.0\n listen_port = {port}\n')
    for index, contact in enumerate(contacts):
        host, _, remote = str(contact).partition(':')
        text += (f' [[Contact{index}]]\n type = TCPClientInterface\n enabled = Yes\n'
                 f' target_host = {host}\n target_port = {remote}\n')
    return text


class Executor:
    def __init__(self, root, machine, worker='v1_node.py'):
        self.root, self.machine, self.worker = Path(root), machine, worker
        self.home = self.root/machine
        self.nodes = {}

    def credential(self, name):
        return self.root/'control'/'identities'/f'{name}.key'

    def __call__(self, action, args):
        return getattr(self, f'do_{action}')(dict(args))

    def node(self, name):
        if name not in self.nodes:
            raise ValueError(f'{name}: not launched on {self.machine}')
        return self.nodes[name]

    def do_launch(self, args):
        name = args['node']
        settings = {'limit_kb': 256}
        credential = self.credential(args.get('credential') or name)
        if credential.exists():
            settings['credential'] = str(credential)
        node = Daemon(self.home, name, self.worker)
        node.launch(args['port'], [], settings,
                    config=config_text(args['port'], args.get('contacts') or []))
        self.nodes[name] = node
        return {'pid': node.pid, 'destination': node.info['destination'],
                'propagation': node.info['propagation'], 'port': args['port']}

    def do_announce(self, args):
        return self.node(args['node']).request('announce', timeout=60)

    def do_send(self, args):
        node = self.node(args['node'])
        node.request('send', label=args['label'], body=args['body'],
                     recipient={'destination': args['recipient'], 'public_key': args['recipient_key']},
                     propagation=args['propagation'], timeout=60)
        handoff = node.wait('handoff', label=args['label'], timeout=240)
        return {'label': args['label'], 'transient_id': handoff['transient_id'],
                'packed_bytes': handoff['packed_bytes']}

    def do_fetch(self, args):
        node = self.node(args['node'])
        node.request('fetch', source={'destination': args['source'], 'public_key': args['source_key']},
                     propagation=args['propagation'], limit_kb=args.get('limit_kb', 256), timeout=120)
        state = node.status(timeout=60)
        return {'sync': state['sync'], 'receiver': state['receiver']}

    def do_custody(self, args):
        node = self.node(args['node'])
        return node.request('custody', relay={'name': args['relay'], 'destination': args['relay'],
                                              'public_key': args['relay_key']},
                            transient_id=args['transient_id'], timeout=120)

    def do_status(self, args):
        state = self.node(args['node']).status(timeout=60)
        return {key: state[key] for key in ('stored', 'sync', 'inventory', 'receiver') if key in state}

    def do_stop(self, args):
        node = self.node(args['node'])
        node.kill()
        self.nodes.pop(args['node'], None)
        return {'stopped': args['node'], 'pid': node.pid}

    def close(self):
        for node in list(self.nodes.values()):
            node.kill()
        self.nodes.clear()
