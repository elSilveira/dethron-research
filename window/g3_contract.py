"""Only public metadata may cross the supervisor boundary; never content or seeds."""
import json
import re


def hex_value(value, length):
    return isinstance(value, str) and re.fullmatch(f'[0-9a-f]{{{length}}}', value)


def validate_checkpoint(state):
    if set(state) != {'version', 'generation', 'mode', 'source', 'destination', 'object', 'expires', 'relays'}:
        raise ValueError('unexpected checkpoint fields')
    if state['version'] != 1 or type(state['generation']) is not int or not 0 <= state['generation'] <= 2:
        raise ValueError('unsupported checkpoint version/generation')
    if state['mode'] not in ('complete', 'missing') or type(state['expires']) is not int:
        raise ValueError('invalid scenario/lifetime')
    for name in ('source', 'destination'):
        obj = state[name]
        if set(obj) != {'destination', 'public_key'} or not hex_value(obj['destination'], 32) or not hex_value(obj['public_key'], 128):
            raise ValueError('invalid public identity')
    obj = state['object']
    if set(obj) != {'id', 'size', 'digest'} or not hex_value(obj['id'], 32) or not hex_value(obj['digest'], 64):
        raise ValueError('invalid object metadata')
    if type(obj['size']) is not int or obj['size'] != 24576:
        raise ValueError('unexpected payload size')
    if set(state['relays']) != set('ABC'):
        raise ValueError('invalid relay set')
    for obj in state['relays'].values():
        if set(obj) != {'destination', 'public_key', 'propagation', 'inventory'}:
            raise ValueError('invalid relay metadata')
        for key, length in (('destination', 32), ('public_key', 128), ('propagation', 32)):
            if not hex_value(obj[key], length):
                raise ValueError('invalid relay identity')
        if not isinstance(obj['inventory'], list) or len(obj['inventory']) > 1 or any(not hex_value(h, 64) for h in obj['inventory']):
            raise ValueError('invalid encrypted inventory')
    return state


def write_checkpoint(root, state):
    validate_checkpoint(state)
    target = root/f"checkpoint-{state['generation']}.json"
    if target.exists():
        raise ValueError('checkpoint already exists')
    pending = target.with_suffix('.pending')
    pending.write_text(json.dumps(state, indent=2))
    pending.replace(target)


def load_checkpoint(root, generation):
    state = validate_checkpoint(json.loads((root/f'checkpoint-{generation}.json').read_text()))
    if state['generation'] != generation:
        raise ValueError('wrong checkpoint generation')
    return state
