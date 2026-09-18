"""The LXMF stamp defect, proven deterministically, and a guard for when upstream fixes it."""
import inspect
import os
import unittest
from unittest import mock

try:
    from LXMF import LXStamper
    from dethron_gateway.lxmf_stamp import DEFECT, UPSTREAM, defect_present, generate_stamp, install
except ImportError as exc:  # pragma: no cover - needs the pinned environment
    raise unittest.SkipTest('requires .venv-gateway') from exc

PEERING = LXStamper.WORKBLOCK_EXPAND_ROUNDS_PEERING


def frozen_clock():
    """A clock that does not advance is exactly what a fast search sees."""
    return 1000.0


class StampDefectTests(unittest.TestCase):
    def test_the_unguarded_division_is_still_in_the_pinned_version(self):
        self.assertIn(DEFECT, inspect.getsource(LXStamper))
        self.assertTrue(defect_present())

    def test_upstream_destroys_a_valid_stamp_when_the_clock_does_not_advance(self):
        with mock.patch.object(LXStamper.time, 'time', frozen_clock):
            with self.assertRaises(ZeroDivisionError):
                UPSTREAM(os.urandom(32), 1, expand_rounds=PEERING)

    def test_the_workaround_returns_the_stamp_under_the_same_clock(self):
        with mock.patch.object(LXStamper.time, 'time', frozen_clock):
            stamp, value = generate_stamp(os.urandom(32), 1, expand_rounds=PEERING)
        self.assertIsNotNone(stamp)
        self.assertGreaterEqual(value, 1)

    def test_a_cheap_peering_stamp_always_returns_a_usable_value(self):
        install()
        for _ in range(40):
            stamp, value = generate_stamp(os.urandom(32), 1, expand_rounds=PEERING)
            self.assertIsNotNone(stamp)
            self.assertGreaterEqual(value, 1)

    def test_installing_replaces_the_upstream_function_once(self):
        self.assertTrue(install())
        self.assertEqual(LXStamper.generate_stamp.__module__, 'dethron_gateway.lxmf_stamp')
        install()
        self.assertIs(LXStamper.generate_stamp, generate_stamp)


if __name__ == '__main__':
    unittest.main()
