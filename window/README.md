# Milestones and harness

Each milestone has a document stating its contract, its result, the **controls that
must fail**, its limits and how to reproduce it. The [cited evidence](evidence/README.md)
is published: you can recompute instead of believe.

| Milestone | What it establishes |
| --- | --- |
| [G0](G0_REFERENCE.md) | Real integration with Reticulum/LXMF; messages survive the propagation nodes crashing |
| [G1](G1_INTEGRATION.md) | Persistent mailbox, receipts, a closed protocol |
| [G2](G2_PARTS.md) | Complementary parts and reconstruction. **Closed with no general advantage** — the record says so |
| [G3](G3_GENERATIONS.md) | Generations of nodes and supervisors; nodes outlive whoever created them |
| [G4](G4_INDEPENDENCE.md) | Delivery with the IP stack cut, plus the control that fails when the cut did not happen |
| [V1](V1_CUSTODY.md) | Signed custody: proof of entry and localizable pendency. And the [receipt returning](V1_RECEIPT_RETURN.md) to an origin that was never online with the destination |
| [V2](V2_REPRODUCTION.md) | A reproduction guide for an independent machine, with a single runner |
| [V3a](V3A_BENCH.md) | Two-machine bench, isolated windows, rendezvous by declared instant |
| [V3c](V3C_BENCH.md) | **An object crossed over a medium that carries no IP**, with the recipient proved to hold no IP interface |

To prepare two machines from scratch: [step by step](V3_SETUP.md).

Published on 20/09/2026, and [what would refute it](ADOPTION.md) written down before
the answer was known.

## Layout

| Path | What it is |
| --- | --- |
| `dethron_gateway/` | The library: protocol, wire, custody, parts, reconstruction, mailbox |
| `g1_*`–`g4_*`, `v1_*` | Each milestone's laboratory and auditor |
| `v2_*` | Reproduction runner and diagnosis |
| `v3_*` | Multi-machine bench: schedule, agent, executor, auditor, serial probe |
| `run_*.py` | The entry points. Nothing else is meant to be called by hand |
| `tests/` | 166 tests; 8 are real reproductions that only run on demand |
| `evidence/` | The artifacts the documents cite |
| `upstream/` | A defect found in LXMF, with a reproduction and a fix |

## Running

```powershell
python -m venv window/.venv-gateway
window/.venv-gateway/Scripts/python.exe -m pip install -r window/requirements-gateway.txt
```

The suite, from the repository root:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v2_reproduction.py --fast-only
```

Expected: `ran=166 skipped=8 PASS`. The 8 skipped are the real reproductions, which
take about an hour and run with `run_v2_reproduction.py` without `--fast-only`.

Every source file is under 200 lines, by project convention.
