# Verified recipe replay and local regeneration

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Prova de recuperação no escopo declarado abaixo. Sobrevivencia local com réplicas não implica autonomia da internet nem garantia de que quaisquer 5% dos nós preservem conectividade e dados. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

The next milestone now has independent local TCP services with persistent stores,
fresh-process recovery, and bounded supervisor repair cycles. The Window runs and
explains the actual process-death probes: [process survival](../window/PROCESS_SURVIVAL.md).
The in-memory experiment below remains the earlier baseline, not the new result.

The v2 prototype now reconstructs byte objects by replaying versioned recipes.
Connected encrypted units supply the inputs; every operation has an expected
SHA-256 state hash, and the completed object has a final hash. Hashes verify
reconstruction; they do not supply missing content. Supported operations are
append, XOR, rotate, and bounded replacement, with no arbitrary code execution.

`network::recipe::replay` authenticates the connected units before replay.
`network::regeneration::regenerate` gathers units from surviving local stores,
checks the recipe, and creates fully replicated replacement stores. It fails
if required content is missing or authentication or state verification fails.
The caller supplies a trusted root and the encryption key.

## Measured result, 2026-09-15

Run from v2, choosing a new output directory:

```powershell
cargo run --release --locked --offline --example survival -- results/survival-new
```

[Saved summary](results/survival-20260915/summary.json) and
[individual trials](results/survival-20260915/trials.jsonl) record **20/20 passing**
trials with varied input bytes, survivor selections, and fresh encryption keys.
Each trial performs:

- One genesis store expands to 100 local stores.
- Five survivors rebuild 100 stores after the original network is dropped.
- A 64-byte object is reconstructed exactly through 33 verified operations.
- A corrupt replica is bypassed; two incomplete stores jointly supply the recipe.
- Missing required content and a wrong key are rejected.

These are deterministic recipe transformations, not learned evolutionary steps.
The test oracle includes independently specified literal states in the recipe
integration tests; the larger example builds its expected states procedurally.
There is no neural answer benchmark in this experiment.

## Meaning of 5% survival

Every generated store contains all required units. Consequently, even one intact
store can suffice when the caller retains the root and key. The 5% experiment
checks this recovery path, not a new redundancy threshold. Across the 100 rebuilt
stores, the first trial stores 1,422,500 ciphertext bytes for its recipe and inputs;
the final object is only 64 bytes. This includes recipe metadata and 100 copies,
but excludes in-memory container overhead. It is not a compression result.

The nodes are in-process storage objects. Expansion is explicitly invoked and
bounded to 100 targets, with at most 16 survivors per call. There is no automatic
failure detection, remote node provisioning, membership protocol, or indefinite
expansion. Trial keys are ephemeral and omitted from reports, so these reports
are not durable recovery backups.

The next distributed milestone is independent persistent stores with restart
recovery, retained keys and trusted roots, followed by failure detection and
automatic repair. A storage-efficient 5% target also needs an explicit redundancy
policy and tests of which required units survive; node count alone is insufficient.

## Validation

Behavioral tests cover recipe version and bounds, intermediate and final state
mismatches, missing connectors, wrong keys, and regeneration limits. A separate
numeric regression test exposed a one-bit floating-point JSON restore mismatch;
enabling serde_json's `float_roundtrip` feature preserves those journal values
exactly without relaxing the existing restore assertion.
