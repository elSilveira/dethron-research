# Dethron / Genesis / BitNet: current position

Review date: 14 September 2026. Code baseline: `d6ae601`, with the preceding
window checkpoint `56f7ca1`. This is a targeted source/document review and
reassessment of saved experiments, not a new energy benchmark or an exhaustive
audit of historical backups. No model was run during this review.

## Verdict

We have a credible experimental foundation for evidence-aware distributed task
execution. We have measured local concurrency and improved evidence-conditioned
answers. We have not measured energy savings or implemented a single model
partitioned across machines. These remain the two major product hypotheses.

The strongest near-term hypothesis is to reduce unnecessary computation while
preserving answer quality. Capacity expansion through model sharding should be
tested separately: more aggregate memory can make a model runnable without making
it faster or more energy efficient.

## Actual project layers

| Layer | Confirmed implementation | Boundary |
| --- | --- | --- |
| `v2` | Bounded factorization strategies, cached knowledge, inheritance, signing/audit commitments, authenticated encrypted snapshots, ternary packing | Core prototype; not an LLM runtime or distributed executor |
| `window/src/reorganization` | Limited procedure composition, validation, reopening, memory-based reconstruction | Arithmetic experiment; conventional composition was cheaper |
| `window/src/neural` and `neural_worker` | Identified resident DeepSeek inference, memory/relation experiments, real token accounting | Fixed pretrained weights; adaptive routing did not beat indexed retrieval |
| `window/src/network` | Concurrent full-model workers, task dependency waves, local/SSH connectors, source recognition and acceptance | Local concurrency measured; remote execution untested; no weight sharding |
| `Deepthron` | Model adapters and orchestration attempts | Inspected legacy sharding still uses random noise/tokens; advertised model substitution remains |
| `Genesis-Lib` / `Genesis-Protocol` | Historical lifecycle, identity, memory, simulation and application structures | Selective reuse candidates; not a validated integrated runtime |

Architectural intent is that `v2` is the core and `window` is the laboratory.
Currently important reusable network and DNA mechanisms remain implemented in
the laboratory. They do not yet inherit v2's encrypted persistence, signed lineage,
or lifecycle automatically. Porting these mechanisms behind core interfaces is
needed before claiming one unified Dethron runtime.

## Value claims and evidence

**Energy savings:** unmeasured. No experiment here integrates physical power over
time across all participating devices. Division counts, token counts, byte counts,
and shorter runtime are useful diagnostics, not joules. The legacy energy manager
sets efficiency from a consciousness score; this is simulation state.

The v2 smoke test saved 2,199 net divisions against its initial strategy, but
evolution time exceeded task time saved. Its ternary payload was 20% smaller than
two-bit packing, while encoding/decoding took longer. The follow-up best-fixed
strategy comparison and arithmetic composition control remove the apparent
general advantage. These results motivate cost-aware selection rather than a
claim that evolution or ternary representation inherently saves energy.

**Concurrent tasks:** demonstrated locally. Two complete CPU model replicas
achieved approximately 1.71–1.76 times the direct-request throughput of serial
execution. This is a worker-pool result. Parallel cooperative waves were faster
than serial waves but slower than direct pooling and did not improve accuracy.

**One huge model on several modest machines:** not implemented. Each new worker
loads a complete checkpoint. The old Deepthron shard path splits text, applies
random operations, and joins text; it does not transmit transformer hidden states
through actual partitioned weights. A proper implementation must handle embeddings,
all layers, output head, positions, attention state/KV cache, and generation steps.
Correctness must match an unsplit reference within a declared numerical tolerance.

“Any machine” should mean an eligible client can access collectively hosted
inference. A participating compute worker still needs enough RAM for its partition,
activations, cache, runtime, and communication buffers. For illustration, 70 billion
weights at four bits require about 35 GB just for weights, before overhead. A
network can distribute that storage requirement; it does not eliminate it.

**Evidence accuracy:** encouraging narrow result. On the same 40 synthetic cases,
raw instructions scored 5, examples scored 23, and examples plus recognized current
evidence scored 35. The last mode answered all 20 supported cases correctly;
five unsupported guesses were rejected. Zero wrong substantive answers were
accepted in this test. Deterministic relation lookup solved all 40, so neural
superiority over retrieval has not been shown.

**Connected context:** eight cases retrieved two relevant facts from 130 stored
sources each; all eight answers passed. A protected parent/child wave passed.
This demonstrates bounded retrieval and evidence propagation, not a larger native
model context window, semantic reconstruction from arbitrary documents, or learned
cross-machine memory. DNA source IDs are not cryptographic attestations of truth.

**Adaptation:** mechanisms exist in separate experiments; a net advantage beyond
competent fixed/retrieval/composition controls has not been established. The current
network graph is explicitly supplied. It does not learn its own connections.

