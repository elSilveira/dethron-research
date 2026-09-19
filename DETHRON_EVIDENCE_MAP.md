# Map of evidence, prior art and documentation

> **Note, 19/09/2026.** This document cites work that predates Dethron — BitNet/Genesis
> probes, Rust crates, a neural worker, a browser dashboard — which left the tree when the
> repository was prepared for publication. The links to that material have been undone and
> the text kept. The content remains in the git history. Links to paths outside the
> reproducible tree (`backup/`, `bkp-dethron/`, `Genesis-Protocol/`, `results/`) were undone
> for the same reason: they resolved only on the author's machine and would break in a clone.

Consolidated: 15/09/2026. It exists so that work can resume without confusing plans with
results. Main entry point: [README](README.md). Current plan: [G0–G7](DETHRON_VALIDATION_PLAN.md).

## The verifiable state in the material examined

| Area | Evidence recorded | Limit |
| --- | --- | --- |
| v2 recovery | Encrypted units, hashes, references, recipes, and failure on a missing dependency | It does not reconstruct lost information from a hash |
| In-memory regeneration | 20/20 runs, 100 stores, five survivors | Objects in the process, complete replication; they are not machines |
| Local survival | 3/3 proofs, 20 processes, restoration from one survivor | Same computer, with controller, root and key available |
| Answer comparison | 32 generations: full 4/8, lexical 3/8, paragraphs 5/8, sentences 2/8 | Annotated development; it proves neither a swarm nor automatic extraction |
| The comparison's Python tests | 124 tests passed, 11 of them new | Local tests, run before this documentary consolidation |
| Historical gateway | The intent recorded and some servers and adapters | Discovery, sending and authentication simulated on the paths examined |
| G0 with a real reference | Reticulum 1.5.4/LXMF 1.1.1: three messages from 1 KiB to 1 MiB received after the propagation nodes crashed and the origin left; the negative retained | TCP on the same host, whole messages, provisioned contacts; it proves neither fragments nor radio |
| G1 integrated | A 64 KiB message, an atomic mailbox and receipt, the recipient's signature, crashes, a duplicate and the negatives; the audit passed | Local direct delivery; composing the receipt with offline propagation, radio and production are not yet validated |
| G2, first slice | 96 KiB reconstructed from three parts after the origin left and the propagation nodes crashed; a missing part prevents completion | The native 64 kB per-fetch limit, one host, provisioned placement; no redundant encoding and no total cost |
| G2, widened comparison | 12 paired cases: without loss, exact parts spend less traffic; with one route lost, only XOR parity completes | Two repetitions, one host, loss induced by omitting a contact; storage grows opposite to traffic |
| G3, generations | Two complete carrier replacements and four distinct supervisors; 24 KiB delivered exactly with a receipt; withdrawing the declared credential refuses the service | Same host and processes; blocking the retired generations is a Python hook, not operating-system isolation |
| G4, logical independence | 16 KiB delivered with no IP interface at all, zero endpoints across six processes; the IP baseline shows three endpoints; a removed medium does not deliver and preserves pendency | Independence from the IP stack, not physical; a file bridge on the same host, with no real loss, latency or range; a netstat sample, not packet capture |
| V1, custody | Three relays attest by signature to what they hold; the auditor derives pendency, names the relay that attested and discarded, and checks the explicit refusal for an id never submitted | Custody is the relay's claim, proving entry and not exit; one host, one round per scenario |
| V1, receipt return | A 395-byte receipt replicated at three relays; the origin comes back as a new process and obtains the proof from a single relay; the relay that discarded its copy shows as proof absent and another relay resolves it; without completion, no proof appears | Sessions disjoint by tenths of a second, not long offline periods; cooperative relays; copy retention not measured; the propagation mechanism is LXMF's |
| Radio and independence from the internet | A plan and external prior art | No new Dethron proof on hardware |
| Universal survival with 5 % | No sufficient evidence | A percentage alone guarantees neither data nor contacts |
| Global energy and storage | Targets | No measurement of a net 5 % saving |

## Current decision documentation

- [V1, second half](window/V1_RECEIPT_RETURN.md): the receipt published in sequence by the
  relays, an origin that comes back and checks against persisted recipients, an auditor with
  session disjunction and the route of the proof.

- [V1, first half](window/V1_CUSTODY.md): the custody envelopes, LXMF facts confirmed in the
  source, an auditor separating entry, exit and pendency, and the scenario that lied and was
  refused by the auditor.

- [G4 executed](window/G4_INDEPENDENCE.md): the external path defined as the IP stack, an
  alternative bridge with no socket, operating-system evidence with a positive control, and
  the total and reversible cut controls.

- [G3 executed](window/G3_GENERATIONS.md): the public checkpoint contract, native transfer
  between generations, blocking what was retired, and the explicit refusal without the
  resource declared indispensable.

