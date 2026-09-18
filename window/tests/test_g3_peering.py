"""The handover depends on an LXMF scheduling rule; if that rule changes, fail here first."""
import unittest

try:
    from LXMF.LXMPeer import LXMPeer
except ImportError as exc:  # pragma: no cover - needs the pinned environment
    raise unittest.SkipTest('requires .venv-gateway') from exc

from g3_lab import HANDOVER_RETRY, HANDOVER_TIMEOUT, PATH_WAIT


class PeeringHazardTests(unittest.TestCase):
    """A sync asked before a path exists postpones the peer far beyond our deadline.

    The second machine's G3 failed exactly this way: one pathless sync, then every
    retry refused as not yet due, then our timeout. The node now waits for the path.
    """

    def test_the_backoff_would_outlast_the_handover_deadline(self):
        self.assertGreater(LXMPeer.SYNC_BACKOFF_STEP, HANDOVER_TIMEOUT,
                           'if LXMF shortened its backoff, waiting for a path may no longer be critical')

    def test_the_path_wait_fits_inside_one_retry_interval(self):
        # Otherwise a retry would fire while the previous attempt is still waiting for a path.
        self.assertGreater(HANDOVER_TIMEOUT, PATH_WAIT)
        self.assertGreaterEqual(HANDOVER_RETRY, LXMPeer.PATH_REQUEST_GRACE,
                                'a retry faster than the grace period would re-ask before LXMF answers')

    def test_several_attempts_fit_in_the_deadline(self):
        self.assertGreaterEqual(HANDOVER_TIMEOUT//HANDOVER_RETRY, 5)


if __name__ == '__main__':
    unittest.main()
