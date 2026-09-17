import tempfile
from pathlib import Path
import unittest

try:
    import RNS
except ImportError as exc:
    raise unittest.SkipTest("requires .venv-gateway") from exc

from gateway_archive import check_schedule, check_absent_store


class ArchiveTests(unittest.TestCase):
    def test_receiver_before_origin_stops_is_rejected(self):
        rows = [{"event": "start", "node": "O", "time": 1},
                {"event": "verified_receipt", "time": 2}]
        with self.assertRaises(ValueError):
            check_schedule(rows)

    def test_origin_restart_is_rejected(self):
        rows = [{"event": "killed", "node": "O", "exit_code": 23, "time": 1},
                {"event": "distribution_complete", "time": 2},
                {"event": "start", "node": "O", "time": 3},
                {"event": "verified_receipt", "time": 4}]
        with self.assertRaises(ValueError):
            check_schedule(rows)

    def test_unrelated_stored_message_cannot_pass_negative_control(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "unrelated").write_bytes(b"x" * 150)
            with self.assertRaises(ValueError):
                check_absent_store(path, "00" * 16)


if __name__ == "__main__":
    unittest.main()
