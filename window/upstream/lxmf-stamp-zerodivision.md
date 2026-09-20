# Upstream report: `generate_stamp` discards a valid stamp with `ZeroDivisionError`

Written for whoever maintains an LXMF fork, so the report below is in English and
assumes no knowledge of this project. Reproduction script:
[`repro_lxmf_stamp.py`](repro_lxmf_stamp.py); the change itself is in
[`pull-request.md`](pull-request.md).

Confirmed present in **LXMF 1.1.1** — the latest release on PyPI — and in
`markqvist/LXMF` `master` at commit `795fdaa`.

## Where this goes, and where it does not

**Not to `markqvist/LXMF`.** Its `MIRROR.md` says the author is stepping back from all
public-facing interaction, that there will be no responses to issues or discussions, and
that this is not a temporary break. The pull request form is still technically open, and
that is not an invitation: a good patch is still one more demand on someone who asked, in
plain words, to be left alone. The defect is published here instead, with everything
needed to apply it.

Anyone maintaining a fork is welcome to take this. No attribution is asked for.

## Re-verified 20/09/2026

Against `markqvist/LXMF` `master` at `795fdaa` (pushed 2026-07-20; upstream has not moved
since this was first written), with `rns 1.5.4`, on Windows 11 and Python 3.10.11:

| | Section B of the reproduction, clock frozen |
| --- | --- |
| Unpatched `795fdaa` | `ZeroDivisionError: float division by zero` |
| With the change below | `no exception` |

Section C of the same run shows why this is a defect rather than a cosmetic slip: the
stamp had already been found. `job_simple` returns it after 2 rounds, value 3 — the work
was complete, and a logging line threw the result away.

The patch in [`0001-guard-rate-calculations.patch`](0001-guard-rate-calculations.patch)
still applies cleanly to `795fdaa` and guards all four rate calculations — three in
`LXStamper.py`, one in `LXMPeer.py`.

---

## Title

`generate_stamp` raises `ZeroDivisionError` and discards a valid stamp when the search completes within one clock tick

## Body

### Summary

`LXStamper.generate_stamp` computes the stamp, then evaluates `speed = rounds/duration`
solely to build a debug log message. When `duration` is `0.0`, the resulting
`ZeroDivisionError` propagates out of the function and destroys a stamp that had
already been found.

The most damaging consequence is silent: `LXMPeer.sync()` generates the peering key
in a daemon thread, so the exception only reaches that thread's stderr. The peering
key is never set, `peering_key_ready()` stays `False`, and every subsequent `sync()`
is postponed with *"since a peering key has not been generated yet"*. Propagation
node peering then never proceeds, with no error surfaced to the application.

### Where

`LXMF/LXStamper.py`, in `generate_stamp` (line 139 in `master` at `795fdaa`, same in 1.1.1):

```python
    workblock = stamp_workblock(message_id, expand_rounds=expand_rounds)

    start_time = time.time()
    ...
    duration = time.time() - start_time
    speed = rounds/duration          # <-- raises when duration == 0.0
    if stamp != None: value = stamp_value(workblock, stamp)

    RNS.log(f"Stamp with value {value} generated in {RNS.prettytime(duration)}, {rounds} rounds, {int(speed)} rounds per second", RNS.LOG_DEBUG)
```

`start_time` is taken *after* the workblock expansion, so `duration` times only the
search. For a low stamp cost that search finishes in tens of microseconds, well
below the granularity of `time.time()` on Windows.

Three further rate calculations divide by an interval that can be zero for the same
reason. Two of them are on paths where the exception would propagate:

| Location | Propagates? |
| --- | --- |
| `LXStamper.generate_stamp` | yes — the case reported here |
| `LXStamper.job_simple`, every 2500 rounds | yes |
| `LXMPeer.resource_concluded` | yes — a small transfer over a fast link can conclude within one tick, inside a Reticulum resource callback |
| `LXStamper.job_linux` | no — inside a `try`/`except`, so only logged |

### Why it is easy to miss

Whether `duration` comes out as exactly `0.0` depends on the machine's clock
granularity, which on Windows varies with what else is running. On one machine the
same code path raised intermittently and the failure looked environmental; on
another it raised every time.

The peering path is the most exposed, because `WORKBLOCK_EXPAND_ROUNDS_PEERING` is
25, making a peering stamp far cheaper than a message stamp.

### Reproduction

```
pip install lxmf==1.1.1
python repro_lxmf_stamp.py
```

Observed on Windows 11, Python 3.10.11, LXMF 1.1.1:

```
time.time nominal resolution: 0.015625 s
smallest observed time.time step: 0.4995 ms

A. real clock, peering workblock (25 expand rounds), 20 runs per cost
  stamp_cost=1   ZeroDivisionError in 19/20 runs
  stamp_cost=8   ZeroDivisionError in 5/20 runs
  stamp_cost=12  ZeroDivisionError in 0/20 runs

B. clock frozen, which is what a sub-tick search observes
  ZeroDivisionError: float division by zero

C. the stamp that was thrown away is recoverable: the search had already finished
  job_simple returned a stamp after 3 rounds, value 1
```

Section C shows the stamp is found before the exception: only the log arithmetic
fails. The frozen-clock case in section B is deterministic and platform independent
— it is what a sufficiently fast search observes on any platform whose clock does
not advance during it.

### Effect observed in practice

Two propagation nodes, `autopeer` disabled, peering driven explicitly with
`router.peer(...)` followed by `LXMPeer.sync()`:

- the peering key thread dies with this traceback,
- every later `sync()` logs *"Postponing sync with peer ... since a peering key has not been generated yet"*,
- messages already queued for the peer never transfer,
- the application sees only a timeout, with nothing in the router state to explain it.

Raising `peering_cost` does not solve it. It only lowers the odds — 4 and 5 in 20
across two runs at cost 8 on the machine above — while costing real work: roughly
100 ms at cost 14 and 800 ms at cost 18 per peering key.

### Suggested fix

`speed` is only used to format a log line, so guarding the division is enough. Note
that the guard has to yield a finite value: `float("inf")` would move the failure to
`int(speed)`, which raises `OverflowError`.

```python
    duration = time.time() - start_time
    speed = rounds/duration if duration > 0 else 0
```

Reporting `0` when the interval is immeasurably short is harmless, because each of
these messages also carries the round or byte count.

Using `time.perf_counter()` for these measurements would additionally avoid the zero
and make the reported rates accurate, but it changes the clock domain, so it is kept
out of the minimal fix.

A pull request with this change applied to all four sites is described in
[`pull-request.md`](pull-request.md).

### Environment

- LXMF 1.1.1 (also present in `master` at `795fdaa`)
- RNS 1.5.4
- Python 3.10.11
- Windows 11 (build 26200); the frozen-clock case is platform independent
