import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    import LXMF
    import RNS
except ImportError as exc:
    raise unittest.SkipTest("requires .venv-gateway") from exc

from dethron_gateway.protocol import data_envelope, encode, receipt_envelope
from v1_return_audit import disjoint, receipt_at_origin, route


def endpoint(identity):
    return RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")


def packed(obj, source, destination):
    message = LXMF.LXMessage(destination, source, encode(obj), "dethron-g1")
    message.pack()
    return message.packed


def launch(node, at):
    return {'event': 'launch', 'node': node, 'time': at}


def stop(node, at):
    return {'event': 'stop', 'node': node, 'time': at}


class DisjointSessionTests(unittest.TestCase):
    def test_origin_leaves_recipient_works_origin_returns(self):
        timeline = [launch('O', 0), stop('O', 10), launch('D', 11), stop('D', 20), launch('O', 21)]
        self.assertEqual(disjoint(timeline), {'origin_sessions': 2, 'recipient_sessions': 1})

    def test_any_overlap_invalidates_the_return(self):
        for timeline in ([launch('O', 0), stop('O', 12), launch('D', 11), stop('D', 20), launch('O', 21)],
                         [launch('O', 0), stop('O', 10), launch('D', 11), stop('D', 25), launch('O', 21)],
                         [launch('O', 0), launch('D', 11), stop('D', 20), launch('O', 21)]):
            with self.subTest(timeline=timeline), self.assertRaises(ValueError):
                disjoint(timeline)

    def test_an_origin_that_never_returned_proves_nothing(self):
        with self.assertRaises(ValueError):
            disjoint([launch('O', 0), stop('O', 10), launch('D', 11), stop('D', 20)])


class ReceiptAtOriginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'O'/'receipts').mkdir(parents=True)
        (self.root/'D').mkdir()
        self.origin_identity, self.recipient_identity = RNS.Identity(), RNS.Identity()
        self.origin, self.recipient = endpoint(self.origin_identity), endpoint(self.recipient_identity)
        self.content = b'the whole object'*64
        self.m = {'source': {'destination': self.origin.hash.hex()},
                  'destination': {'destination': self.recipient.hash.hex(),
                                  'public_key': self.recipient_identity.get_public_key().hex()},
                  'object': {'id': 'c'*32}, 'expires': 100}
        original = data_envelope(self.origin.hash.hex(), self.recipient.hash.hex(), self.content, 100, 'c'*32)
        self.receipt = receipt_envelope(original)
        (self.root/'D'/'completion.json').write_bytes(encode(self.receipt))

    def store(self, obj, signer=None):
        (self.root/'O'/'receipts'/(obj['id']+'.lxmf')).write_bytes(
            packed(obj, endpoint(signer or self.recipient_identity), self.origin))

    def test_the_recipients_receipt_over_the_exact_object_is_accepted(self):
        self.store(self.receipt)
        result = receipt_at_origin(self.root, self.m, self.content, 10)
        self.assertEqual(result['id'], 'c'*32)
        self.assertEqual(result['digest'], hashlib.sha256(self.content).hexdigest())

    def test_a_forged_receipt_is_rejected(self):
        self.store(self.receipt, signer=RNS.Identity())
        with self.assertRaises(ValueError):
            receipt_at_origin(self.root, self.m, self.content, 10)

    def test_a_receipt_for_other_bytes_is_rejected(self):
        other = receipt_envelope(data_envelope(self.origin.hash.hex(), self.recipient.hash.hex(),
                                               b'different bytes', 100, 'c'*32))
        self.store(other)
        with self.assertRaises(ValueError):
            receipt_at_origin(self.root, self.m, self.content, 10)

    def test_no_completion_means_no_receipt_may_exist(self):
        self.assertIsNone(receipt_at_origin(self.root, self.m, None, 10))
        self.store(self.receipt)
        with self.assertRaises(ValueError):
            receipt_at_origin(self.root, self.m, None, 10)


class RouteTests(unittest.TestCase):
    def test_relays_asked_before_the_proof_arrived_are_named(self):
        timeline = [{'event': 'return_visit', 'relay': 'C', 'receipt': False},
                    {'event': 'return_visit', 'relay': 'A', 'receipt': True}]
        self.assertEqual(route(timeline), {'proof_via': 'A', 'missing_before': ['C'], 'visits': 2})

    def test_no_proof_anywhere_is_reported_as_such(self):
        timeline = [{'event': 'return_visit', 'relay': r, 'receipt': False} for r in 'ABC']
        self.assertEqual(route(timeline), {'proof_via': None, 'missing_before': ['A', 'B', 'C'], 'visits': 3})


if __name__ == "__main__":
    unittest.main()
