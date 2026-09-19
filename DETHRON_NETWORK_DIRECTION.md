# Dethron: the network's direction and viability criteria

> **Note, 19/09/2026.** This document cites work that predates Dethron — BitNet/Genesis
> probes, Rust crates, a neural worker, a browser dashboard — which left the tree when the
> repository was prepared for publication. The links to that material have been undone and
> the text kept. The content remains in the git history.

Index: [consolidated documentation](README.md). Execution: [G0–G7 plan](DETHRON_VALIDATION_PLAN.md).
Final hypothesis: [autonomy from the internet and survival with 5 %](DETHRON_AUTONOMY_CONTRACT.md).

Updated on 15/09/2026 after the user clarified the objective.

Before implementing the milestones below, apply the criteria in the
[validation of usefulness and differentiation](DETHRON_UTILITY_VALIDATION.md): compare
against existing references and demonstrate a gap. A delivery proof of our own shows that
something works, but on its own it does not demonstrate an advantage justifying the
recreation of a complete stack.

A framing correction: this vision already belongs to the earlier project, DNA, swarm,
reconstruction and wave communication included. This document organises the validation of
that intent; it does not inaugurate a new objective. See the historical synthesis,
especially 2.5–2.9. The historical names, such as "living cryptography", certify no
properties: each property needs an operational definition, an implementation and a real
test.

## Main objective

One additional hypothesis is to pay for maintenance through a verifiable service, possibly
with a transferable token. See [incentives and their criteria](DETHRON_INCENTIVES.md).
Remuneration may favour participation; availability, funding and compatibility with offline
periods all still require demonstration.

The ambition includes migrating from a network resting on the internet to a network with
sufficient paths of its own, possibly with automatic transport switching. That process
depends on observed coverage and service; growing in node count does not demonstrate that
switching the internet path off is safe. Preserve the objective without assuming universal
survival when 5 % of the participants remain.

BitNet, on the basis of the Genesis protocol, should allow a Dethron network that preserves
and delivers messages across disconnections and successive generations of nodes, with
recoverable storage, different transports and open participation. The objective includes
making use of small nodes and reducing the resources consumed. The quality of LLM answers is
a secondary application, not the central criterion for the network's viability. The earlier
measurements remain valid within their scope.

"Immortal" describes the ambition of continuity; it is not an absolute technical guarantee.
The verifiable contract is recovery and delivery under declared conditions: sufficient
information survives, keys and identity remain usable, there is storage, energy and
compatible devices, and there exists a temporal sequence of contacts allowing the recipient
to be reached before expiry. A whole connected path need not exist at any single instant.
Without a future contact, or with the loss of all indispensable information, there is no
delivery.

## Swarm as a meeting of complementary parts

A message may travel over several paths, transports and generations of nodes. No individual
path needs to deliver the whole message. The destination accumulates verified parts until
the information received allows exact reconstruction. Intermediate nodes may also accumulate
and forward parts without decrypting the content; verifying that transport must be designed
separately from the recipient's private reading key.

"Finding its pair" means discovering useful information that is missing: the nodes announce
inventories, recognise the message, version and encoding scheme, and exchange complementary
parts. Fragments do not discover each other; the protocol running on the devices implements
that search. Identical replicas add no information for decoding, although they may improve
availability.

There are two options to compare, not an implementation already chosen:

- Original units by id: every indispensable unit has to be obtained.
- Symbols with encoded redundancy: sufficient combinations may replace specific lost parts,
  according to the properties of the chosen code.

