# Autonomy from the internet, and survival with 5 %

> **Note, 19/09/2026.** This document cites work that predates Dethron — BitNet/Genesis
> probes, Rust crates, a neural worker, a browser dashboard — which left the tree when the
> repository was prepared for publication. The links to that material have been undone and
> the text kept. The content remains in the git history.

Date: 15/09/2026. A proposed contract for assessing the user's final vision. It is neither
an experimental result nor a guarantee about the current implementation.

## The intent to preserve

The internet serves as a path during the organic expansion of the gateways. The ambition is
for the Dethron network to acquire sufficient paths of its own to stop needing that path
and, even after losing 95 % of the nodes, to preserve its continuity. Automatically
switching the internet path off is a desired feature to assess, not an action authorised on
real equipment at this documentary stage.

## Two independent hypotheses

**H-A — autonomy:** the network sustains the declared service without depending on internet
links, central servers or indispensable discovery infrastructure reachable only over those
links.

**H-S — survival:** after defined losses, the survivors keep enough data, identities and
state to maintain or recover that service.

Passing H-A does not imply H-S. Recovering an object in H-S implies neither connectivity
between the survivors nor delivery to the recipient. The protocol does not substitute for
physical distance, radio range, energy, hardware or available transport.

## What surviving means

| Level | Criterion | What does not follow from it |
| --- | --- | --- |
| Process | An executable is still running | Data or identity preserved |
| Information | An object is reconstructed exactly | The recipient being reachable |
| Service | The declared users receive within the deadline | Global reach, or the same capacity as before |
| Regeneration | New nodes recover valid state | Physical capacity created from nothing |
| Autonomy | The service works without the internet path in the scenario | An impossibility of interruption in other scenarios |

If the recipient was destroyed, define in advance whether there is a replacement device and
a mechanism for recovering the identity. Do not count delivery to a process the evaluator
created with a hidden key as the recipient's autonomous continuity.

## "5 %" requires a denominator and a failure model

Declare whether it is 5 % of the processes, devices, storage, radio capacity or regions.
Processes on the same computer are not independent failures. Fix the node count before the
injection: excluding the dead from the denominator does not turn a broken network into a
100 % healthy one.

Separate:

1. Survivors chosen so as to preserve copies and paths.
2. Random losses, with the distribution and seeds recorded.
3. Correlated failures: one region, shared power or a common gateway.
4. Losses targeted at the nodes concentrating data, keys or connectivity.
5. Simultaneous losses, and gradual losses with an opportunity to repair.

Results from the first case demonstrate none of the others. A small network may hold all the
data and lose its only bridge. Thousands of nodes may stay alive on islands with no future
contact. That is an impossibility of delivery in that scenario, not a fault fixable merely
by renaming the routing a swarm.

## The minimum cost of guaranteeing any 5 %: a bounded argument

A mathematical example, not a measurement of the repository: there are 100 nodes, each
holding `s` bytes of the representation, and an arbitrary object has `M` bytes of
incompressible information. There is no other source of data outside those nodes. If **any
set of five nodes** must reconstruct the object exactly:

```text
5 × s >= M
100 × s >= 20 × M
```

Under the uniform storage model, at least 20 volumes of the object are needed, before
metadata and other costs. It is an information bound on that strong contract, not an
algorithm recommendation. Compressing data with redundancy is measured against its effective
information; a small recipe or key does not remove the need to preserve arbitrary
information.

Schemes with probabilistic losses, restricted survivors or repairs over time have different
contracts and may show other cost relations. Do not use this example as a universal bound on
every survival policy. Even sufficient redundancy does not guarantee that the fragments can
meet.

## What the current tests say

Process survival: 20 services on the same computer, one survivor with a complete copy, with
the key and a trusted root kept by the controller. Three recorded proofs recomposed the
services. The test demonstrates local recovery in the defined scenario. It proves no
universal 5 % threshold, no storage saving, no geographical losses, and no continuity
without the controller and its resources.

The earlier in-memory experiment also uses complete replication. Its 20/20 runs must not be
added to the three process proofs as though they were independent runs of the same contract,
or of a worldwide network.

## Automatic disconnection from the internet

The trigger must depend on capacity observed within the scope being served: destinations
reachable over alternative paths, deadlines, delivery rate, queue capacity, and recovery of
the identity and discovery services. A count of gadgets or a percentage of adoption is not,
on its own, a valid trigger.

Assess separately:

- A preference for our own paths while keeping the internet as an option.
- An operating mode that disables the external interface explicitly.
- Automatic switching, with a reactivation policy, or a declared policy of remaining
  isolated, stated before the test, and without oscillating on every brief contact.

The initial recommendation is to validate autonomy by a controlled cut of the external path.
That tests the ambition without presuming that switching off a useful route improves the
service. The product may offer operators a choice of policy. No cut policy will be enabled
on real machines by these documents.

The offline run must also start cold: discover peers, validate identities, recover state and
receive messages with the external services blocked. Success only with warm caches does not
establish autonomy at startup. An absent internet does not mean IP is forbidden: a local
Wi-Fi may use IP without a WAN. An IP tunnel crossing an external provider stays dependent
on that path.

## The formulation we can try to demonstrate

"In scenario S, with the internet path unavailable and losses F, we preserved the data and
delivered X of Y eligible messages by deadline T, using resources R."

Also keep in the report the ineligible messages, the causes of impossibility and the total
original count. Do not exclude unreachable destinations to inflate the score. Do not convert
this into "practically impossible to switch off": that would require a threat model, an
interruption effort and evidence that do not exist today.

References: [DTN/BPv7](https://www.rfc-editor.org/rfc/rfc9171.html),
[Reticulum and physical media](https://markqvist.github.io/Reticulum/manual/networks.html),
[Tahoe-LAFS and encoding](https://github.com/tahoe-lafs/tahoe-lafs/blob/master/docs/architecture.rst).
The numerical argument above is an explicit derivation, not a result attributed to those
sources. Next steps in the [validation plan](DETHRON_VALIDATION_PLAN.md).
