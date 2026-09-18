"""Keep an LXMF defect from discarding a valid stamp.

`LXStamper.generate_stamp` computes the stamp, then evaluates
`speed = rounds/duration` only to write a debug log line. On Windows
`time.time()` has a 15.6 ms resolution, so a cheap stamp finishes inside a
single tick, `duration` is 0.0, and a `ZeroDivisionError` throws away a result
that was already correct.

The crash is silent exactly where it hurts: `LXMPeer` generates the peering key
in a daemon thread, so the key is simply never set, `peering_key_ready()` stays
false, every sync is postponed "since a peering key has not been generated yet",
and a handover times out with nothing in the timeline to explain it. A peering
workblock uses only 25 expand rounds, so with a low peering cost the race is
almost always lost. This was observed on a second machine where G3 failed every
time, and the same traceback is present in this machine's artifacts, where the
race sometimes resolved in time and the run passed.

`install()` restores upstream's own computation without the log division. LXMF
stays pinned at 1.1.1 for reproducibility: this is a workaround, not a fork, and
the defect should be reported upstream.
"""
import inspect

from LXMF import LXStamper
from RNS.vendor import platformutils

DEFECT = 'speed = rounds/duration'


def generate_stamp(message_id, stamp_cost, expand_rounds=LXStamper.WORKBLOCK_EXPAND_ROUNDS):
    """Upstream's dispatch and result, minus the division that only feeds a log line."""
    workblock = LXStamper.stamp_workblock(message_id, expand_rounds=expand_rounds)
    if platformutils.is_windows() or platformutils.is_darwin():
        stamp, rounds = LXStamper.job_simple(stamp_cost, workblock, message_id)
    elif platformutils.is_android():
        stamp, rounds = LXStamper.job_android(stamp_cost, workblock, message_id)
    elif LXStamper.USE_WORKER_MANAGER:
        stamp, rounds = LXStamper.job_linux_managed(stamp_cost, workblock, message_id)
    else:
        stamp, rounds = LXStamper.job_linux(stamp_cost, workblock, message_id)
    value = LXStamper.stamp_value(workblock, stamp) if stamp is not None else 0
    return stamp, value


def defect_present():
    """False once upstream guards the division, so the workaround can be dropped."""
    try:
        return DEFECT in inspect.getsource(LXStamper)
    except OSError:
        return True


def install():
    """Idempotent. Returns whether the upstream defect is still present."""
    if getattr(LXStamper.generate_stamp, '__module__', None) != __name__:
        LXStamper.generate_stamp = generate_stamp
    return defect_present()
