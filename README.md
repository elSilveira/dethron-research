# Dethron

Verifiable message delivery over [Reticulum](https://reticulum.network/) and LXMF,
with a harness that treats every claim as something to knock down before publishing.

## What this solves

**Guaranteed** delivery is impossible over intermittent contact: if the recipient
never appears, nothing reaches them. What is possible is **verifiable** delivery —
knowing, with cryptographic proof and without trusting the relay, which state a
message is in:

| State | Proof |
| --- | --- |
| **Entered** | The relay signs a custody attestation for that message, for that recipient. A relay that attests and does not deliver **is named** |
| **Pending** | Telling *awaiting contact* apart from *attested and not delivered* — localizable pendency, not a silence |
| **Left** | The recipient signs a receipt that returns to the origin, even when origin and destination are never online together |

## What is proved

Each line has a document, controls that must fail, declared limits, and
[published artifacts](window/evidence/README.md):

- **[V1](window/V1_CUSTODY.md)** — signed custody, proof of entry, localizable
  pendency, and a [receipt returning](window/V1_RECEIPT_RETURN.md) to the origin.
- **[V2](window/V2_REPRODUCTION.md)** — reproduction on an independent machine,
  following the document alone.
- **[V3c](window/V3C_BENCH.md)** — a 16 KiB object crossed between two machines over
  a link that **carries no IP**, with the recipient proved to hold no IP interface
  at all, and the machines proved distinct.

The full index, G0 through V3, is in [window/](window/README.md). The
[master plan](DETHRON_MASTER_PLAN.md) carries the hypotheses, the criteria, and what
was abandoned — including G2, closed with **no general advantage**, recorded as such.

## What does not exist yet

This is a harness with evidence, not a product. Plainly:

- **There is no client.** Nodes are driven by benches. Nobody installs this and sends
  a message.
- **Scale was never measured.** One message, one relay, one recipient, 16 KiB.
- **Windows only.** It has never run on Linux or Android.
- **Laboratory keys.** There is no key exchange and no contact discovery.
- **No written threat model.** The tests cover cases; the document is missing.

## Verify

```powershell
python -m venv window/.venv-gateway
window/.venv-gateway/Scripts/python.exe -m pip install -r window/requirements-gateway.txt
window/.venv-gateway/Scripts/python.exe window/run_v2_reproduction.py --fast-only
```

Expected: `ran=166 skipped=8 PASS`. The full guide, including the eight real
reproductions, is [V2_REPRODUCTION.md](window/V2_REPRODUCTION.md).

## How this repository treats evidence

- A control that **must not** pass accompanies every claim. G4's `dark` control once
  passed by accident; the record says so.
- Numbers come from artifacts, not from memory. The cited artifacts are published.
- What failed stays written. Every document has a rounds-and-checks section listing
  the errors found, including mine.
- A real LXMF defect was found, reproduced and fixed: see
  [window/upstream/](window/upstream/lxmf-stamp-zerodivision.md). Submitting it
  upstream is blocked — the maintainer has withdrawn and issues are disabled.

## Licence

[Apache 2.0](LICENSE). Reticulum and LXMF are dependencies under their own licences;
this work imports them, it does not derive from them.

## History

This repository contains work that predates Dethron — BitNet/Genesis probes, Rust
crates, a neural worker and a browser dashboard. That material left the tree in
September 2026 and **remains in the git history**, recoverable by anyone who wants it.

The documents were written in Portuguese and translated into English in September
2026; the code and the commit messages have always been in English. Where a document
quotes a number from the tree of its own day, it says so rather than being silently
updated.
