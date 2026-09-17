"""Frozen G4 profile: which interfaces each scenario is allowed to have, and nothing else."""
import re

PROFILE = {'version': 1, 'payload_bytes': 16384, 'deadline_seconds': 180,
           'scenarios': ['ip', 'bridged', 'dark', 'cut'], 'bridge_poll_seconds': .02}

QUOTES = chr(34)+chr(39)

BASE = ('[reticulum]\n share_instance = No\n enable_transport = No\n'
        ' discover_interfaces = No\n[logging]\n loglevel = 3\n[interfaces]\n')


def tcp_listener(port):
    return (' [[Listener]]\n type = TCPServerInterface\n enabled = Yes\n'
            f' listen_ip = 127.0.0.1\n listen_port = {port}\n')


def tcp_contact(index, port):
    return (f' [[Contact{index}]]\n type = TCPClientInterface\n enabled = Yes\n'
            f' target_host = 127.0.0.1\n target_port = {port}\n')


def pipe_bridge(command, name='Bridge', respawn=2):
    return (f' [[{name}]]\n type = PipeInterface\n enabled = Yes\n'
            f' command = {command}\n respawn_delay = {respawn}\n')


def bridge_command(python, script, channel, side, ledger):
    """configobj strips quotes and shlex would then collapse the line into one argument,
    so every path must be posix-shaped, unquoted and free of whitespace."""
    parts = [str(python), str(script), str(channel), str(side), str(ledger)]
    posix = [part.replace(chr(92), '/') for part in parts]
    for value in posix:
        if not value or any(char.isspace() or char in QUOTES for char in value):
            raise ValueError(f'bridge paths must be unquoted and whitespace-free: {value!r}')
    return ' '.join(posix)


def config_text(interfaces):
    return BASE+''.join(interfaces)


def interface_types(text):
    return re.findall(r'type\s*=\s*(\w+)', text)


def isolated(text):
    """True only when nothing in this configuration can reach the IP stack."""
    return set(interface_types(text)) <= {'PipeInterface'} and 'share_instance = No' in text


def expected_delivery(scenario):
    return scenario in ('ip', 'bridged', 'cut')
