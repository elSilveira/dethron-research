# Connected DNA recovery

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Prova de recuperação no escopo declarado abaixo. Sobrevivencia local com réplicas não implica autonomia da internet nem garantia de que quaisquer 5% dos nós preservem conectividade e dados. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Implemented in `network::recovery_dna` and `network::recovery_plan`.

A recoverable DNA unit contains payload bytes and content-addressed child links.
A root manifest connects task definitions to branch units and individual source
facts. The source fields include identity, context, revision and revocation;
additional provenance metadata is preserved. Queries remain in the root plan.
These are data structures and bounded recovery routines, not autonomous learned
agents or executable instructions.

## Reconstruction contract

1. Preserve a unit by serializing its payload and child links, hashing that
   representation, then encrypting/authenticating it with the existing AES-GCM
   implementation. The hash identifies the plaintext unit, not its ciphertext.
2. Start recovery with an owner-trusted root and encryption key. Fetch available
   replicas, authenticate/decrypt each candidate, then check its content hash.
3. Follow verified child links. Visit shared IDs once. A damaged replica can be
   bypassed only when another candidate supplies the exact verified unit.
4. Return the complete graph only when every required unit is present. A missing
   dependency, wrong key, altered identity or exhausted budget fails explicitly.
5. Rebuild source arrays in their recorded order, validate the recovered DNA,
   and pass the recovered plan to the existing worker/evidence runtime.

Encryption reverses an encoding when the key and ciphertext survive. Graph
recovery reconnects surviving content through verified references. A hash alone
cannot recreate lost bytes. This implementation uses replicas, not erasure coding,
learned reconstruction, inference of missing facts or universal recovery.

Exact graph recovery and semantic conclusion recovery are different contracts:
`recovery_plan` requires all referenced units; `AtomicDna::reconstruct` may derive
a conclusion from a surviving alternative route. Losing an optional reasoning
route need not lose the conclusion, but does prevent claiming full original-plan
recovery if that route's bytes cannot be restored.

## Running the connection

From `v2`, use new output/key paths with existing parent directories:

```powershell
cargo run --release --locked --offline --example recover_plan -- preserve input.json results/new-units ../window/private/new-key.bin
cargo run --release --locked --offline --example recover_plan -- recover TRUSTED_ROOT results/new-units ../window/private/new-key.bin
cargo run --release --locked --offline --example recognize_plan -- results/new-units/recovered-config.json results/selected-plan.json
```

The disk example writes two replicas and a root reference. Preserve the trusted
root separately; do not accept a root supplied by an untrusted store as authority.
The key is outside the replica directories. The same-machine copies demonstrate
file-corruption recovery, not resilience against losing the machine or disk.
No automatic key lifecycle, remote transport, repair, retention tiers or source
extraction from prose has been added. Existing journal recovery remains separate;
the recovered config can be supplied to its existing API when persistence is configured.

Limits: 64 KiB payload per unit, 64 child links, 512 reachable units, 16 MiB total
payload, 16 replica candidates per fetch and 128 tasks per plan. The caller's fetch
adapter must enforce I/O deadlines and allocation bounds; the core cannot bound
allocations or blocking work performed inside caller code. Root manifests must
fit the unit size limit. No automatic arbitrary-file chunking is provided.
Content identifiers expose equality and are not secret commitments. Trust in a
root authenticates a chosen version, not its freshness or external factual truth.

## Validation

Behavioral failing tests preceded implementation. Tests cover linked/shared units,
corrupt-replica fallback, missing data, wrong keys/IDs, payload/link limits, and
restoration of task DNA including provenance metadata. The metadata test first
exposed and then prevented silent loss during source normalization.

The connected model experiment is in `results/connected-recovery-20260915/`:
49 units, a fresh recovery process, five deliberately corrupted primary copies,
and equality of the recovered task plan before model execution. New wording and
unsupported-evidence cases are evaluated only after recovery. Raw guesses remain
visible; DNA acceptance does not overwrite them with the verifier's conclusion.

This is a concrete bounded implementation of connected recovery. It does not yet
implement the full vision of distributed recovery TRONs, autonomous discovery of
connections, long-term memory policies or recreation without surviving content.
