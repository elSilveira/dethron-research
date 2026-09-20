# A — adoption: does anybody outside want this?

20/09/2026. The first milestone whose subject is not the software. Every earlier one asked
whether a claim held; this one asks whether the claim is worth anything to somebody who is
not us, and it is written before the answer is known so that the answer cannot be moved.

## Why this needs a rejection criterion like the rest

The project has closed milestones by refusing them before — G2 found a trade-off rather
than an advantage, V3b was dropped because two media that both carry IP prove nothing about
media. The temptation here is different and stronger: adoption can always be explained away.
Nobody came *yet*. The post went up on a *Saturday*. The community is *small*.

So the criterion is fixed now, in advance, and the honest outcome of failing it is written
down with it.

## What was published

| | When | Where |
| --- | --- | --- |
| Both repositories made public | 19/09/2026 | `elSilveira/dethron`, `elSilveira/dethron-research` |
| CI green on Linux and Windows, Python 3.10–3.12, end-to-end test included | 19/09/2026 | 8 jobs, first run |
| Package on the index | 20/09/2026 | `pip install dethron`, 0.1.0 |
| Defect report, carrying no mention of this project | 20/09/2026 | [rns.recipes forum](https://rns.recipes/forum/general/lxmf-propagation-node-peering-can-silently-never-start-zerodivisionerror-in-stamp-generation-2) and [a pull request](https://github.com/Reticulum-Community/LXMF/pull/1) |
| The project itself | 20/09/2026 | [rns.recipes forum, Showcase](https://rns.recipes/forum/showcase/dethron-portable-proof-of-delivery-for-lxmf) |

The defect report went first and deliberately said nothing about Dethron. A defect report
that arrives carrying a project is an advertisement wearing a bug report's clothes.

## The three marks, and what refutes each

| | Mark | Deadline | Reject if |
| --- | --- | --- | --- |
| **A1** | Three people who are not the author complete the round trip on their own machines | 20/10/2026 | Two of them are blocked by the installation or the guide. That refutes the documentation, not the usefulness: fix it and start again |
| **A2** | **Somebody runs it a second time without being asked** | 20/11/2026 | Zero in sixty days refutes the usefulness hypothesis |
| **A3** | Somebody runs a relay for others, or asks for a feature that only makes sense if they are using it for something real | 20/12/2026 | Zero in ninety days refutes the product in this scope |

**A2 is the one that decides.** A first run is curiosity and costs nothing to explain away.
A second run is need. It is also cheap to observe, which is why it was chosen over anything
involving counts of stars or downloads: those measure attention, and attention is not the
hypothesis.

## What happens if A2 is zero

The honest conclusion, declared in advance: **the contribution is the harness and the
evidence, not the product.** The product ambition is archived the way G2's cost advantage
was archived, the research repository stands as the record, and nothing is quietly kept
alive by lowering the bar.

This is not a bad outcome. V2 exists in this project to measure the distance between "it
works on the machine of whoever wrote it" and "it works from what is published". A is the
same measurement pointed at usefulness rather than correctness, and a distance found is
what it is for.

## What this does not establish

Publishing establishes reachability and nothing else. The forum is small — hundreds of
threads, not thousands of people — and a quiet week means the sample is small, not that the
hypothesis is confirmed or denied. Counting anything before the deadlines above would be
reading noise.

The pull request may never be read: that fork has been dormant since April 2026, with
issues disabled and no forks of its own. Its silence is not evidence about the defect,
which was verified independently and is recorded in
[`upstream/`](upstream/lxmf-stamp-zerodivision.md).

Nothing here measures whether the thing is *good*. It measures whether anyone returns to
it, which is a weaker and more honest question.

## What to watch, in order of what it would mean

1. **Somebody says they have seen this happen** — the defect bites in the field, not only
   on the bench, and it came from an operator running a real propagation node.
2. **Somebody asks how it was found** — the harness enters the conversation without being
   pushed, which is the only way it should.
3. **Somebody answers the specific request in the Showcase post**, checking whether a
   custody attestation matches what is really in their own store. That is the one check
   this project cannot run on its own, and whoever runs it will have run the software
   against real infrastructure.
4. **Silence.** The most likely result in the first week, and not yet information.

The result, whatever it is, belongs in this document with its date.