[RaptorQ, RFC 6330](https://www.rfc-editor.org/rfc/rfc6330.html) gives a well-known example
of the second option: recovery from almost any sufficiently large set of symbols. That
guarantees neither decoding from any quantity nor an implementation of RaptorQ in this
repository.

`v2/src/network/recovery_dna.rs` already walks references and accepts one verified replica
for each required unit. The callback may fetch units from different sources. It does not yet
implement redundant encoding, opportunistic discovery of complements, or persistent
reception across contacts; a missing unit makes the current call fail. `node_wire.rs` remains
restricted to loopback.

### The refined priority experiment

Distribute a message's parts over at least three incomplete paths. Interrupt contacts and
replace carrier processes. Remove the origin from the recovery flow. The destination must
gather parts at different moments, preserve progress after a restart, reject corruption and
version mixing, ignore duplicates when counting information, and only deliver after exact
validation. A run below the threshold must stay incomplete, or expire without inventing
content. No individual path must have been sufficient in the positive proof.

This experiment complements milestones 1–3 below. It remains planned; it was not executed in
this documentary update. The goal is to validate the original intent with real evidence,
making use of the current components that already support it.

## Technical grounding and what already exists

### Gateway and organic adoption: the historical intent and the implementation examined

The user clarified that participating gadgets should act as gates; the internet is one of
the paths linking segments, while local contacts and other networks offer additional paths.
This already appears in the earlier materials:

- `bkp-dethron/future-plans/01-genesis-gateway-service.md`: entry into the network, service
  discovery and a bridge between the traditional internet and BitNet.
- `backup/bitnet_extension/bitnet-p2p-gateway.js`: an explicit intent to turn the extension
  into an expansion gateway. The DHT and the connection and sending to peers have simulated
  sections, or logs alone; creating and closing an RTCPeerConnection does not prove a
  connection and a delivery to another device.
- `Genesis-Protocol/src/network.rs`: Gateway and Relay roles declared; `discover_organisms`
  creates simulated nodes at loopback addresses.
- `bkp-dethron/Dethron/services/genesis_gateway_service.py`: a mock fallback and
  authentication based on a string format, with no proof of a cryptographic signature.
- `backup/BitNet-lib/bitnet_lib/core/tron_streaming/living_tron_internet_gateway.py`:
  contains HTTP/SSE server code, which is distinct from proving mesh routing.

These are findings from a static reading on 15/09/2026; those historical gateways were not
executed in this review, and it is not claimed that every equivalent file was audited.
Preserve the intent and make use of the real components, replacing tests that confirm only
simulations.

A growth hypothesis: more compatible and available participants may create more useful
paths. The world count of gadgets measures neither local connectivity, nor diversity of
failures, nor forwarding capacity. Two gateways behind the same external link stay dependent
on it for that destination. More nodes also generate discovery traffic; its cost enters the
comparison.

A proposed test: two segments communicate over the internet; cut that path and check
delivery through gateways over a physically distinct link. Then cut the alternative too: the
message must stay pending and preserved until a new contact or expiry. Vary the number and
location of the gateways, measuring delivery rate, delay, traffic and energy. Not yet
executed.

Reticulum documents networks over the internet and other media, open participation and
transport roles. It is a close comparison for this adoption hypothesis too:
[building networks](https://markqvist.github.io/Reticulum/manual/networks.html).

- DTN and the Bundle Protocol: store, carry and forward data even when origin and
  destination are not simultaneously connected.
- Mesh: multiple hops and routes; Wi-Fi, Bluetooth and other radios require compatible
  adapters, hardware and permissions. A common logical protocol does not make different
  radios directly interoperable.
- Content addressing, integrity checking, deduplication, lossless compression and erasure
  codes are known mechanisms.
- Distributed computation benefits divisible tasks when the useful work exceeds the costs of
  transfer, coordination, verification and repetition.

Primary sources:

- [Bundle Protocol v7, RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html).
- [Bluetooth Mesh: directed forwarding](https://www.bluetooth.com/mesh-directed-forwarding/).
- [Tahoe-LAFS: storage architecture](https://github.com/tahoe-lafs/tahoe-lafs/blob/master/docs/architecture.rst).
- [SNIA: measuring energy efficiency](https://www.snia.org/energy).

This prior art does not eliminate the project's usefulness. The contribution to be tested is
an open, interoperable and measurably efficient integration. No scientific novelty and no
superiority over existing implementations has been demonstrated. The user's phrase "open
brand" does not yet specify a licence, governance, or a discovery and identification format;
it has not been converted into a presumed requirement.

## The real state and its limits

v2 already holds verified units, recipes, persistence and recovery. Window demonstrated the
replacement of local processes using one survivor with a complete copy. That demonstrates
neither opportunistic delivery, nor radio, nor continuity without a controller, nor survival
of machine loss, nor any storage saving. Reference: PROCESS_SURVIVAL.md.

A recipe reconstructs only what its data and inputs allow it to reconstruct. Hashes verify
bytes; they do not recover lost bytes on their own. Summarising text into facts may discard
information and does not free storage while preserving the original exactly. Atomising
creates opportunities for sharing, but also indices, hashes, authentication and
fragmentation. The ideal granularity requires measurement.

There is tension between redundancy, repair, latency and saving. An illustrative example:
encoding ten data parts into fourteen parts of the same size requires about 1.4 times the
original volume, excluding metadata, and can tolerate four losses with an adequate code.
That is not equivalent to tolerating the arbitrary loss of 95 % of the data. Repairs over
time may cross many generations if they happen before the remaining fragments fall below the
recovery threshold.

## A proposed reference architecture, not yet implemented

1. A message envelope: a stable id, the recipient, an encrypted payload, authentication,
   limits, expiry and confirmation of receipt by the recipient.
2. A persistent mailbox: verifiable writing, recovery after a restart, deduplication and a
   bounded retention and forwarding policy.
3. Contacts: transport over separate interfaces and opportunistic forwarding.
4. Recovery: redundancy and repair of messages, indices, identity and the state needed for
   continuity, with recovery of the supervisor and its dependencies.
5. Measurement: delivery, integrity, delay, physical bytes, traffic and joules.
6. Computation: a later extension for independent tasks, after the network is validated.

Do not require an LLM on every node and do not use the model as an integrity mechanism.
Consider integrating with the Bundle Protocol before creating another complete protocol.
Nodes participate with authorisation; reconstruction presupposes available capacity, not
autonomous installation on any device encountered.

## Next experiments, in order

This list organises capabilities. The operational order is the
[G0–G7 plan](DETHRON_VALIDATION_PLAN.md), which requires an executable reference and a gap
before widening any implementation of our own.

| Milestone | Experiment | Evidence needed |
| --- | --- | --- |
| 1 — a persistent message | A delivers to B; A disappears; B restarts; then meets C | C receives the exact bytes and confirms; no simultaneous A–C connection exists |
| 2 — generations | Replace every original process in cycles, the supervisor included | The pending message survives; there is no hidden original copy and no lost key |
| 3 — partitions | Absence of contact, partial loss, duplicates, corruption, full queues and expiry | Delivery when the conditions allow; an explicit failure when they do not |
| 4 — hardware | At least two real transports between distinct devices | A record of contacts, delivery, limits and consumption; a simulation does not count as radio |
| 5 — storage | Compare replication, deduplication/compression and encoded redundancy | The same original information, recovery contract and physical accounting |
| 6 — energy | Complete paired runs, with and without failures, electrical measurement | A net saving, its uncertainty and the same service quality |
| 7 — processing | A partitionable task with verification and repetition after a failure | A net gain against conventional local execution |

None of these new milestones was executed in this direction update. For milestone 1, an
initial local proof may use TCP transport with explicitly controlled contacts; it must be
labelled as such, without claiming a radio mesh.

## The 5 % goal: two separate hypotheses

1. Storage: at least 5 % fewer total physical bytes, including replicas, fragments, indices,
   manifests and authentication, for the same recoverable data.
2. Energy: at least 5 % fewer total joules on the declared workload, including CPU, radio,
   disks, attributable idleness, maintenance and repairs.

Compare against a competent conventional alternative, under the same hardware, volume,
failure distribution, durability, delivery rate and tolerated deadline. Record the raw
measurement and the repetitions; the uncertainty must allow a 5 % gain to be told apart from
noise. Do not infer energy from tokens, bytes or time in isolation.

Redistributing data does not automatically reduce its global volume. Deduplication may
reduce avoidable copies; redundancy needed for survival is not waste by definition. Freeing
logical space likewise does not imply an immediate electrical saving. A saving demonstrated
in a local scenario cannot be extrapolated to 5 % worldwide without evidence of
representative adoption, workloads, hardware and operating costs.

## Decision

Prioritise the persistent message network and continuity across generations. Keep the LLM
studies documented, without using them as the measure of this vision's success. Seek
usefulness and a measurable improvement in a bounded scenario first; global expansion and
energy savings are later validation stages.
