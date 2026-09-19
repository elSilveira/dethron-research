# Dethron — decision, test and implementation plan

Consolidated into the [master plan](DETHRON_MASTER_PLAN.md), which details the architecture
and extends this sequence with processing (G8) and incentives (G9).

Document version: 4, 16/09/2026. G0 executed within the whole-message scope:
[configuration, controls and the decision to integrate](window/G0_REFERENCE.md).
G1 was validated as a [laboratory integration](window/G1_INTEGRATION.md).
G2 is closed: [exact parts and the widened paired comparison](window/G2_PARTS.md).
G3 executed [two generations of nodes and four supervisors](window/G3_GENERATIONS.md).
G4 delivered [without the IP stack, with cut controls](window/G4_INDEPENDENCE.md).
Version 7 of the master plan reframes the focus towards an evidence harness and verifiable
delivery, with the V1–V3 trail; G5 and G7 are deferred, G8 and G9 come after outside
acceptance. V1 is executed in both halves:
[custody, proof of entry and pendency](window/V1_CUSTODY.md) and
[a receipt returning without direct contact](window/V1_RECEIPT_RETURN.md).
V2 is [approved on an independent machine](window/V2_REPRODUCTION.md): a complete pass in 58
minutes, eight paths with the declared verdict. V3 began with the schedule contract and the
local agent. See the [master plan](DETHRON_MASTER_PLAN.md). The vision is in the
[direction](DETHRON_NETWORK_DIRECTION.md) and the autonomy guarantees in the
[contract](DETHRON_AUTONOMY_CONTRACT.md).

## Order of decision

1. Validate a requirement and an existing reference.
2. Demonstrate a measurable gap.
3. Implement only the mechanism that attempts to close the gap.
4. Re-assess against the same reference, every cost included.
5. Continue, integrate the reference, reduce the scope or abandon the hypothesis.

Do not make "finishing a global network" a prerequisite for deciding whether value exists.
The LLM studies remain secondary and do not block the network's validation.

## Before the first new execution

Create a versioned configuration holding:

- The intended use and participant; the service requested and the tolerated deadline.
- The identities, devices, resources, transport and failure domain of each node.
- The original messages, sizes, hashes and recipients; the evaluator's source must not be
  reachable by the system during recovery.
- The topology and the calendar of contacts, failures, expiry and queue budget.
- The policy for replicas and encoding, retention, repair and identity recovery.
- The permitted external dependencies: key, root, bootstrap, time and controller.
- The reference's versions and configuration, plus development and held-out scenarios.
- The metrics, targets, repetitions and stopping criterion, defined before seeing results.

There is no held-out configuration ready at this stage. Candidate initial values: short
messages and small files in separate classes, several contact orders and multiple seeds. Fix
the numbers according to the hardware and service chosen; do not claim statistical
sufficiency from an arbitrary number of repetitions.

## Milestones and controls

| Milestone | Execution | Approval | The control that must fail |
| --- | --- | --- | --- |
| G0 — reference | Reticulum/LXMF, or an adequate identified BPv7 implementation | The service works, or the gap is reproduced and attributed | With no recipient, no valid final confirmation |
| G1 — envelope and mailbox | Persist the message and fragments, restart the receiver | Bytes and identity preserved; one logical delivery | Altering payload, version or id must not pass |
| G2 — complements | Three individually incomplete paths, separate contacts | A sufficient union reconstructs the exact bytes | Duplicates do not replace parts; an insufficient union stays pending |
| G3 — generations | Replace every original and the supervisor in cycles | State and pending messages continue with no hidden source | Withdrawing a resource declared indispensable produces an explicit failure |
| G4 — external path | Cut the internet, including before startup | The service in scope uses alternative physical paths | Cutting every bridge as well prevents delivery, preserving pendency |
| G5 — survivors | Test 5 % chosen, random, correlated and targeted | A score separated by failure model and survival level | Isolated survivors must not be reported as global connectivity |
| G6 — hardware | Repeat on distinct devices and at least two real media | Evidence of the interfaces and the transmission, with no hidden external tunnel | A medium switched off stops carrying data |
| G7 — cost | The same load and guarantees with and without the Dethron difference | A reproducible net benefit; the uncertainty declared | Metadata, repair and idleness do not vanish from the accounting |

G0 comes before widening any code of our own. G1–G5 may begin in a local laboratory, but
must be labelled as an emulation of contacts and processes. G6 is necessary in order to
claim diversity of physical media. Using TCP on two ports is not proof of two radios or of
two independent failure domains.

For G5, measure simultaneous and gradual losses separately. In the gradual scenario, record
the repair window and the capacity available to restore the nodes. Report the loss of
capacity and of latency, even where the recovery is correct.

## Small implementations, conditional on G0's gap

