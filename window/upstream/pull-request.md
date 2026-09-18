# Pull request: guard rate calculations against a zero-length interval

Companion to [`lxmf-stamp-zerodivision.md`](lxmf-stamp-zerodivision.md), which is the
issue text. The change itself is in
[`0001-guard-rate-calculations.patch`](0001-guard-rate-calculations.patch) and
applies cleanly with `git am` to `markqvist/LXMF` at `795fdaa`.

## The change

Six insertions, four deletions, across two files. Four rate calculations divide by a
measured interval that can be `0.0`; all four exist only to build a log message, and
three of them are on paths where the exception propagates.

| Location | Before | After |
| --- | --- | --- |
| `LXStamper.generate_stamp` | `speed = rounds/duration` | guarded, `0` when the interval is zero |
| `LXStamper.job_simple` | `speed = rounds / (time.time()-st)` | interval bound to a local, then guarded |
| `LXStamper.job_linux` | `speed = total_rounds/elapsed` | guarded |
| `LXMPeer.resource_concluded` | `(size*8)/(time.time()-started)` | interval bound to a local, then guarded |

Clock sources are unchanged. `time.perf_counter()` would also avoid the zero and give
accurate rates, but it changes the clock domain, so it is offered separately in the
commit message rather than bundled here.

The guard yields `0`, not `float("inf")`: the log lines do `int(speed)`, and
`int(float("inf"))` raises `OverflowError`, which would only move the failure one line
down. Reporting `0` is harmless because each message also carries the round or byte
count.

## Evidence that it fixes the reported failure

The defect was found because a three-relay LXMF propagation scenario failed on one
machine and not another. With the patch applied and **no workaround of our own
active**, that scenario passes end to end:

| Run | LXMF | Our workaround | Result |
| --- | --- | --- | --- |
| Before | 1.1.1 as released | not yet written | handover timed out, `ZeroDivisionError` in node stderr |
| With workaround | 1.1.1 as released | active | passes |
| **With this patch** | `795fdaa` + this commit | **inactive** (`stamp_workaround: false` on every node) | **passes, 294 s** |

In the patched run all six relay handovers succeeded on the first sync attempt and no
node left a non-empty stderr. The scenario is `window/run_g3_probe.py` in
<https://github.com/elSilveira/dethron>; it starts eleven real Reticulum processes and
audits the delivered bytes.

## Filing it

The fork has to be created once, from the GitHub page for `markqvist/LXMF`. Then, from
the repository root:

```
git clone https://github.com/<your-user>/LXMF.git lxmf-fork
cd lxmf-fork
git am --3way ../dethron/window/upstream/0001-guard-rate-calculations.patch
git push origin HEAD:guard-rate-calculations
```

GitHub prints the pull request URL in the push output. Use the title and body from
[`lxmf-stamp-zerodivision.md`](lxmf-stamp-zerodivision.md), or open the issue first and
reference it from the pull request.

The patch carries the commit message, author and the `Co-Authored-By` line already.
