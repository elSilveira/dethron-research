"""Minimal reproduction of the LXMF stamp defect. No network, no Reticulum instance.

    python repro_lxmf.py

Prints the observed behaviour of LXStamper.generate_stamp for a cheap stamp, both
with the real clock and with a clock that does not advance.
"""
import os
import platform
import sys
import time
from unittest import mock

import LXMF
from LXMF import LXStamper

PEERING = LXStamper.WORKBLOCK_EXPAND_ROUNDS_PEERING

print(f'LXMF {LXMF.__version__}, Python {platform.python_version()}, {platform.platform()}')
print(f"time.time nominal resolution: {time.get_clock_info('time').resolution} s")

steps = set()
for _ in range(200000):
    a, b = time.time(), time.time()
    if b != a:
        steps.add(b-a)
print(f'smallest observed time.time step: {min(steps)*1000:.4f} ms' if steps else 'no step observed')

print('\nA. real clock, peering workblock (25 expand rounds), 20 runs per cost')
for cost in (1, 8, 12):
    raised = 0
    for _ in range(20):
        try:
            LXStamper.generate_stamp(os.urandom(32), cost, expand_rounds=PEERING)
        except ZeroDivisionError:
            raised += 1
    print(f'  stamp_cost={cost:<3} ZeroDivisionError in {raised}/20 runs')

print('\nB. clock frozen, which is what a sub-tick search observes')
with mock.patch.object(LXStamper.time, 'time', lambda: 1000.0):
    try:
        LXStamper.generate_stamp(os.urandom(32), 1, expand_rounds=PEERING)
        print('  no exception')
    except ZeroDivisionError as exc:
        print(f'  ZeroDivisionError: {exc}')

print('\nC. the stamp that was thrown away is recoverable: the search had already finished')
with mock.patch.object(LXStamper.time, 'time', lambda: 1000.0):
    workblock = LXStamper.stamp_workblock(os.urandom(32), expand_rounds=PEERING)
    stamp, rounds = LXStamper.job_simple(1, workblock, b'x'*32)
    print(f'  job_simple returned a stamp after {rounds} rounds, '
          f'value {LXStamper.stamp_value(workblock, stamp)}')
sys.exit(0)