The names below are proposals; the files and test commands do not exist yet. If the
reference already meets the requirement, create adapters and tests over it, rather than
implementing the same protocol again in v2.

| Slice | Proposed files | First behavioural test |
| --- | --- | --- |
| A verifiable message | `v2/src/network/message_envelope.rs`, `v2/tests/message_envelope.rs` | Tampered content or version is rejected |
| Persistent progress | `v2/src/network/message_inbox.rs`, `v2/tests/message_inbox.rs` | A restart loses no parts and causes no second logical delivery |
| Complements | `v2/src/network/fragment_inventory.rs`, `v2/tests/fragment_inventory.rs` | The inventory asks for absent information and ignores duplicates |
| Contacts and forwarding | `v2/src/network/contact_transport.rs`, `v2/tests/contact_transport.rs` | A message crosses non-simultaneous contacts, within the limits |
| External experiment | `window/run_gateway_probe.py`, `window/gateway_audit.py`, `window/tests/test_gateway_audit.py` | A record without final reception is rejected by the auditor |

After creating the minimal interface and the test, run, from `v2`,
`cargo test --locked --offline --test message_envelope` (or the slice's name). Require the
failure to come from incorrect behaviour, not merely from a missing file or import.
Implement the minimum, repeat the test, run the relevant suite and only then refactor. For
the auditor: from the repository root, set `PYTHONPATH=window` and run
`python -m pytest window/tests/test_gateway_audit.py -q` once the file exists.

Keep every code and test file under 200 lines. Preserve the execution of the existing
experiments. Do not reuse the historical gateways' simulated authentication as a security
implementation; use established primitives. Select the encoding scheme and the dependencies
after the comparison, without inventing cryptography or declaring RaptorQ implemented on the
strength of a reference.

## Minimum evidence per execution

- The configuration and a manifest with hashes of code, dependencies and binary.
- Clocks and the sequence of events; real pids/devices, sessions and interfaces.
- Messages sent, parts received, inventories, repairs and the final confirmation.
- The surviving dependencies and who supplied them, the supervisor and identity included.
- Partial records preserved on failure; status started, incomplete, completed or failed. An
  exceeded deadline and an error never become a correct delivery.
- An auditor independent of the sender's success counters: check the bytes, the recipient's
  identity, the cause of pendency and the coherence of each scenario.
- Hashes give traceability; on their own they do not authenticate a remote execution.

Count every original message: delivered on time, late, pending, expired, rejected as
corrupt, and undue deliveries. Show eligibility separately, without quietly removing the
hard cases from the denominator.

## Usefulness and cost metrics

Measure the rate of intact delivery within the deadline, delay, useful bytes, total traffic,
physical bytes persisted, RAM and electrical energy. Include discovery, confirmations,
encryption, encoding, retransmissions, repairs and attributable idleness. Do not treat
aggregate throughput as the speed of a single task.

Compare modes in paired runs, with balanced orders. Vary failures and contacts; identical
repetitions do not create independent scenarios. Document contamination from warm-up, shared
hardware and other loads.

The goals of 5 % saved in bytes and 5 % saved in joules are separate from survival with 5 %
of the nodes. To claim the gain, the measurement's uncertainty must allow it to be told
apart from noise, under equivalent service quality and recovery. Without an adequate meter,
the energy result stays **unmeasured**.

## Decision after each milestone

| Result | Action |
| --- | --- |
| The reference already meets the need with no useful gap | Integrate or contribute; stop any equivalent reimplementation |
| A reproducible correctness failure | Fix the slice or withdraw the mechanism; do not increase scale |
| Correct reconstruction, but insufficient contacts | Revisit deployment and use; do not promise universal delivery |
| A mechanism of our own wins on held-out scenarios at an acceptable cost | A bounded pilot and a new assessment |
| It only wins with chosen survivors or with an omitted cost | Reject the general claim and record the restricted scope |
| There is neither an advantage nor demand for integration | Abandon the hypothesis or product in that scope and archive the evidence |

Absolute immortality, the survival of any network with any 5 %, and automatic disconnection
by mere size must be abandoned as guarantees. That decision does not require abandoning
resilient networks with conditional contracts.

## Resumption point

The user's economic observation is in [incentives](DETHRON_INCENTIVES.md). Investigate
demand, costs and remuneration alongside G0's requirements; do not use token issuance as a
substitute for validating the network. Test receipts and accounting may accompany the
experiments. A tradable token, real payments and a consensus of our own are neither
implemented nor authorised by this plan.

Read the [index](README.md), [usefulness](DETHRON_UTILITY_VALIDATION.md) and the
[autonomy contract](DETHRON_AUTONOMY_CONTRACT.md). G0–G3 were executed after the initial
consolidation. Resume at G4, the cut of the external path, before widening autonomy or
scale; the current state is in [G2](window/G2_PARTS.md) and [G3](window/G3_GENERATIONS.md).
