"""The workaround for the LXMF stamp defect, and a guard for when upstream fixes it."""
import inspect
import os
import time
import unittest

try:
    from LXMF import LXStamper
    from dethron_gateway.lxmf_stamp import DEFECT, defect_present, generate_stamp, install
except ImportError as exc:  # pragma: no cover - needs the pinned environment
    raise unittest.SkipTest('requires .venv-gateway') from exc


class StampDefectTests(unittest.TestCase):
    """A cheap stamp finishing inside one clock tick must not destroy the result."""

    def test_the_hazard_is_real_in_the_pinned_version(self):
        self.assertIn(DEFECT, inspect.getsource(LXStamper))
        self.assertTrue(defect_present())
        if os.name == 'nt':
            self.assertGreater(time.get_clock_info('time').resolution, .001,
                               'a coarse clock is what makes a cheap stamp divide by zero')

    def test_a_cheap_peering_stamp_always_returns_a_usable_value(self):
        install()
        for _ in range(40):
            stamp, value = generate_stamp(os.urandom(32), 1,
                                          expand_rounds=LXStamper.WORKBLOCK_EXPAND_ROUNDS_PEERING)
            self.assertIsNotNone(stamp)
            self.assertGreaterEqual(value, 1)

    def test_installing_replaces_the_upstream_function_once(self):
        self.assertTrue(install())
        self.assertEqual(LXStamper.generate_stamp.__module__, 'dethron_gateway.lxmf_stamp')
        install()
        self.assertIs(LXStamper.generate_stamp, generate_stamp)


if __name__ == '__main__':
    unittest.main()
