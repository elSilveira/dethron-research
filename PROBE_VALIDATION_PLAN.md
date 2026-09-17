# BitNet / Genesis / Deepthron probe validation plan

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](README.md) - [Plano de decisão](DETHRON_VALIDATION_PLAN.md) - [Evidências](DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Date: 2026-09-13. Based on [the project audit](PROJECT_FEASIBILITY_REPORT.md).

## What we are trying to validate

Working assumption: the first product hypothesis is **one identified language model can execute correctly across workers, and adaptive coordination can provide a measurable benefit**. Storage and security are separate hypotheses. A successful distributed demo proves neither biological intelligence nor consciousness.

We will answer three different questions: (1) does the mechanism work, (2) is it useful under a stated resource constraint, and (3) does the project's adaptive approach improve on conventional engineering? Keep the results separate. Existing failures are evidence about this implementation, not disproof of distributed computing.

No production rewrite is part of this planning step. Planned commands below refer to files that do not exist yet. Hardware discovery is completed; new model, transport and adaptation probes have not run.

Revision 2026-09-14: prioritize independently verified task correctness and consistency under changed inputs and equivalent phrasing. See [the capability validation contract](CAPABILITY_VALIDATION_CONTRACT.md). Exact wording is not a product success criterion. Numerical comparisons remain diagnostic gates for the specific claim that a model was partitioned without changing its computation.

## Capability correctness and implementation fidelity

Record two separate outcomes: **capability correctness** (the answer satisfies the task) and **implementation fidelity** (the declared computation actually ran). A fluent or plausible answer alone passes neither. Different wording can pass capability correctness; matching a stored answer cannot establish execution or generalization.

For arithmetic, verify results using an independent oracle and fresh operand combinations; test changed operands, composition and inverse relations. For language, judge preserved propositions, including entities, roles, negation, quantities and temporal context. Accept “the sky is dark” and “dark is the sky” in the same context. Reject “the sky is not dark”; do not treat matching keywords as matching meaning. Unknown or ambiguous equivalence is INCONCLUSIVE pending review.

Run the capability track against an identified single-worker baseline before assessing distributed quality. Exact-model partitioning still follows P1–P3 below. If an approximate or alternative computation is proposed, declare a separate experiment before running it: record actual model/computation identity, task quality floors and acceptable degradation, then compare quality, resource use and reliability against the baseline. It may establish useful task performance without establishing equivalent model execution.

Report capability correctness, paraphrase consistency, changed-input sensitivity and completion coverage separately. Agreement is useful only when answers are also correct. Include constant-answer, echo, answer-replay and role/negation-insensitive controls. No aggregate score may hide a failed hard constraint or missing worker execution.

## Starting environment and practical limits

- Confirmed locally: Windows, 16 logical CPU threads, 63.9 GiB RAM, NVIDIA RTX 4060 Ti with 8,188 MiB VRAM, driver 595.97.
- Default Python: 3.10.11; pytest and cryptography available; Torch, Transformers and psutil absent. Windows CIM discovery was denied; read-only NVIDIA and OS memory queries supplied the figures above.
- Begin in an isolated probe environment with CPU FP32 correctness checks and a small pretrained model. Choose and pin the actual checkpoint only after confirming architecture support, license and download size. A roughly 100–500M parameter model is a planning range, not a required identity or performance claim.
- A tiny seeded transformer fixture can test transport mathematics offline, but cannot establish useful language generation. The pretrained checkpoint is a separate mandatory gate.
- Two processes on this computer can establish process isolation and tensor handoff. They cannot establish multi-machine performance or two-GPU speedup. Only one GPU was identified; no second machine is assumed available.
- Larger GPT-OSS/DeepSeek models come after correctness. Do not silently substitute a smaller checkpoint and preserve the larger model's name.

## Experiment rules

Every run records a run ID, code hashes, environment versions, model/tokenizer revisions, weight hashes, hardware, dtype, seeds, prompt-set hash, partition map, sampling settings, concurrency, cache mode, timestamps and result status. Hash checkpoints outside timed inference.

Use four statuses: PASS, FAIL, BLOCKED and INCONCLUSIVE. Missing dependencies or hardware are BLOCKED, never PASS. A crashed worker or absent result is never replaced by mock output. Keep timeouts and failures in benchmark accounting.

For each implementation slice, first add a behavior test, run it and observe the intended assertion failure, then make the smallest change and rerun. Import/setup errors do not count as the intended failing test. Keep new source/test files below 200 lines and avoid editing the archived application to make a probe look successful.

Store raw events as JSONL and summaries as JSON/Markdown under `probes/results/<run-id>/`. All downloads, generated checkpoints and environments must have explicit locations and size accounting. Timed runs must not download anything.

## Probe sequence and decision gates

| ID | Hypothesis and experiment | Pass gate | What failure means |
|---|---|---|---|
| P0 | Evidence can detect a lie: feed deliberately incorrect model metadata, missing measurements and synthetic output to the evidence validator | Validator rejects each case; complete real metadata passes | Measurement harness is not trustworthy yet |
| P1 | A pinned real model works locally: run fixed prompts, teacher-forced logits and greedy decoding with cache on/off | Correct checkpoint/tokenizer identity; finite logits; reproducible reference; cache paths agree within declared tolerance | Repair the baseline before distribution |
| P2 | The same model can be split without changing computation: invoke two stage modules in one process | Correct partition coverage, no missing parameters, allowed tied weights documented; logits and generated tokens match the reference fixture | Partition implementation is wrong |
| P3 | Workers genuinely cooperate: move the P2 stages into two separate processes and transmit hidden states | Same numerical gate; distinct process IDs; each worker loads only its declared partition; complete trace of tensor handoff | Local execution is not yet distributed correctly |
| P4 | Distribution survives adverse conditions: corrupt messages, wrong revisions, duplicate requests, worker termination and stalls | Explicit failure by deadline or a bounded retry with one final result; no silent corruption or false success | Reliability contract is incomplete |
| P5 | Cross-machine execution is feasible on the intended link: place workers on two hosts | P3/P4 gates hold; actual bytes, bandwidth, round-trip time and per-stage timings recorded | Network/runtime constraints need redesign; no speed claim |
| P6 | Distribution solves a useful resource/performance problem: compare against the same model on one worker | Meets one preregistered capacity, latency, throughput or energy objective without reduced correctness | Mechanism may work, but its product value is unproven |
| P7 | Adaptive coordination adds value: compare ordinary scheduling, fixed heuristics and evolutionary scheduling | Repeatable held-out improvement beyond a declared practical threshold, including adaptation overhead | Reject or narrow the adaptive-performance claim |

Stop at a failed prerequisite. Do not move to a bigger model, add UI polish or publish speedups while its correctness gate is failing.

### P0: turn the audit into executable negative controls

Use temporary/in-memory fixtures to capture current failures: advertised identity versus loaded identity; ciphertext bit tampering; decrypting old data after rotation; actual stored byte size; retrieving by a returned key; and a send operation with no receiver. Validate functional behavior rather than searching for suspicious strings in source.

These should initially FAIL the advertised contracts for the audited paths. Record those failures in a dedicated characterization run, separate from the new probe harness's green regression suite. Do not install or load a large model merely to rediscover the DialoGPT name mismatch; use the adapter's reported configuration and an instrumented loader for that specific contract, then require actual checkpoint evidence at P1.

Add harness controls: a deliberately altered output tensor must fail comparison; a worker replaced by an echo/random-output stub must fail equivalence; a stopped destination must fail delivery. These controls show that a later green result is capable of distinguishing correct computation from a demonstration.

### P1–P3: model correctness before speed

Freeze 20 prompts spanning short/long inputs, repeated tokens, Unicode, empty input under the tokenizer's documented policy, and batch sizes 1 and 2 with different lengths. Generate up to 32 new tokens per prompt, with a fixed EOS policy. Define a separate small smoke subset for development.

Start on the same CPU/runtime in FP32, evaluation mode, with sampling and dropout disabled. Proposed initial comparator: `abs(candidate-reference) <= 1e-5 + 1e-4*abs(reference)`, applied to intermediate states and teacher-forced logits, with shape/dtype/finite-value checks. Also require identical greedy token IDs on the frozen same-environment fixture.

Confirm repeated unsplit runs satisfy the chosen comparator before testing shards. If they do not, first investigate nondeterminism. Do not widen tolerance after seeing shard failures merely to pass. Across devices or reduced precision, define a separate tolerance experiment and report top-logit margins/token divergence explicitly; mathematical equivalence does not guarantee bitwise identity. See [PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html) and [reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html).

Compare full-sequence prefill and each subsequent decode step. Test cache enabled versus disabled and ensure request caches never mix. A first-token match is insufficient.

The partition is: tokenization -> embeddings -> earlier transformer blocks -> hidden-state transport -> later blocks -> final normalization/output projection -> sampling. Preserve masks, positions, residuals and per-layer KV state. Prompt chunks and concatenated text outputs are not this computation.

P3 records worker model manifests and loaded parameter ownership, not only process names. Stop worker B and verify A cannot return a successful complete generation through a hidden local fallback. Alter one B-owned tensor in a disposable test fixture and verify the comparator detects changed output. Pass this control without modifying downloaded checkpoint files.

For network payloads use explicit tensor schemas with dtype, shape, length, request/step IDs and bounded buffers. Reject malformed or oversized input; avoid executable object deserialization. Evaluate an established distributed backend for the eventual runtime rather than claiming a novel transport. [PyTorch distributed communication](https://docs.pytorch.org/docs/stable/distributed) supplies relevant primitives; backend/Windows compatibility must be checked in the selected pinned environment.

### P4–P6: reliability and useful performance

Inject termination during prefill and decoding, a stalled worker, altered payload bytes, stale/out-of-order steps, a mismatched checkpoint, duplicate completion and coordinator restart. For small local fixtures propose a configurable 10-second request deadline and at most one retry; accept only explicit failure or one valid result before the deadline. Track duplicate computation separately from duplicate externally delivered results. Define restart semantics before testing them.

Benchmark identical checkpoint, precision, prompt/output lengths, batching, thread allocation and quality requirements. Use warm-up followed by at least 30 measured requests per condition for an initial screen, with alternating/randomized condition order over three sessions. Report cold load separately. Use a larger confirmation run before relying on p95; 30 observations do not characterize a reliable tail.

Record time to first token, end-to-end latency, decode tokens/sec, aggregate throughput, peak per-worker/aggregate memory, CPU/GPU utilization, bytes sent, communication time, failures and retries. Use monotonic coordinator timings; do not subtract timestamps from unsynchronized remote clocks. Synchronize asynchronous GPU work at measurement boundaries where needed.

Choose the primary objective before the run: (a) run under a declared per-worker memory cap where the unsplit model does not fit, (b) at least 10% throughput improvement at fixed latency/error limits, or (c) at least 10% latency reduction at fixed workload. These are proposed engineering decision thresholds, not known benefits. A memory-cap experiment on one host must be labeled artificial, not presented as evidence of physical multi-host capacity.

Include a conventional model-parallel implementation as a comparator before attributing benefits to BitNet. Compare replicated request routing separately; it solves a different problem. A faster run that changes the model or outputs fewer tokens is invalid evidence.

Energy is a separate optional objective: joules per completed equivalent request over sustained runs, including every worker. NVIDIA telemetry is GPU-only, not whole-machine energy; CPU/network/host consumption needs additional measurement. If it is unavailable, report energy as BLOCKED or estimated, not measured savings. Never infer watts from a consciousness score.

### P7: the distinctive idea needs an ablation experiment

Use identical execution and transport with only scheduler behavior changed: A = standard static partition/routing; B = deterministic load-aware heuristic; C = the proposed evolutionary/TRON policy. Include a frozen version of C to test whether online adaptation itself helps. An extra useful control shuffles fitness feedback; improvement should not survive unchanged if meaningful feedback drives it.

Define “fitness” using externally measured goodput, deadline misses and resource use, not the agent's self-reported consciousness. Bound the policy's actions to scheduling/resource choices. It cannot change model identity, skip required computation or relax answer checks.

Tune on one workload set and evaluate on an untouched set with changing input lengths, burstiness and slow workers. Start with at least 10 independent workload/policy seeds and paired runs per condition. Include warm-up, monitoring, exploration, repartitioning and migration costs. Use confidence intervals over independent runs, not correlated tokens from the same request.

Proposed go/no-go: at least 10% held-out improvement over the strongest conventional baseline on the preregistered primary metric, a paired 95% confidence interval excluding no benefit, and no regression beyond declared correctness/error/resource limits. This sample count is a starting point; wide intervals mean INCONCLUSIVE and require more runs. If C only beats a deliberately poor baseline, it has not established value.

## Independent storage and security track

Run S1 alongside P0–P3 if storage is a product goal. Test empty, text, already-compressed and random byte payloads from 0 bytes through 10 MiB, plus chunk-boundary cases. Assert byte-exact recovery, stable receipt-key retrieval, correct actual byte accounting, durable manifests and recovery in a fresh process. Report raw/encoded/metadata/replication bytes separately; random input need not compress.

Run S2 with three worker processes and declared replication factor 2. Acknowledge a write only after the required durable copies exist. Stop one holder, retrieve verified bytes from the other, restart and repair replication. Test interrupted writes, corrupt replicas and loss beyond the promised redundancy. Same-host workers do not protect against losing that host.

Run S3 against the exact storage encryption adapter: wrong key, altered ciphertext, altered nonce, altered associated data and truncated tag must fail closed. Old records must remain recoverable across rotation using explicit key versions; incorrect versions must fail. Add real known-answer comparisons, replay controls at the protocol layer, and controlled-clock rollback/restart cases for nonce management. Passing these probes is a prerequisite, not a security certification.

Do not test literal consciousness with self-reports, rising scores or fluent text. Test useful capabilities such as resource adaptation and transfer to unseen tasks. Physical quantum effects and quantum security would need distinct scientific mechanisms and expert evidence; none of these software probes validates them.

## Planned small implementation slices

All paths below are proposed. `probes/tests/` tests the new harness; current-code contract failures live in `probes/characterization/`. Add test fixtures/adapters before each red run so that the expected failure is behavioral, not simply a missing import. Split any source/test file before 200 lines.

| Slice | Files to create | First targeted command and intended red result |
|---|---|---|
| Evidence contract | `probes/evidence.py`, `probes/tests/test_evidence.py`, `probes/README.md` | `python -m pytest probes/tests/test_evidence.py -q`: accepts a wrong checkpoint or missing timing; reject it to turn green |
| Current-code characterization | `probes/characterization/test_identity.py`, `test_storage_contract.py`, `test_crypto_contract.py`, `test_delivery_contract.py` | `python -m pytest probes/characterization -q`: the named advertised contracts fail; preserve results without redefining success |
| Real reference | `probes/model/reference.py`, `probes/model/manifest.py`, `probes/tests/test_reference.py`, `probes/fixtures/prompts.json` | `python -m pytest probes/tests/test_reference.py -q`: incorrect identity, nondeterministic reference or cache mismatch; repair before proceeding |
| Stage computation | `probes/model/stages.py`, `probes/model/compare.py`, `probes/tests/test_stages.py` | `python -m pytest probes/tests/test_stages.py -q`: omitted stage/tensor breaks logits and tokens; implement complete partition |
| Process handoff | `probes/runtime/worker.py`, `probes/runtime/coordinator.py`, `probes/runtime/tensor_wire.py`, `probes/tests/test_workers.py` | `python -m pytest probes/tests/test_workers.py -q`: no valid receiver computation or missing tensor handoff; implement actual transfer |
| Failure semantics | `probes/runtime/deadlines.py`, `probes/runtime/request_state.py`, `probes/tests/test_faults.py` | `python -m pytest probes/tests/test_faults.py -q`: stopped worker hangs or yields false success; implement bounded failure/retry |
| Measurement | `probes/benchmark/run.py`, `probes/benchmark/summary.py`, `probes/tests/test_measurement.py` | `python -m pytest probes/tests/test_measurement.py -q`: failed requests disappear or words count as tokens; correct accounting |
| Storage/security | `probes/storage/adapter.py`, `probes/tests/test_storage_bytes.py`, `test_storage_recovery.py`, `test_storage_auth.py` | Run these files individually: receipt/restart/corruption/rotation assertions fail against the current adapter; replacement work is a separate slice |
| Adaptation | `probes/policies/static.py`, `load_aware.py`, `evolutionary.py`, `probes/tests/test_policy_contract.py`, `probes/benchmark/ablation.py` | `python -m pytest probes/tests/test_policy_contract.py -q`: policy can exceed resource/compute constraints; enforce invariants before benchmarking benefit |

After each slice, run its targeted tests and `python -m pytest probes/tests -q`; do not include intentionally failing characterization tests in that green-suite command. Harness tests passing does not imply benchmark hypotheses passed. Preserve negative and inconclusive experimental results.

## First execution batch

1. Freeze this hypothesis list and the capability contract, select the first priority and record available second-host hardware when it exists. Begin with P0 and an independently scored single-worker capability baseline; retain P1–P3 for the exact distributed-model claim.
2. Build P0 evidence validation and current-code characterization with existing lightweight dependencies. Deliver a machine-readable ledger of reproduced failures and negative controls.
3. Establish a pinned isolated environment and a documented small checkpoint selection. Implement P1; save a reusable reference fixture and measured single-process baseline.
4. Implement P2, then P3, testing first. Deliver one request traced across two actual worker processes with equivalent logits/tokens and a worker-stop negative control.
5. Review the evidence. If correctness holds, obtain/use a second host for P5 and only then test cross-machine usefulness. If it fails, fix the smallest failing boundary; do not scale the model.

The first meaningful milestone is **one honest, reproducible two-worker inference run that fails correctly when a worker is absent**. The subsequent milestone is evidence that the adaptive approach adds value over ordinary distributed inference. Those are distinct achievements.