- [G2 closed](window/G2_PARTS.md): the restricted comparison, the widened paired campaign,
  the audit, the controls and the limits of the conclusions.

- [G1 and the advance review](window/G1_INTEGRATION.md): the contract, persistence, the
  satisfaction assessment, and the usefulness condition for a small G2.

- [G0 executed](window/G0_REFERENCE.md): the configuration, the controls, the artifacts, the
  limitations, and the decision to integrate the reference in G1.

- [Master plan](DETHRON_MASTER_PLAN.md): the main starting point, the hypothesis matrix, the
  architecture, the contracts, milestones G0–G9 and the proposed initial campaign.

- [Incentives and remuneration](DETHRON_INCENTIVES.md): the economic hypothesis and the
  Golem/Filecoin prior art; no token and no economic experiment executed.

- [Direction](DETHRON_NETWORK_DIRECTION.md): the historical intent, swarm and gateways.
- [Autonomy](DETHRON_AUTONOMY_CONTRACT.md): optional use of the internet, survival,
  denominators, information and connectivity.
- [Usefulness](DETHRON_UTILITY_VALIDATION.md): existing references and the gaps to measure.
- [Plan](DETHRON_VALIDATION_PLAN.md): requirements, controls, slices and decisions.

## Core and local proofs

- v2 README.
- Connected recovery.
- In-memory regeneration.
- Semantic evidence status.
- [Window README](window/README.md).
- Survival with processes.

Reference records:

- The survival report, `window/results/survival-20260915T125653Z-71e25ad2/report.json`.
- The in-memory regeneration summary, `v2/results/survival-20260915/summary.json`.
- The four-modes report, `window/results/comparison-20260915T132942Z-19a1b580/report.json`.

Those files are local artifacts and will not accompany a clean clone, because results are
ignored by Git and because the work they belong to has left the tree. Local availability is
not external publication. The artifacts the current milestones cite are published under
[`window/evidence/`](window/evidence/README.md); keep copies of anything else when sharing
the evidence.

## Model applications and diagnostics, a secondary scope

- The current comparison.
- The initial document.
- Atoms.
- Visual reconstruction.
- The harness audit.
- The evaluators.
- The capability contract.
- The earlier inference plan.
- The DeepSeek roadmap.

The integrity rules remain useful. A model's correct answers do not measure connectivity and
are not a prerequisite for G0. Do not promote results on development data to proof of
generalisation or of a global saving.

## History and intent

- The conceptual synthesis.
- The repository audit of 13/09: historical findings, earlier than the new v2/Window proofs;
  it is not a current inventory.
- The 2025 architecture.
- The 2025 implementation guide.
- Templates and use cases.
- The Genesis Gateway plan, `bkp-dethron/future-plans/01-genesis-gateway-service.md`.

The three 2025 guides contain claims and examples requiring characterisation, such as API
availability and biological properties. Context notices were added; the historical bodies
were not rewritten as a new specification.

## Historical gateway code examined statically

The paths in this section, and the Genesis Gateway plan cited above, point at historical
snapshots (`backup/`, `bkp-dethron/`, `Genesis-Protocol/`) that sit **outside the
repository** by a decision recorded in the root `.gitignore`: they are local copies of old
code, not part of the reproducible tree. In a clean clone those paths do not exist; the
analysis below is documentary and is not a prerequisite for G0–V1.

- The P2P extension, `backup/bitnet_extension/bitnet-p2p-gateway.js`: the DHT returns an
  empty list; WebRTC discovery establishes no data exchange; sending contains logs.
- The Genesis Gateway Service, `bkp-dethron/Dethron/services/genesis_gateway_service.py`: a
  mock fallback and a "signature" check by string format.
- Rust roles and discovery, `Genesis-Protocol/src/network.rs`: Gateway and Relay declared;
  discovery fills in simulated loopback nodes.
- The HTTP/SSE gateway,
  `backup/BitNet-lib/bitnet_lib/core/tron_streaming/living_tron_internet_gateway.py`: HTTP
  server code present, proving neither mesh nor reconstruction over radio.

Those gateways were not executed in this analysis. Do not claim that every duplicated backup
file or every dependency was audited. The current code lives in v2; any reuse must pass
behavioural tests of its own.

## Scope of the consolidation

The vision and decision documents were consolidated, and the evidence and plan pages
identified in that conversation were connected. Historical documents received context
without erasing earlier results, examples or claims. Thousands of backup files were not
rewritten, and not every project was certified. `1.md` is a separate note on neural emulation
and was not modified.

The documentary check confirms the local targets of the new links and the presence of the
notices; it is not a repetition of the experiments cited. Old metrics keep their date and
scope, including where the result is negative.

The previous consolidation was checked: six central pages and 21 documents given context;
128 local references verified with no missing target. The historical bodies were preserved
when the notices were inserted. No code, inference, radio or recovery tests were repeated in
that exclusively documentary update.
