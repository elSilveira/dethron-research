# TRON v2 prototype

A Rust experiment in bounded strategy selection, inherited memoized knowledge,
private audit commitments, encrypted snapshots, and ternary payload encoding.
It runs integer factorization on classical hardware. It does not implement
distributed language-model inference, source-code synthesis, or quantum computing.

From this directory, with Rust 1.89 or later and the locked dependencies cached:

```powershell
cargo test --locked --offline
cargo run --release --locked --offline -- --help
cargo run --release --locked --offline -- probe 3 results/my-run.json
```

For an initial dependency fetch, omit `--offline`. Probe cycles range from 1 to
100; the default is 3. Omit the output path for JSON on stdout. Export requires
a new filename and an existing parent directory; existing reports are preserved.
Generated reports are ignored by version control.

The library exposes `Tron::run`, `evolve`, `spawn`, `checkpoint`, and `restore`.
Factorization inputs and division budgets range from 1 to 1,000,000. Knowledge
holds at most 128 entries. Evolution evaluates three fixed strategies against
training and validation fixtures and promotes only a measured improvement.
Children receive distinct signing identities and optionally inherit cached results.

Snapshots contain private state and signing material under encryption. The owner
must retain the encryption key and trusted signing key/latest checkpoint head
separately to restore and detect rollback. The CLI emits public evidence only;
it does not provide persistent key management. Public audit records reveal event
types, order, identity, and lineage links, while payload openings remain private.

Validation continued on 2026-09-13: 18 integration tests passed, including a
fresh-process snapshot restore, tampering and rollback rejection, factorization
checks through 5,000, ternary roundtrips, and CLI export collision handling.
Formatting and Clippy checks are also part of the local verification:

```powershell
cargo fmt -- --check
cargo clippy --locked --offline --all-targets -- -D warnings
```

The saved release smoke run is
[`results/probe-20260913-continued.json`](results/probe-20260913-continued.json).
Its environment and SHA-256 file inventory are in
[`results/probe-20260913-continued.manifest.json`](results/probe-20260913-continued.manifest.json).
It used rustc/cargo 1.89.0 on Windows and three evolution cycles:

| Measurement | Result |
| --- | ---: |
| Baseline workload divisions | 4,103 |
| Evolved workload divisions | 95 |
| Candidate evaluation divisions | 1,809 |
| Net divisions saved after evaluations | 2,199 |
| Baseline task time | 16,700 ns |
| Evolved task time | 1,000 ns |
| Evolution time | 445,400 ns |
| Ternary / two-bit payload for 100,000 symbols | 20,000 / 25,000 bytes |

Correctness, inherited recall after restore, audit verification, and encoding
roundtrip checks passed. The first cycle promoted a strategy; later cycles did
not. Evolution time exceeded the task time saved. Ternary packing saved 20% of
payload bytes versus two-bit packing, but encoding and decoding were slower in
this run. Headers and length metadata are excluded from the byte comparison.

These timings are one small smoke run, without confidence intervals or a full
lifecycle cost comparison. Random identities and commitments change on reruns.
The division counts describe this fixed workload and are not a general speedup
claim. The earlier root-level probe plan's distributed-inference gates remain
unimplemented by this prototype.

The next performance experiment should compare strategy selection with the best
fixed strategy on held-out repeated workloads, including evaluation and audit
overhead. Persistent execution also needs an explicit key-storage and audit
retention design before it becomes a durable service.

## Evidence-aware worker runtime

The core now exports `tron_v2::network` for bounded concurrent task execution,
versioned source DNA, acceptance checks, and local/SSH worker connectors.
`tron_v2::neural` provides resident process transport and model identity checks.
The window crate consumes these APIs and keeps the experimental workloads.
See [core integration](../window/CORE_INTEGRATION.md) for tests and scope.
This runtime does not yet attach network state to encrypted TRON snapshots,
implement model sharding, or establish physical energy savings.
## Persistent network execution

`network::run_persistent` adds an authenticated encrypted checkpoint journal.
Completed records survive process restart; uncertain in-flight tasks fail closed
and retain their reserved cost. See [persistence probes](../window/PERSISTENCE.md)
for configuration, tested guarantees, rollback limits, and key requirements.
This journal is separate from the original Tron snapshot API.