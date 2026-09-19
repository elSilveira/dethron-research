# Validating Dethron's usefulness and differentiation

Entry point: [consolidated index](README.md). Next actions: [G0–G7 plan](DETHRON_VALIDATION_PLAN.md).

**G0 update, 15/09/2026:** the Reticulum/LXMF reference was executed and met the local scope
of whole messages after a crash. [Results and limits](window/G0_REFERENCE.md). The next
slice is integration in G1; differentiation through fragments remains a G2 hypothesis. The
prior-art analysis below is not market validation.

Date: 15/09/2026. A documentary review of primary sources and of the local evidence already
examined. It is not a benchmark between implementations, a radio test, validation with
users, an exhaustive prior-art search, or a patent analysis.

## Assessment

The final hypothesis of adopting the internet as an initial path, migrating to paths of our
own and surviving with 5 % was analysed in the
[autonomy contract](DETHRON_AUTONOMY_CONTRACT.md). It does not change the usefulness
assessment: physical autonomy requires sufficient contacts and infrastructure, and a
percentage of survivors certifies neither connectivity, nor recovery, nor an impossibility
of being switched off.

The problem class is practically useful and implemented in the real world. The general idea
of preserving, forwarding over contacts and reconstructing data from fragments has
substantial prior art. Dethron's specific usefulness and advantage are not yet demonstrated.
Do not justify a new global implementation on the strength of the swarm, DNA or successive
generations vision alone.

Recommended decision: keep the original vision and limit the next investment to a comparison
with an existing solution in a defined scenario. Integrate existing components where they
meet the requirement; implement differences only once a measurable gap has been identified.
No network implementation was added during this review.

## Close prior art and the nature of the evidence

| Need | Prior art | What it allows us to conclude |
| --- | --- | --- |
| Delivery after interruptions | NASA DTN / the PACE mission | This class of communication has operational use |
| Communication over several physical media | Reticulum | An open stack with interfaces for heterogeneous media exists |
| Persistent messages on a peer network | LXMF over Reticulum | Propagation nodes sync messages and allow later retrieval |
| Messages without the internet over Wi-Fi/Bluetooth | Briar | A distributed application with those media exists; it is not automatically equivalent to the proposed fragment swarm |
| Recovery from redundant fragments | RaptorQ and Tahoe-LAFS | Reconstruction with sufficient information is already a specified and implemented mechanism |
| Coding, multiple paths and DTN | RFCs 9407 and 8975 | The combination also has research prior art; an informational RFC does not prove a complete deployment |

Sources:

1. [NASA: DTN and operational use on PACE](https://www.nasa.gov/communicating-with-missions/delay-disruption-tolerant-networking/).
2. [Reticulum: building heterogeneous networks](https://markqvist.github.io/Reticulum/manual/networks.html).
3. [LXMF: propagation nodes and the router](https://github.com/markqvist/LXMF#propagation-nodes).
4. [Briar: how it works](https://briarproject.org/how-it-works/).
5. [RaptorQ, RFC 6330](https://www.rfc-editor.org/rfc/rfc6330.html).
6. [Tahoe-LAFS: distributed storage](https://tahoe-lafs.org/~trac/lafs.pdf).
7. [Tetrys, RFC 9407, section 6.1](https://www.rfc-editor.org/rfc/rfc9407.html#section-6.1).
8. [Network Coding and DTN, RFC 8975, section 4.4](https://www.rfc-editor.org/rfc/rfc8975.html#section-4.4).

The capabilities above are described by their projects and authors; they were not reproduced
in this session. Do not claim that Reticulum/LXMF or any other tool implements exactly the
whole fragment and regeneration policy imagined. Neither should exclusivity of the
integration be deduced from a bounded search.

## The candidate application, to be validated with users

Exchanging non-urgent messages and documents between teams in the field who have brief
contacts and irregular connectivity. The intended benefit is completing transfers after
interruptions, preserving progress and surviving a change of device, with known limits of
deadline, energy and storage.

An example usage hypothesis: a report has to arrive by the end of the day; parts sit on
distinct carriers and the destination gathers what it received. This has to solve a real
failure or cost that a user already faces. No users have been interviewed and no real
contacts or devices have been measured. Do not present that example as proven commercial
demand.

The first product must not promise to replace a low-latency interactive connection, nor to
support any load over any radio. Small nodes likewise do not imply a computational saving
without accounting for coordination and communication.

## Possible differences: hypotheses, not demonstrated properties

- Less repair traffic to complete the same object after losses.
- More complete objects delivered within the same deadline and energy budget.
- Fewer bytes persisted for the same recovery contract.
- Lower RAM, or simpler operation, on the available participating devices.

Call none of these a differentiator until after a comparison. Being able to show delivery
over three incomplete paths proves that it works, not that it is superior: conventional
recovery solutions may satisfy that test too.

## Decision gates before widening the project

1. **Requirement:** declare recipients, sizes, contacts, the tolerated deadline, the
   expected losses, the hardware and the resources. Validate whether a real team needs that
   service and can keep the participating nodes running.
2. **An executable reference:** test an adequate existing solution. Reticulum with LXMF is a
   close candidate for heterogeneous messages; DTN with the Bundle Protocol is a candidate
   for interruption-tolerant delivery. Encoded storage needs a comparison of its own. Do not
   choose the weakest reference.
3. **The gap:** document which requirement the reference does not meet, or meets at
   excessive cost. If it does meet it, prioritise integration or a contribution to the
   project.
4. **An isolated difference:** introduce only the Dethron mechanism that attempts to close
   that gap. Freeze the experimental protocol and compare with and without the change.
5. **Paired measurement:** the same messages, hardware, contact schedule, losses,
   cryptography and guarantees. Count correct delivery within the deadline, duplicates,
   corruption rejected, physical bytes, total traffic, RAM and measured energy.
6. **Decision:** continue if there is a reproducible and operationally useful benefit. For
   the 5 % goal, measure storage and joules separately; declare the uncertainty and avoid
   trading lower consumption for worse service without saying so.

Without a technical gain, there may still be product value in ease of use and support, but
that also requires validation with users. If there is neither a gain nor a need for
integration, the rational choice is to use the existing solution and stop the equivalent
reimplementation. The work already done stays useful as learning and as test
infrastructure.

## The situation on closing this review

- Usefulness of the problem class: supported by operational use and existing software.
- Novelty of the general concept: not demonstrated; close prior art identified.
- Viability of the complete Dethron implementation: not demonstrated.
- An energy, storage or commercial advantage: not demonstrated.
- Recommended next work: requirements and an executable reference, before widening a swarm
  of our own. This document does not declare those stages complete.

See also [the network's vision and contracts](DETHRON_NETWORK_DIRECTION.md).
