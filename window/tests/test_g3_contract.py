import tempfile
import unittest
from pathlib import Path

from g3_contract import validate_checkpoint, write_checkpoint, load_checkpoint


def checkpoint():
    return {'version': 1, 'generation': 0, 'mode': 'complete', 'source': {'destination': 'a'*32, 'public_key': 'a'*128},
            'destination': {'destination': 'b'*32, 'public_key': 'b'*128},
            'object': {'id': 'c'*32, 'size': 24576, 'digest': 'd'*64}, 'expires': 2000000000,
            'relays': {n: {'destination': 'a'*32, 'public_key': 'a'*128, 'propagation': 'a'*32,
                           'inventory': ['e'*64]} for n in 'ABC'}}


class ContractTests(unittest.TestCase):
    def test_checkpoint_contains_only_public_continuation_metadata(self):
        state = checkpoint()
        self.assertEqual(validate_checkpoint(state), state)
        for key in ('payload', 'private_key', 'seed', 'path'):
            bad = {**state, key: 'hidden source'}
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_checkpoint(bad)
        state['source']['private_key'] = 'secret'
        with self.assertRaises(ValueError):
            validate_checkpoint(state)

    def test_checkpoint_missing_or_wrong_generation_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(FileNotFoundError):
                load_checkpoint(root, 0)
            write_checkpoint(root, checkpoint())
            self.assertEqual(load_checkpoint(root, 0)['generation'], 0)
            with self.assertRaises(FileNotFoundError):
                load_checkpoint(root, 1)


if __name__ == '__main__':
    unittest.main()
