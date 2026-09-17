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

from dethron_gateway.custody import attest, request
from dethron_gateway.protocol import encode
from v1_audit import entry_proofs, pendency


def endpoint(identity):
    return RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")


def packed(obj, source, destination):
    message = LXMF.LXMessage(destination, source, encode(obj), "dethron-g1")
    message.pack()
    return message.packed


class EntryProofTests(unittest.TestCase):
    """The auditor must never promote a handoff, or the wrong packet, into proof of entry."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.origin_dir = Path(self.temp.name)/'O.offline'
        (self.origin_dir/'custody').mkdir(parents=True)
        self.origin_identity, self.relay_identity = RNS.Identity(), RNS.Identity()
        self.origin, self.relay = endpoint(self.origin_identity), endpoint(self.relay_identity)
        self.stored = b"lxmf bytes plus stamp"
        self.tid = hashlib.sha256(b"the message").hexdigest()
        self.m = {'source': {'destination': self.origin.hash.hex()},
                  'destination': {'destination': 'd'*32},
                  'relays': {'A': {'public_key': self.relay_identity.get_public_key().hex()}}}
        self.handoffs = {'A': self.tid}
        self.inventories = {'A': [hashlib.sha256(self.stored).hexdigest()]}

    def custody_file(self, tid=None, recipient='d'*32, stored=None):
        req = request(self.origin.hash.hex(), self.relay.hash.hex(), tid or self.tid,
                      self.origin_identity.get_public_key().hex(), expires=100)
        obj = attest(req, self.relay.hash.hex(), recipient, stored or self.stored, 50)
        (self.origin_dir/'custody'/f'{self.tid}.lxmf').write_bytes(packed(obj, self.relay, self.origin))

    def test_a_handoff_alone_is_not_proof_of_entry(self):
        proofs, missing = entry_proofs(self.origin_dir, self.m, self.handoffs, self.inventories, 10)
        self.assertEqual(proofs, {})
        self.assertEqual(missing, ['A'])

    def test_a_verified_custody_packet_is_proof_of_entry(self):
        self.custody_file()
        proofs, missing = entry_proofs(self.origin_dir, self.m, self.handoffs, self.inventories, 10)
        self.assertEqual(missing, [])
        self.assertEqual(proofs['A']['transient_id'], self.tid)
        self.assertEqual(proofs['A']['stored_size'], len(self.stored))

    def test_custody_for_another_message_or_recipient_is_refused(self):
        self.custody_file(tid=hashlib.sha256(b"other").hexdigest())
        with self.assertRaises(ValueError):
            entry_proofs(self.origin_dir, self.m, self.handoffs, self.inventories, 10)
        self.custody_file(recipient='e'*32)
        with self.assertRaises(ValueError):
            entry_proofs(self.origin_dir, self.m, self.handoffs, self.inventories, 10)

    def test_custody_must_match_what_the_relay_really_stored(self):
        self.custody_file(stored=b"something else")
        with self.assertRaises(ValueError):
            entry_proofs(self.origin_dir, self.m, self.handoffs, self.inventories, 10)


class PendencyTests(unittest.TestCase):
    def setUp(self):
        self.m = {'placement': {'A': 0, 'B': 1, 'C': 2}}
        self.proofs = {'A': {}, 'B': {}, 'C': {}}

    def test_custody_never_implies_delivery(self):
        result = pendency(self.m, self.proofs, parts=set(), fetched=set())
        self.assertEqual(result['awaiting_contact'], ['A', 'B', 'C'])
        self.assertEqual(result['attested_not_delivered'], [])

    def test_a_relay_that_attested_and_did_not_deliver_is_named(self):
        result = pendency(self.m, self.proofs, parts={0, 2}, fetched={'A', 'B', 'C'})
        self.assertEqual(result['attested_not_delivered'], ['B'])
        self.assertEqual(result['awaiting_contact'], [])

    def test_a_relay_without_custody_is_not_blamed(self):
        result = pendency(self.m, {'A': {}, 'C': {}}, parts={0, 2}, fetched={'A', 'B', 'C'})
        self.assertEqual(result['attested_not_delivered'], [])


if __name__ == "__main__":
    unittest.main()