## Relation to the broader BitNet idea

The scientific synthesis describes selective specialists, reusable paths,
multiple memory timescales, migration, opportunistic device participation, and
context-sensitive validation. Those remain coherent research goals. Communication
waves can carry task state over ordinary links; all execution still needs physical
hardware, energy, accessible state, and a reliability protocol.

Distinguish our project name from Microsoft's BitNet/bitnet.cpp. The latter
provides optimized inference for compatible low-bit models and reports energy
benefits in its own benchmarks. Our v2 base-3 payload encoding is not that kernel
implementation, and our active DeepSeek worker uses BF16 on GPU or FP32 on CPU.
Those external savings cannot be claimed as Dethron results.
[Official BitNet project](https://github.com/microsoft/BitNet).

Collaboratively serving actual model partitions is feasible in existing systems:
Petals explicitly loads a part locally and uses peers for other parts. This makes
it a relevant reference/baseline, rather than evidence that our implementation has
already achieved the same capability.
[Official Petals project](https://github.com/bigscience-workshop/petals).

## Recommended sequence

1. **Define the core contract.** Consolidate proven task, evidence, validation,
   worker and lifecycle interfaces in v2, keeping workloads and reports in window.
   Separate worker identity, model identity, source identity and learned capability.
   Preserve existing behavior and avoid importing historical fallback paths.
2. **Measure energy before expanding node count.** Compare direct inference,
   retrieval plus inference, verified reuse, and selectively invoked specialists
   on fixed independently authored tasks. Report correctness and coverage beside
   total joules per correct substantive result. Include failed attempts, validation,
   startup amortization, idle operation, and all workers. Compare sustained load
   and intermittent use; keeping otherwise sleeping devices awake has a cost.
3. **Add a compatible efficient backend as a separate experiment.** Keep the
   checkpoint/runtime explicit. Compare kernel performance using the same model
   when possible; otherwise label it a quality-constrained system comparison.
   Quantization, request scheduling, and DNA retrieval are separate interventions.
4. **Prove model sharding locally.** Partition one identified small real model into
   two processes with each loading only its portion. Test logits, greedy tokens,
   cache behavior, parameter coverage, peak memory and corrupted/late handoffs.
   Splitting prompts or running independent experts does not satisfy this gate.
5. **Prove capacity across two physical machines.** Run under explicit per-node
   memory limits, then demonstrate a model that cannot fit the designated single
   node but can execute across the pair. Measure latency, bytes, failures and
   aggregate energy. Compare with conventional offload/model-parallel software.
6. **Only then optimize adaptive placement.** Reward useful answers within energy,
   memory and latency budgets. Compare with a competent ordinary scheduler and
   include learning/validation overhead. Growth must coexist with consolidation,
   eviction and bounded connectivity.

NVML can report GPU energy in millijoules on supported devices. That is GPU-only
telemetry, not whole-machine consumption; unsupported counters must be reported
as unavailable. Whole-system claims need a defensible host/network measurement
boundary, ideally external power measurements for each participating machine.
[NVIDIA NVML documentation](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceQueries.html).

## Documents and source evidence reviewed

- [v2 README](../v2/README.md), `src/{tron,evolution,trit,crypto,lib}.rs`.
- [Root architecture](../BITNET_ECOSYSTEM_ARCHITECTURE.md), implementation guide,
  templates/use cases, and [distributed roadmap](../DEEPSEEK_DISTRIBUTED_INFERENCE_ROADMAP.md).
- [Scientific synthesis](../dethron_genesis_sintese_cientifica.md), especially
  opportunistic nodes, memory reconstruction, and energy feasibility.
- [Original audit](../PROJECT_FEASIBILITY_REPORT.md) and
  [probe gates](../PROBE_VALIDATION_PLAN.md). The audit predates our real-worker
  work and Git tracking; its negative legacy findings are not a current verdict
  on the new harness. Model-sharding gates P2/P3/P5 remain outstanding.
- [Deepthron README](../Deepthron/README.md),
  `src/gpt_oss_final_working.py:49,62`, `trons/shard_worker.py:195–219`,
  `trons/shard_manager.py:28,282,344`: rechecked legacy claims against source.
- `Genesis-Lib/genesis_lib/energy/energy_manager.py:36–39` and
  `Genesis-Protocol/src/neural.rs:364`: simulated accounting/transport.
- [Reuse review](REPOSITORY_REUSE.md), [feasibility](FEASIBILITY.md),
  [reorganization](REORGANIZATION.md), [network](NETWORK.md), and
  [accuracy](ACCURACY.md), including the latest accuracy JSON report.

No new performance/energy tests were run for this review. The defensible current
description is an early, measurable prototype for evidence-aware execution, with
energy-efficient operation and pooled model capacity as explicit unproved goals.
