"""Synthetic signed archives test the evaluator; they are not network evidence."""
import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import tempfile
import unittest

try:
    import LXMF
    import RNS
except ImportError as exc:
    raise unittest.SkipTest("requires .venv-gateway") from exc

from dethron_gateway.protocol import data_envelope, encode, receipt_envelope
from run_g1_probe import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = RNS.Destination(RNS.Identity(), RNS.Destination.OUT,
                                      RNS.Destination.SINGLE, "lxmf", "delivery")
        self.dest = RNS.Destination(RNS.Identity(), RNS.Destination.OUT,
                                    RNS.Destination.SINGLE, "lxmf", "delivery")
        self.message = data_envelope(self.source.hash.hex(), self.dest.hash.hex(), b"test", 100)
        negative = data_envelope(self.source.hash.hex(), "0"*32, b"absent", 100)
        manifest = {"source": self.info(self.source), "destination": self.info(self.dest),
                    "message": self.message, "negative": negative}
        (self.root / "manifest.json").write_text(json.dumps(manifest))
        for name in ("O", "D"):
            (self.root / name).mkdir()
            with self.db(name) as db:
                db.execute("CREATE TABLE messages(body BLOB,wire BLOB,state TEXT,direction TEXT)")
        with self.db("D") as db:
            db.execute("INSERT INTO messages VALUES (?,?,'received','in')",
                       (encode(self.message), self.packet(self.message, self.source, self.dest)))
        with self.db("O") as db:
            db.execute("INSERT INTO messages VALUES (?,?,'confirmed','out')",
                       (encode(self.message), self.packet(receipt_envelope(self.message), self.dest, self.source)))
            db.execute("INSERT INTO messages VALUES (?,X'','expired','out')", (encode(negative),))

    @contextmanager
    def db(self, name):
        db = sqlite3.connect(self.root / name / "mailbox.db")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def info(dest):
        return {"destination": dest.hash.hex(), "public_key": dest.identity.get_public_key().hex()}

    @staticmethod
    def packet(obj, source, dest):
        message = LXMF.LXMessage(dest, source, encode(obj), "dethron-g1")
        message.pack()
        return message.packed

    def test_valid_archive_passes(self):
        self.assertEqual(audit(self.root), "passed")

    def test_receipt_for_different_expiry_is_rejected_even_with_valid_signature(self):
        altered = {**receipt_envelope(self.message), "expires": 101}
        with self.db("O") as db:
            db.execute("UPDATE messages SET wire=? WHERE state='confirmed'",
                       (self.packet(altered, self.dest, self.source),))
        with self.assertRaises(ValueError):
            audit(self.root)

    def test_altered_sender_obligation_cannot_pass_using_a_valid_receipt(self):
        with self.db("O") as db:
            db.execute("UPDATE messages SET body=? WHERE state='confirmed'",
                       (encode({**self.message, "size": 7}),))
        with self.assertRaises(ValueError):
            audit(self.root)


if __name__ == "__main__":
    unittest.main()
