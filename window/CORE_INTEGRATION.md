# Core runtime integration

The evidence-aware worker network is now owned by `v2`:

- `v2/src/network`: task/configuration contracts, bounded concurrent execution,
  dependency waves, source recognition, acceptance, and local/SSH endpoints.
- `v2/src/neural`: resident worker client, process transport, and identity/response
  validation. The worker backend remains the Python package in `window`.
- `window/src/network`: synthetic accuracy/throughput workloads and reporting.
  Public compatibility exports preserve existing harness imports.
- `window/src/neural`: experimental memory/adaptation controller and its probes;
  transport imports delegate to v2.

This makes the reusable runtime callable as `tron_v2::network::run` without a
dependency on the window Rust crate. It does not yet persist network task graphs
in `Tron` snapshots or sign evidence packets with a TRON identity. Those are
separate reliability slices, not implied by moving modules into the core.

## Reliability regression

A new direct-core probe demonstrated that a custom Worker could return text with
zero generated tokens and be counted as completed. The core now requires exactly
one response output and, for generation, nonempty nonnegative integer token IDs,
a matching count within the task limit, and a recognized finish reason. Invalid
responses fail and consume their reserved budget. The existing acceptance tests
still prevent rejected or truncated answers from feeding downstream tasks.

Core tests cover independent overlapping work, dependency failures, context and
revision isolation, budget bounds, source identity rewrites, unsupported answers,
truncation, malformed DNA, and connector argument/identity handling. Some tests
also remain in window to check compatibility; counts across crates are not counts
of distinct scenarios.

## Evidence and reproduction

`run_neural.py` and `run_network.py` now fingerprint v2 source/tests and Cargo
manifests as well as the harness. Before this change, the source manifest omitted
the sibling dependency. Old reports remain historical evidence, not manifests
of the integrated runtime.

```powershell
cargo test --manifest-path ../v2/Cargo.toml --locked --offline
cargo clippy --manifest-path ../v2/Cargo.toml --locked --offline --all-targets -- -D warnings
cargo test --locked --offline
python -m unittest discover -s tests -p 'test_*.py'
python run_network.py --experiment accuracy --workers 1 --device cuda
```

Next reliability work should address persisted task receipts, restart semantics,
worker replacement, and signed source lineage, each with injected-failure tests.
Energy measurement and model partitioning remain separate open probes. This
integration alone does not prove either benefit.

## Verified checkpoint

The real-model rerun is `results/network-20260914T140330Z-46932e75/`.
Source fingerprints include the actual v2 runtime and match the final code.
All seven trial accuracy totals match the previous harness run: held-out raw
5/40, examples 23/40, recognized evidence 35/40; recognized evidence accepts all
20 answerable cases with no wrong acceptances. Expansion remains 8/8 and the
protected wave accepts both answers. This is a migration regression check, not a
new independent accuracy benchmark.

Verification passed 35 v2 Rust tests, 58 window Rust tests, 20 Python tests,
Clippy for both crates, and formatting checks. Some core scenarios are exercised
in both crates. All source/test files remain within 200 lines. No browser changes
were made and browser QA was not repeated. Cross-machine execution, energy, and
crash recovery of the network remain untested in this checkpoint.
